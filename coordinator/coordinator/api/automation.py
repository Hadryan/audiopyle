from logging import Logger

from typing import List

from commons.abstractions.api_model import ApiRequest, ApiResponse, HttpStatusCode
from commons.abstractions.flask_api import FlaskRestApi
from commons.db.exception import EntityNotFound
from commons.models.extraction_request import ExtractionRequest
from commons.models.plugin import VampyPlugin
from commons.repository.result import ResultRepository
from commons.services.audio_tag_providing import ACCEPTED_EXTENSIONS
from commons.services.plugin_providing import VampyPluginProvider
from commons.services.store_provider import FileStore
from extractor.engine.tasks import extract_feature
from extractor.task_api import run_task


class AutomationApi(FlaskRestApi):
    def __init__(self, plugin_provider: VampyPluginProvider, audio_file_store: FileStore,
                 result_repo: ResultRepository, logger: Logger) -> None:
        super().__init__(logger)
        self.plugin_provider = plugin_provider
        self.audio_file_store = audio_file_store
        self.result_repo = result_repo

    def _post(self, the_request: ApiRequest) -> ApiResponse:
        audio_file_identifiers = self.audio_file_store.list()
        plugins = self.plugin_provider.list_vampy_plugins()

        if audio_file_identifiers and plugins:
            extraction_requests = self._generate_extraction_requests(audio_file_identifiers, plugins)
            task_id_to_request = {r.uuid(): r.to_serializable() for r in extraction_requests}
            self.logger.debug("Sending {} extraction requests...".format(task_id_to_request))
            for task_id, the_request in task_id_to_request.items():
                try:
                    self.result_repo.get_by_task_id(task_id=task_id)
                    self.logger.warning("Request {} #{} already exist in DB! Omitting...")
                except EntityNotFound:
                    run_task(task=extract_feature, task_id=task_id, extraction_request=the_request)
                    self.logger.info("Sent feature extraction request {} with id {}...".format(the_request, task_id))
            return ApiResponse(HttpStatusCode.accepted, task_id_to_request)
        elif not audio_file_identifiers:
            return ApiResponse(status_code=HttpStatusCode.no_content,
                               payload="No audio files matching {} extensions found!".format(ACCEPTED_EXTENSIONS))
        elif not plugins:
            return ApiResponse(status_code=HttpStatusCode.no_content, payload="No whitelisted plugins found!")

    def _generate_extraction_requests(self, audio_file_identifiers: List[str],
                                      plugins: List[VampyPlugin]) -> List[ExtractionRequest]:
        extraction_requests = []
        for audio_file_identifier in audio_file_identifiers:
            for plugin in plugins:
                for plugin_output in plugin.outputs:
                    extraction_requests.append(
                        ExtractionRequest(audio_file_identifier=audio_file_identifier,
                                          plugin_full_key=plugin.key,
                                          plugin_output=plugin_output))
        return extraction_requests
