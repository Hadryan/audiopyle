from commons.db.entity import ResultStats, Result
from commons.db.session import SessionProvider
from commons.models.result import AnalysisStats, AnalysisResult
from commons.repository.abstract import DbRepository
from commons.repository.audio_file import AudioFileRepository
from commons.repository.audio_tag import AudioTagRepository
from commons.repository.vampy_plugin import VampyPluginRepository


class ResultStatsRepository(DbRepository):
    def __init__(self, session_provider: SessionProvider) -> None:
        super().__init__(session_provider, ResultStats)

    def get_by_task_id(self, task_id: str) -> AnalysisStats:
        return self._query_single_with_filters(task_id=task_id)

    def get_id_by_model(self, model_object: AnalysisStats) -> int:
        return self.get_id_by_task_id(model_object.task_id)

    def get_id_by_task_id(self, task_id: str) -> int:
        return self._get_id(task_id=task_id)

    def _map_to_entity(self, obj: AnalysisStats) -> ResultStats:
        return ResultStats(task_id=obj.task_id, total_time=obj.total_time, extraction_time=obj.extraction_time,
                           compression_time=obj.compression_time, data_stats_build_time=obj.data_stats_build_time,
                           encode_audio_time=obj.encode_audio_time, result_store_time=obj.result_store_time)

    def _map_to_object(self, entity: ResultStats) -> AnalysisStats:
        return AnalysisStats(task_id=entity.task_id, total_time=entity.total_time,
                             extraction_time=entity.extraction_time, compression_time=entity.compression_time,
                             data_stats_build_time=entity.data_stats_build_time,
                             encode_audio_time=entity.encode_audio_time, result_store_time=entity.result_store_time)


class ResultRepository(DbRepository):
    def __init__(self, session_provider: SessionProvider, audio_file_repository: AudioFileRepository,
                 audio_tag_repository: AudioTagRepository, plugin_repository: VampyPluginRepository) -> None:
        super().__init__(session_provider, Result)
        self.audio_file_repository = audio_file_repository
        self.audio_tag_repository = audio_tag_repository
        self.plugin_repository = plugin_repository

    def get_id_by_model(self, model_object: AnalysisResult) -> int:
        return self.get_by_task_id(model_object.task_id)

    def get_by_task_id(self, task_id: str) -> int:
        return self._query_single_with_filters(task_id=task_id)

    def _map_to_entity(self, obj: AnalysisResult) -> Result:
        plugin_id = self.plugin_repository.get_id_by_model(obj.plugin)
        audio_meta_id = self.audio_file_repository.get_id_by_model(obj.audio_meta)
        audio_tag_id = self.audio_tag_repository.get_id_by_model(obj.id3_tag)
        return Result(task_id=obj.task_id, vampy_plugin_id=plugin_id, audio_file_id=audio_meta_id,
                      audio_tag_id=audio_tag_id)

    def _map_to_object(self, entity: Result) -> AnalysisResult:
        audio_meta = self.audio_file_repository.get_by_id(entity.audio_file_id)
        audio_tag = self.audio_tag_repository.get_by_id(entity.audio_tag_id)
        plugin = self.plugin_repository.get_by_id(entity.vampy_plugin_id)
        return AnalysisResult(task_id=entity.task_id, audio_meta=audio_meta, id3_tag=audio_tag, plugin=plugin)