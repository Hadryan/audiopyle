from unittest import TestCase
from assertpy import assert_that

import requests

from testcases.utils import get_service_host_name


class CoordinatorApiTest(TestCase):
    def setUp(self):
        self.extraction_api_url = "http://{}:8080/extraction".format(get_service_host_name("coordinator"))

    def test_should_accept_task_and_return_extracted_data(self):
        extraction_request = {
            "audio_file_name": "102bpm_drum_loop_mono_44.1k.wav",
            "plugin_key": "vamp-example-plugins:amplitudefollower",
            "plugin_output": "amplitude"
        }
        expected_status_code = 200
        response = requests.post(url=self.extraction_api_url, json=extraction_request)
        assert_that(response.status_code).is_equal_to(expected_status_code)
        actual_response = response.json()
        assert_that(actual_response).is_not_none()

        results = requests.get(url=self.extraction_api_url)
        assert_that(results.status_code).is_equal_to(expected_status_code)