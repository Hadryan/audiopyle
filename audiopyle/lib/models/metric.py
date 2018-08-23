from typing import Dict, Text, Any

import numpy

from audiopyle.lib.abstractions.model import Model
from audiopyle.lib.models.feature import VampyFeatureAbstraction, VampyConstantStepFeature, VampyVariableStepFeature
from audiopyle.lib.models.file_meta import CompressedAudioFileMeta
from audiopyle.lib.models.result import DataStats


class MetricDefinition(Model):
    def __init__(self, name: str, plugin_key: str, function: str, kwargs: dict) -> None:
        self.name = name
        self.plugin_key = plugin_key
        self.function = function
        self.kwargs = kwargs


class MetricTransformation(Model):
    def __init__(self, name, **kwargs) -> None:
        self.name = name
        self.kwargs = kwargs

    def call(self, vampy_feature: VampyFeatureAbstraction) -> numpy.ndarray:
        if isinstance(vampy_feature, VampyConstantStepFeature):
            return self._call_on_constant_step(vampy_feature)
        elif isinstance(vampy_feature, VampyVariableStepFeature):
            return self._call_on_variable_step(vampy_feature)
        else:
            raise ValueError("Input parameter is not feature: {}".format(vampy_feature))

    def _call_on_constant_step(self, feature: VampyConstantStepFeature) -> numpy.ndarray:
        raise NotImplementedError("Called abstract _call_on_constant_step")

    def _call_on_variable_step(self, feature: VampyVariableStepFeature) -> numpy.ndarray:
        raise NotImplementedError("Called abstract _call_on_variable_step")


class NoneTransformation(MetricTransformation):
    def __init__(self, **kwargs) -> None:
        super().__init__("none", **kwargs)

    def _call_on_constant_step(self, feature: VampyConstantStepFeature) -> numpy.ndarray:
        return feature.values()

    def _call_on_variable_step(self, feature: VampyVariableStepFeature) -> numpy.ndarray:
        return feature.values()


class SelectRowTransformation(MetricTransformation):
    def __init__(self, **kwargs) -> None:
        super().__init__("select_row", **kwargs)

    def _call_on_constant_step(self, feature: VampyConstantStepFeature) -> numpy.ndarray:
        row_index = self.kwargs["row_index"]
        return numpy.asanyarray([vs[row_index] for vs in feature.values()])

    def _call_on_variable_step(self, feature: VampyVariableStepFeature) -> numpy.ndarray:
        row_index = self.kwargs["row_index"]
        return numpy.asanyarray([sf.values[row_index] for sf in feature.step_features])  # type: ignore


class SingleValueTransformation(MetricTransformation):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__("singe_value", **kwargs)

    def _call_on_constant_step(self, feature: VampyConstantStepFeature) -> numpy.ndarray:
        first_value = feature.values()[0]
        return numpy.asanyarray([first_value, first_value])

    def _call_on_variable_step(self, feature: VampyVariableStepFeature) -> numpy.ndarray:
        first_value = feature.step_features[0].values[0]  # type: ignore
        return numpy.asanyarray([first_value, first_value])


class SegmentLabelShareRatioTransformation(MetricTransformation):
    def __init__(self, **kwargs) -> None:
        super().__init__("segment_share_ratio", **kwargs)
        self.audio_meta = kwargs["audio_meta"]  # type: CompressedAudioFileMeta

    def _call_on_constant_step(self, feature: VampyConstantStepFeature) -> numpy.ndarray:
        raise NotImplementedError("Can not run segment_share_ratio transformation on constant step feature!")

    def _call_on_variable_step(self, feature: VampyVariableStepFeature) -> numpy.ndarray:
        segment_label = self.kwargs["label"]
        segment_lengths_seconds = []
        last_segment_start_sec = None
        for step in feature.step_features:
            if last_segment_start_sec is not None:
                # case when segment with selected label has ended and step.timestamp represents next segment start time
                segment_lengths_seconds.append(step.timestamp - last_segment_start_sec)
                last_segment_start_sec = None
            elif step.label == segment_label:
                # case when step.timestamp is start of segment with selected label
                last_segment_start_sec = step.timestamp
            else:
                # case when step is point between two segments without selected label
                last_segment_start_sec = None
        if last_segment_start_sec is not None:
            # case when last segment was selected
            segment_lengths_seconds.append(self.audio_meta.length_sec - last_segment_start_sec)
        return numpy.asanyarray([sls / self.audio_meta.length_sec for sls in segment_lengths_seconds])  # type: ignore


class MetricValue(Model):
    def __init__(self, task_id: str, definition: MetricDefinition, stats: DataStats) -> None:
        self.task_id = task_id
        self.definition = definition
        self.stats = stats

    def to_serializable(self):
        base_serialized = super().to_serializable()
        base_serialized.update({"definition": self.definition.to_serializable(),
                                "stats": self.stats.to_serializable()})
        return base_serialized

    @classmethod
    def from_serializable(cls, serialized: Dict[Text, Any]):
        stats_object = DataStats.from_serializable(serialized["stats"])
        definition_object = MetricDefinition.from_serializable(serialized["definition"])
        serialized.update({"stats": stats_object,
                           "definition": definition_object})
        return MetricValue(**serialized)
