from commons.abstractions.api import AudiopyleRestApi
from commons.services.extraction import ExtractionRequest
from extractor.service import run_task
from extractor.tasks import extract_feature


class ExtractionApi(AudiopyleRestApi):
    def get(self, request_url, query_params):
        return "ok"

    def post(self, request_url, query_params, request_payload):
        execution_request = ExtractionRequest.deserialize(request_payload)
        self.logger.info("Sending feature extraction task: {}...".format(execution_request))
        async_result = run_task(extract_feature, execution_request.serialize())
        self.logger.info("Sent feature extraction task! ID: {}.".format(async_result.task_id))
        return async_result.task_id
