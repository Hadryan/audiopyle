from numpy.core.multiarray import ndarray

from commons.abstractions.model import Model
from commons.audio.file_meta import LocalAudioFileMeta
from commons.utils.conversion import frames_to_sec


class AudioSegmentMeta(Model):
    def __init__(self, source_file_meta: LocalAudioFileMeta, frame_from: int, frame_to: int) -> None:
        """Represents metadata of a part of an audio wave"""
        self.source_file_meta = source_file_meta
        self.frame_from = frame_from
        self.frame_to = frame_to

    def length_frames(self) -> int:
        return abs(self.frame_to - self.frame_from)

    def length_sec(self) -> float:
        return frames_to_sec(self.length_frames(), self.source_file_meta.sample_rate)

    def serialize(self):
        super_serialized = super(AudioSegmentMeta, self).serialize()
        super_serialized.update({"source_file_meta": self.source_file_meta.serialize()})
        return super_serialized


class MonoAudioSegment(AudioSegmentMeta):
    def __init__(self, source_file_meta: LocalAudioFileMeta, frame_from: int, frame_to: int, data: ndarray) -> None:
        """Represents metadata of a part of an audio wave"""
        super(MonoAudioSegment, self).__init__(source_file_meta, frame_from, frame_to)
        self.data = data

    def get_meta(self) -> AudioSegmentMeta:
        return AudioSegmentMeta(self.source_file_meta, self.frame_from, self.frame_to)

    def __str__(self):
        return super(MonoAudioSegment, self).__str__()

    def serialize(self):
        super_serialized = super(MonoAudioSegment, self).serialize()
        super_serialized.update({"data": self.data.tolist()})
        return super_serialized
