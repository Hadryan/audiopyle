from logging import Logger

from flask import Flask

from commons.services.store_provider import Mp3FileStore, LzmaJsonFileStore
from commons.utils.file_system import AUDIO_FILES_DIR, RESULTS_DATA_DIR, RESULTS_STATS_DIR, \
    RESULTS_META_DIR
from commons.utils.logger import setup_logger, get_logger
from coordinator.api.audio_file import AudioFileListApi, AudioFileDetailApi
from coordinator.api.automation import AutomationApi
from coordinator.api.plugin import PluginListApi, PluginDetailApi
from coordinator.api.root import CoordinatorApi
from coordinator.api.extraction import ExtractionApi, ResultListApi, ResultDetailsApi

app = Flask(__name__)


def main():
    setup_logger()
    logger = get_logger()
    logger.info("Initializing Coordinator app...")
    start_app(logger, "0.0.0.0", 8080, debug=False)


def start_app(logger: Logger, host: str, port: int, debug: bool = False):
    audio_file_store = Mp3FileStore(AUDIO_FILES_DIR)
    result_data_file_store = LzmaJsonFileStore(RESULTS_DATA_DIR)
    result_meta_file_store = LzmaJsonFileStore(RESULTS_META_DIR)
    result_stats_file_store = LzmaJsonFileStore(RESULTS_STATS_DIR)
    app.add_url_rule("/automation", view_func=AutomationApi.as_view('automation_api', logger=logger))
    app.add_url_rule("/extraction", view_func=ExtractionApi.as_view('extraction_api', logger=logger))
    app.add_url_rule("/result/<task_id>/data",
                     view_func=ResultDetailsApi.as_view('result_data_detail_api',
                                                        file_store=result_data_file_store,
                                                        logger=logger))
    pp.add_url_rule("/result/<task_id>/meta",
                    view_func=ResultDetailsApi.as_view('result_meta_detail_api',
                                                       file_store=result_meta_file_store,
                                                       logger=logger))
    pp.add_url_rule("/result/<task_id>/stats",
                    view_func=ResultDetailsApi.as_view('result_stats_detail_api',
                                                       file_store=result_stats_file_store,
                                                       logger=logger))
    app.add_url_rule("/result",
                     view_func=ResultListApi.as_view('result_list_api',
                                                     file_store=result_data_file_store,
                                                     logger=logger))
    app.add_url_rule("/plugin/<vendor>/<name>",
                     view_func=PluginDetailApi.as_view('plugin_detail_api',
                                                       logger=logger))
    app.add_url_rule("/plugin",
                     view_func=PluginListApi.as_view('plugin_list_api',
                                                     logger=logger))
    app.add_url_rule("/audio/<identifier>",
                     view_func=AudioFileDetailApi.as_view('audio_detail_api',
                                                          file_store=audio_file_store,
                                                          logger=logger))
    app.add_url_rule("/audio",
                     view_func=AudioFileListApi.as_view('audio_list_api',
                                                        file_store=audio_file_store,
                                                        logger=logger))
    app.add_url_rule("/", view_func=CoordinatorApi.as_view('coordinator_api', logger=logger))
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
