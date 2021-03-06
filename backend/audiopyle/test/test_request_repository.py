import unittest

from assertpy import assert_that

from audiopyle.lib.models.audio_tag import Id3Tag
from audiopyle.lib.models.file_meta import CompressedAudioFileMeta
from audiopyle.lib.models.plugin import VampyPlugin, VampyPluginParams
from audiopyle.lib.models.result import AnalysisRequest
from audiopyle.lib.repository.audio_file import AudioFileRepository
from audiopyle.lib.repository.audio_tag import AudioTagRepository
from audiopyle.lib.repository.request import RequestRepository
from audiopyle.lib.repository.vampy_plugin import VampyPluginRepository, PluginConfigRepository
from audiopyle.test.utils import setup_db_repository_test_class, tear_down_db_repository_test_class


class RequestRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_db_repository_test_class(cls)

    @classmethod
    def tearDownClass(cls):
        tear_down_db_repository_test_class(cls)

    def setUp(self):
        self.task_id = "0f961f20-b036-5740-b526-013523dd88c7"
        self.audio_meta_example_1 = CompressedAudioFileMeta("some_file.mp3", 1024 * 1024 * 2, 1, 44100, 45., 128.)
        self.audio_meta_example_2 = CompressedAudioFileMeta("some_file_2.mp3", 1024 * 1024 * 2, 1, 44100, 45., 128.)
        self.tag_example_1 = Id3Tag(artist="Pink Floyd", title="Have a cigar", album="Wish you were here",
                                    date=1975, track=3, genre="Progressive rock")
        self.tag_example_2 = Id3Tag(artist="Floyd", title="Cigar", album="Wish you were here",
                                    date=1981, track=2, genre="Rock")
        self.plugin_example_1 = VampyPlugin("my_vendor", "my_name", "outputs", "my_file.so")
        self.plugin_example_2 = VampyPlugin("my_vendor", "my_name_2", "outputs", "my_file_2.so")
        self.plugin_config_example_1 = VampyPluginParams(block_size=2048, step_size=1024)
        self.the_request = AnalysisRequest(task_id=self.task_id, audio_meta=self.audio_meta_example_1,
                                           id3_tag=self.tag_example_1, plugin=self.plugin_example_1,
                                           plugin_config=self.plugin_config_example_1)
        self.plugin_repo = VampyPluginRepository(self.session_provider)
        self.audio_repo = AudioFileRepository(self.session_provider)
        self.audio_tag_repo = AudioTagRepository(self.session_provider)
        self.plugin_config_repo = PluginConfigRepository(self.session_provider)
        self.request_repo = RequestRepository(self.session_provider, self.audio_repo, self.audio_tag_repo,
                                              self.plugin_repo, self.plugin_config_repo)

    def tearDown(self):
        self.request_repo.delete_all()
        self.plugin_repo.delete_all()
        self.plugin_config_repo.delete_all()
        self.audio_repo.delete_all()
        self.audio_tag_repo.delete_all()

    def test_should_insert_sub_entities_of_request_and_then_list_them(self):
        self.plugin_repo.insert(self.plugin_example_1)
        self.plugin_config_repo.insert(self.plugin_config_example_1)
        self.audio_repo.insert(self.audio_meta_example_1)
        self.audio_tag_repo.insert(self.tag_example_1)

        request_list = self.request_repo.get_all()
        assert_that(request_list).is_empty()

        self.request_repo.insert(self.the_request)

        request_list = self.request_repo.get_all()
        assert_that(request_list).is_length(1)
        assert_that(request_list[0]).is_equal_to(self.the_request)

    def test_should_insert_the_request_with_sub_entities_automatically_and_then_list_them(self):
        assert_that(self.plugin_repo.get_all()).is_empty()
        assert_that(self.plugin_config_repo.get_all()).is_empty()
        assert_that(self.audio_repo.get_all()).is_empty()
        assert_that(self.audio_tag_repo.get_all()).is_empty()
        assert_that(self.request_repo.get_all()).is_empty()

        self.request_repo.insert(self.the_request)

        assert_that(self.plugin_repo.get_all()).is_length(1)
        assert_that(self.plugin_config_repo.get_all()).is_length(1)
        assert_that(self.audio_repo.get_all()).is_length(1)
        assert_that(self.audio_tag_repo.get_all()).is_length(1)

        result_list = self.request_repo.get_all()
        assert_that(result_list).is_length(1)
        assert_that(result_list[0]).is_equal_to(self.the_request)
