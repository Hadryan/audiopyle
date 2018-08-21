from logging import Logger
from typing import List

from audiopyle.lib.abstractions.api_model import ApiRequest, ApiResponse, HttpStatusCode
from audiopyle.lib.abstractions.flask_api import FlaskRestApi
from audiopyle.lib.repository.metric import MetricDefinitionRepository, MetricValueRepository


class MetricDefinitionListApi(FlaskRestApi):
    def __init__(self, metric_repo: MetricDefinitionRepository, logger: Logger) -> None:
        super().__init__(logger)
        self.metric_repo = metric_repo
        self.logger = logger

    def _get(self, the_request: ApiRequest) -> ApiResponse:
        all_results = self.metric_repo.get_all_keys()  # type: ignore
        return ApiResponse(HttpStatusCode.ok, all_results)


class MetricDefinitionDetailsApi(FlaskRestApi):
    def __init__(self, metric_repo: MetricDefinitionRepository, logger: Logger) -> None:
        super().__init__(logger)
        self.metric_repo = metric_repo
        self.logger = logger

    def _get(self, the_request: ApiRequest) -> ApiResponse:
        try:
            metric_def_id = the_request.query_params["id"]
            metric_definition = self.metric_repo.get_by_id(metric_def_id)
            if metric_definition:
                return ApiResponse(status_code=HttpStatusCode.ok, payload=metric_definition.to_serializable())
            else:
                return ApiResponse(status_code=HttpStatusCode.not_found,
                                   payload={"Could not find metric definition with id: {}".format(metric_def_id)})
        except KeyError:
            return ApiResponse(HttpStatusCode.bad_request,
                               {"error": "Could not find metric definition ID in URL: {}".format(the_request.url)})


class MetricValueListApi(FlaskRestApi):
    def __init__(self, metric_repo: MetricValueRepository, logger: Logger) -> None:
        super().__init__(logger)
        self.metric_repo = metric_repo
        self.logger = logger

    def _get(self, the_request: ApiRequest) -> ApiResponse:
        all_results = self.metric_repo.get_all_keys()  # type: ignore
        return ApiResponse(HttpStatusCode.ok, all_results)


class MetricValueDetailsApi(FlaskRestApi):
    def __init__(self, metric_repo: MetricValueRepository, logger: Logger) -> None:
        super().__init__(logger)
        self.metric_repo = metric_repo
        self.logger = logger

    def _get(self, the_request: ApiRequest) -> ApiResponse:
        try:
            metric_def_id = the_request.query_params["id"]
        except KeyError:
            return ApiResponse(HttpStatusCode.bad_request,
                               {"error": "Could not find metric value ID in URL: {}".format(the_request.url)})
        metric_definition = self.metric_repo.get_by_id(metric_def_id)
        if metric_definition is not None:
            return ApiResponse(status_code=HttpStatusCode.ok, payload=metric_definition.to_serializable())
        else:
            return ApiResponse(status_code=HttpStatusCode.not_found,
                               payload={"error": "Could not find metric value with ID of {}".format(metric_def_id)})