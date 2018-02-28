from typing import Text, Dict, Any

import numpy
import vamp

from commons.models.feature import VampyFeatureAbstraction, VampyVariableStepFeature, VampyConstantStepFeature, \
    StepFeature
from commons.models.file_meta import WavAudioFileMeta
from commons.models.plugin import VampyPlugin
from commons.utils.logger import get_logger

logger = get_logger()


def extract_features(wav_data: numpy.ndarray, audio_meta: WavAudioFileMeta, vampy_plugin: VampyPlugin,
                     output_name: Text) -> VampyFeatureAbstraction:
    raw_results = vamp.collect(data=wav_data, sample_rate=audio_meta.sample_rate, plugin_key=vampy_plugin.key,
                               output=output_name)
    return _map_feature(raw_results)


def _map_feature(extracted_data: Dict[Text, Any]) -> VampyFeatureAbstraction:
    data_type = list(extracted_data.keys())[0]
    if data_type == "list":
        value_list = [StepFeature(f.get("timestamp").to_float(), f.get("values"), f.get("label") or None)
                      for f in extracted_data.get("list")]
        return VampyVariableStepFeature(step_features=value_list)
    elif data_type in ("vector", "matrix"):
        data = extracted_data.get("vector") or extracted_data.get("matrix")
        return VampyConstantStepFeature(time_step=data[0].to_float(), matrix=data[1])
    else:
        raise NotImplementedError("Can not recognize feature type: {}".format(extracted_data.keys()))
