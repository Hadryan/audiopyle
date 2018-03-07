from commons.abstractions.api_model import ApiRequest, ApiResponse, HttpStatusCode
from commons.abstractions.flask_api import FlaskRestApi
from commons.models.extraction_request import ExtractionRequest
from extractor.engine.tasks import extract_feature
from extractor.result_model import TaskStatus
from extractor.task_api import run_task, retrieve_result, delete_result


class ExtractionStatusApi(FlaskRestApi):
    def _get(self, the_request: ApiRequest) -> ApiResponse:
        task_id = the_request.query_params.get("task_id")
        task_result = retrieve_result(task_id)
        if task_result.status in [TaskStatus.in_progress, TaskStatus.not_known, TaskStatus.ignored]:
            return ApiResponse(HttpStatusCode.no_content, task_result.to_serializable())
        else:
            return ApiResponse(HttpStatusCode.no_content, task_result.to_serializable())

    def _delete(self, the_request: ApiRequest) -> ApiResponse:
        task_id = the_request.query_params.get("task_id")
        delete_result(task_id)
        return ApiResponse(HttpStatusCode.ok, {"task_id": task_id})


class ExtractionApi(FlaskRestApi):
    def _post(self, the_request: ApiRequest) -> ApiResponse:
        execution_request = ExtractionRequest.from_serializable(the_request.payload)
        task_id = execution_request.uuid()
        task_result = retrieve_result(task_id)
        if task_result.status in [TaskStatus.ignored, TaskStatus.in_progress, TaskStatus.done]:
            message = "Could not send task because task is already in state: {}".format(task_result.status)
            return ApiResponse(HttpStatusCode.precondition_failed, {"error": message})
        else:
            async_result = run_task(task=extract_feature,
                                    task_id=task_id,
                                    extraction_request=execution_request.to_serializable())
            self.logger.info("Sent feature extraction task: {} with id: {}.".format(execution_request, task_id))
            return ApiResponse(HttpStatusCode.accepted, {"task_id": async_result.task_id})
