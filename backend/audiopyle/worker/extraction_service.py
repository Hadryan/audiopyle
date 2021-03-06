from logging import Logger
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime

import numpy as np
from sqlalchemy.exc import DatabaseError

from audiopyle.lib.models.compressed_feature import CompressedFeatureDTO, CompressionType
from audiopyle.lib.models.metric import MetricValue, MetricDefinition
from audiopyle.lib.repository.audio_file import AudioFileRepository
from audiopyle.lib.repository.audio_tag import AudioTagRepository
from audiopyle.lib.repository.feature_data import FeatureDataRepository
from audiopyle.lib.repository.feature_meta import FeatureMetaRepository
from audiopyle.lib.repository.metric import MetricDefinitionRepository, MetricValueRepository
from audiopyle.lib.repository.request import RequestRepository
from audiopyle.lib.repository.stats import ResultStatsRepository
from audiopyle.lib.repository.vampy_plugin import VampyPluginRepository, PluginConfigRepository
from audiopyle.lib.services.compression import compress_model
from audiopyle.lib.services.metric_provider import get_transformation, extract_metric_value
from audiopyle.lib.services.plugin_providing import VampyPluginProvider
from audiopyle.lib.utils.conversion import seconds_between
from audiopyle.lib.models.audio_tag import Id3Tag
from audiopyle.lib.models.extraction_request import ExtractionRequest
from audiopyle.lib.models.feature import VampyFeatureAbstraction
from audiopyle.lib.models.file_meta import FileMeta, CompressedAudioFileMeta, AudioFileMeta
from audiopyle.lib.models.plugin import VampyPlugin, VampyPluginParams
from audiopyle.lib.models.result import AnalysisRequest, AnalysisStats
from audiopyle.lib.services.audio_tag_providing import read_audio_tag
from audiopyle.lib.services.feature_extraction import extract_raw_feature, build_feature_object
from audiopyle.lib.services.feature_meta_extraction import build_feature_meta
from audiopyle.lib.services.file_meta_providing import read_file_meta, read_audio_file_meta
from audiopyle.lib.services.audio_providing import read_raw_audio_from_file
from audiopyle.lib.services.store_provider import Mp3FileStore
from audiopyle.lib.utils.env_var import read_env_var


class FeatureExtractionService(object):
    def __init__(self, plugin_provider: VampyPluginProvider, audio_file_store: Mp3FileStore,
                 audio_tag_repo: AudioTagRepository, audio_meta_repo: AudioFileRepository,
                 plugin_repo: VampyPluginRepository, plugin_config_repo: PluginConfigRepository,
                 metric_definition_repo: MetricDefinitionRepository, metric_value_repo: MetricValueRepository,
                 feature_data_repo: FeatureDataRepository,
                 feature_meta_repo: FeatureMetaRepository, request_repo: RequestRepository,
                 result_stats_repo: ResultStatsRepository,
                 logger: Logger) -> None:
        self.plugin_provider = plugin_provider
        self.audio_file_store = audio_file_store
        self.plugin_repo = plugin_repo
        self.plugin_config_repo = plugin_config_repo
        self.audio_tag_repo = audio_tag_repo
        self.audio_meta_repo = audio_meta_repo
        self.feature_data_repo = feature_data_repo
        self.feature_meta_repo = feature_meta_repo
        self.metric_definition_repo = metric_definition_repo
        self.metric_value_repo = metric_value_repo
        self.request_repo = request_repo
        self.result_stats_repo = result_stats_repo
        self.logger = logger

    def extract_feature_and_store(self, request: ExtractionRequest):
        task_start_time = datetime.utcnow()
        task_id = request.task_id

        self.logger.info("Building context for extraction {}: {}...".format(task_id, request))
        input_audio_file_path = self.audio_file_store.get_full_path(request.audio_file_name)
        plugin = self.plugin_provider.build_plugin_from_full_key(str(request.plugin_full_key))
        if plugin is None:
            raise ValueError("Could not find plugin with full key: {}".format(request.plugin_full_key))
        plugin_config = self._build_plugin_config(request)
        file_meta, audio_meta, id3_tag = self._read_file_meta(input_audio_file_path)
        analysis_request = AnalysisRequest(task_id, audio_meta, id3_tag, plugin, plugin_config)
        self.request_repo.insert(analysis_request)

        self.logger.debug("Built context: {}! Extracting features...".format(request))
        wav_data, read_raw_audio_time = self._read_raw_audio_data_from(input_audio_file_path)
        feature_object, extraction_time = self._do_extraction(task_id, plugin, audio_meta, wav_data, plugin_config)
        feature_dto, compression_time = self._compress_feature(feature_object, task_id)
        feature_meta, feature_meta_build_time = self._build_feature_meta(feature_object, task_id)
        metric_values, metrics_extraction_time = self._extract_metrics(task_id, audio_meta, request.plugin_full_key,
                                                                       request.metric_config, feature_object)

        self.logger.debug("Extracted features for {}; storing...".format(request))
        storage_time = self._store_results_in_db(metric_values, feature_dto, feature_meta)

        task_time = seconds_between(task_start_time)
        results_stats = AnalysisStats(task_id, task_time, extraction_time, compression_time, feature_meta_build_time,
                                      read_raw_audio_time, storage_time, metrics_extraction_time)
        self.result_stats_repo.insert(results_stats)
        self.logger.debug("Done {}!".format(request))

    def _build_plugin_config(self, request: ExtractionRequest) -> VampyPluginParams:
        if request.plugin_config:
            block_size = request.plugin_config.pop("block_size", None)
            step_size = request.plugin_config.pop("step_size", None)
            return VampyPluginParams(block_size, step_size, **request.plugin_config)
        else:
            return VampyPluginParams(None, None)

    def _store_results_in_db(self, metric_values: List[MetricValue], feature_dto, feature_meta):
        start_time = datetime.utcnow()
        for metric_value in metric_values:
            self.metric_definition_repo.get_or_create(metric_value.definition)
            self.metric_value_repo.insert(metric_value)
        self.feature_meta_repo.insert(feature_meta)
        if read_env_var("EXTRACTION_FULL_RESULT_PERSISTENCE", int, 1):
            try:
                self.feature_data_repo.insert(feature_dto)
            except DatabaseError as e:
                self.logger.error(
                    "Couldn't insert feature of size {} from into DB: {}".format(feature_dto.size_humanized(), e))
                raise e
        else:
            self.logger.warning("Ignoring full result due to EXTRACTION_FULL_RESULT_PERSISTENCE setting!")
        return seconds_between(start_time)

    def _build_feature_meta(self, feature_object, task_id):
        start_time = datetime.utcnow()
        feature_meta = build_feature_meta(task_id, feature_object)
        return feature_meta, seconds_between(start_time)

    def _compress_feature(self, feature_object: VampyFeatureAbstraction, task_id: str) -> Tuple[CompressedFeatureDTO, float]:
        start_time = datetime.utcnow()
        compressed_feature_bytes = compress_model(CompressionType.lzma, feature_object.to_serializable())
        feature_dto = CompressedFeatureDTO(task_id, CompressionType.lzma, compressed_feature_bytes)
        return feature_dto, seconds_between(start_time)

    def _do_extraction(self, task_id: str, plugin: VampyPlugin, input_audio_meta: AudioFileMeta,
                       wav_data: np.ndarray, plugin_config: VampyPluginParams) -> Tuple[VampyFeatureAbstraction, float]:
        extraction_start_time = datetime.utcnow()
        raw_feature = extract_raw_feature(wav_data, input_audio_meta.sample_rate, plugin.vampy_key,
                                          plugin.output, plugin_config)
        feature_object = build_feature_object(task_id=task_id, extracted_data=raw_feature)
        extraction_time = seconds_between(extraction_start_time)
        return feature_object, extraction_time

    def _read_raw_audio_data_from(self, input_file_path: str) -> Tuple[np.ndarray, float]:
        read_raw_audio_start_time = datetime.utcnow()
        raw_data = read_raw_audio_from_file(input_file_path)
        read_raw_audio_time = seconds_between(read_raw_audio_start_time)
        return raw_data, read_raw_audio_time

    def _read_file_meta(self, audio_file_absolute_path: str) -> Tuple[FileMeta, CompressedAudioFileMeta, Id3Tag]:
        input_file_meta = read_file_meta(audio_file_absolute_path)
        input_audio_meta = read_audio_file_meta(audio_file_absolute_path)
        id3_tag = read_audio_tag(audio_file_absolute_path)
        if input_file_meta and input_audio_meta and id3_tag:
            return input_file_meta, input_audio_meta, id3_tag
        else:
            raise ValueError(
                "Either file meta, audio meta or tag for file {} is empty!".format(audio_file_absolute_path))

    def _extract_metrics(self, task_id: str, audio_meta: CompressedAudioFileMeta, plugin_key: str, metric_config: Optional[Dict[str, Any]],
                         feature: VampyFeatureAbstraction) -> Tuple[List[MetricValue], float]:
        extraction_start_time = datetime.utcnow()
        metric_values = []
        if metric_config is not None:
            for metric_name, metric_config in metric_config.items():
                value = self._calculate_metric(feature, metric_config, metric_name, plugin_key, task_id, audio_meta)  # type: ignore
                metric_values.append(value)
        metric_extraction_time = seconds_between(extraction_start_time)
        return metric_values, metric_extraction_time

    def _calculate_metric(self, feature: VampyFeatureAbstraction, metric_config: Dict[str, Any], metric_name: str,
                          plugin_key: str, task_id: str, audio_meta) -> MetricValue:
        transformation_function_name = metric_config["transformation"]["name"]
        transformation_function_params = metric_config["transformation"].get("kwargs", {})
        transformation_function = get_transformation(transformation_function_name,
                                                     audio_meta,
                                                     transformation_function_params)
        definition = MetricDefinition(name=metric_name, plugin_key=plugin_key,
                                      function=transformation_function_name,
                                      kwargs=transformation_function_params)
        return extract_metric_value(task_id, definition, transformation_function, feature)
