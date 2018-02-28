from time import sleep
from unittest import TestCase
from assertpy import assert_that

import requests

from extractor.result_model import ExtractionResult
from testcases.utils import get_service_host_name


class CoordinatorApiTest(TestCase):
    def setUp(self):
        self.extraction_api_url = "http://{}:8080/extraction".format(get_service_host_name("coordinator"))
        self.mp3_extraction_request = {
            "audio_file_name": "102bpm_drum_loop_mono_44.1k.mp3",
            "plugin_key": "vamp-example-plugins:amplitudefollower",
            "plugin_output": "amplitude"
        }

    def test_should_accept_mp3_task_and_return_extracted_data(self):
        expected_status_code = 200
        response = requests.post(url=self.extraction_api_url, json=self.mp3_extraction_request)
        assert_that(response.status_code).is_equal_to(expected_status_code)
        actual_response = response.json()
        assert_that(actual_response).is_not_none()

        sleep(4.)
        task_id = actual_response.get("task_id")
        results_response = requests.get(url=self.extraction_api_url, params={"task_id": task_id})
        assert_that(results_response.status_code).is_equal_to(expected_status_code)
        extraction_result = ExtractionResult.from_serializable(results_response.json())
        assert_that(extraction_result.data).is_not_none()
        assert_that(extraction_result.status).is_equal_to("SUCCESS")

        clean_up_response = requests.delete(url=self.extraction_api_url, params={"task_id": task_id})
        assert_that(clean_up_response.status_code).is_equal_to(expected_status_code)
