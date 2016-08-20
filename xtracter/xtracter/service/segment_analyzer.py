# coding=utf-8
import vamp

from commons.utils.logging_setup import get_logger


class AudioSegmentAnalyzer(object):
    def __init__(self, vamp_lib=vamp):
        self.vamp_lib = vamp_lib
        self.logger = get_logger()

    def analyze_all(self, plugin_key, plugin_output, audio_segments):
        output = []
        for audio_segment in audio_segments:
            output.append(self.analyze(plugin_key, plugin_output, audio_segment))
        return output

    def analyze(self, plugin_key, plugin_output, audio_segment):
        try:
            return self.vamp_lib.collect(audio_segment.data, audio_segment.sample_rate, plugin_key, plugin_output)
        except Exception as e:
            self.logger.error(
                "Error on analyzing segment with plugin key: {} output: {}. Details: {}".format(plugin_key,
                                                                                                plugin_output,
                                                                                                e))
            return None
