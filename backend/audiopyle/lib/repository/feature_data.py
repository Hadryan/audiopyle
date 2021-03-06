from typing import List, Optional

from audiopyle.lib.db.entity import FeatureData
from audiopyle.lib.db.session import SessionProvider
from audiopyle.lib.models.compressed_feature import CompressedFeatureDTO, CompressionType
from audiopyle.lib.repository.abstract import DbRepository
from audiopyle.lib.utils.conversion import safe_cast


class FeatureDataRepository(DbRepository):
    def __init__(self, session_provider: SessionProvider) -> None:
        super().__init__(session_provider, FeatureData)

    def filter_by_compression(self, compression_type: CompressionType) -> List[CompressedFeatureDTO]:
        return self._query_multiple(compression=compression_type.value)

    def get_id_by_model(self, model_object: CompressedFeatureDTO) -> Optional[str]:
        return safe_cast(self._get_id(id=model_object.task_id), str, None)

    def _map_to_object(self, entity: FeatureData) -> CompressedFeatureDTO:
        return CompressedFeatureDTO(task_id=entity.id, compression=CompressionType(entity.compression),
                                    data=entity.feature_data)

    def _map_to_entity(self, obj: CompressedFeatureDTO) -> FeatureData:
        return FeatureData(id=obj.task_id, compression=obj.compression.value, feature_data=obj.data)
