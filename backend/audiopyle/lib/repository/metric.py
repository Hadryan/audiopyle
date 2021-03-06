import json
from typing import Optional, List

from audiopyle.lib.models.metric import MetricDefinition as MetricDefObj, MetricValue
from audiopyle.lib.db.entity import MetricDefinition as MetricDefEnt, VampyPlugin, Metric
from audiopyle.lib.db.session import SessionProvider
from audiopyle.lib.models.plugin import full_key_to_params, params_to_full_key
from audiopyle.lib.models.result import DataStats
from audiopyle.lib.repository.abstract import DbRepository
from audiopyle.lib.repository.vampy_plugin import VampyPluginRepository
from audiopyle.lib.utils.conversion import safe_cast


class MetricDefinitionRepository(DbRepository):
    def __init__(self, session_provider: SessionProvider, plugin_repository: VampyPluginRepository) -> None:
        super().__init__(session_provider, MetricDefEnt)
        self.plugin_repository = plugin_repository

    def _map_to_entity(self, obj: MetricDefObj) -> MetricDefEnt:
        vendor, name, output = full_key_to_params(obj.plugin_key)
        vampy_plugin_id = self.plugin_repository.get_id_by_params(vendor, name, output)
        json_kwargs_repr = json.dumps(obj.kwargs)
        return MetricDefEnt(plugin_id=vampy_plugin_id, name=obj.name, function=obj.function, kwargs=json_kwargs_repr)

    def _map_to_object(self, entity: MetricDefEnt) -> MetricDefObj:
        plugin_entity = self.plugin_repository.get_by_id(entity.plugin_id)  # type: Optional[VampyPlugin]
        if plugin_entity:
            full_key = params_to_full_key(plugin_entity.vendor, plugin_entity.name, plugin_entity.output)
            model_kwargs = json.loads(entity.kwargs)
            return MetricDefObj(name=entity.name, plugin_key=full_key, function=entity.function, kwargs=model_kwargs)
        raise ValueError(
            "Could not find plugin with ID of {} when resolving metric definition named {}".format(entity.plugin_id,
                                                                                                   entity.name))

    def get_id_by_model(self, model_object: MetricDefObj) -> Optional[int]:
        return safe_cast(self._get_id(name=model_object.name), int, None)

    def get_metric_by_name(self, metric_name: str) -> Optional[MetricDefObj]:
        return self._query_single(name=metric_name)

    def get_key_by_metric_name(self, metric_name: str) -> Optional[int]:
        return self._get_id(name=metric_name)  # type: ignore


class MetricValueRepository(DbRepository):
    def __init__(self, session_provider: SessionProvider, definition_repository: MetricDefinitionRepository) -> None:
        super().__init__(session_provider, Metric)
        self.definition_repository = definition_repository

    def _map_to_entity(self, obj: MetricValue) -> Metric:
        definition_id = self.definition_repository.get_id_by_model(obj.definition)
        return Metric(task_id=obj.task_id, definition_id=definition_id,
                      minimum=obj.stats.minimum, maximum=obj.stats.maximum,
                      median=obj.stats.median, mean=obj.stats.mean,
                      standard_deviation=obj.stats.standard_deviation, variance=obj.stats.variance,
                      sum=obj.stats.sum, count=obj.stats.count)

    def _map_to_object(self, entity: Metric) -> MetricValue:
        definition_object = self.definition_repository.get_by_id(entity.definition_id)
        if not definition_object:
            raise ValueError("Could not find metric definition with id {} for metric {}".format(entity.definition_id,
                                                                                                entity.task_id))
        data_stats = DataStats(minimum=entity.minimum, maximum=entity.maximum,
                               median=entity.median, mean=entity.mean,
                               standard_deviation=entity.standard_deviation, variance=entity.variance,
                               sum=entity.sum, count=entity.count)
        return MetricValue(task_id=entity.task_id, definition=definition_object, stats=data_stats)

    def get_id_by_model(self, model_object: MetricValue) -> Optional[int]:
        definition_id = self.definition_repository.get_id_by_model(model_object.definition)
        return safe_cast(self._get_id(definition_id=definition_id, task_id=model_object.task_id), int, None)

    def get_values_by_name(self, metric_name: str) -> Optional[List[MetricValue]]:
        metric_def_id = self.definition_repository.get_key_by_metric_name(metric_name=metric_name)
        if metric_def_id is None:
            return None
        else:
            return self._query_multiple(definition_id=metric_def_id)

    def get_by_task_id(self, task_id: str) -> List[MetricValue]:
        return self._query_multiple(task_id=task_id)

    def get_by_name_and_task_id(self, metric_name: str, task_id: str) -> Optional[MetricValue]:
        metric_def_id = self.definition_repository.get_key_by_metric_name(metric_name=metric_name)
        if metric_def_id is None:
            return None
        else:
            return self._query_single(definition_id=metric_def_id, task_id=task_id)
