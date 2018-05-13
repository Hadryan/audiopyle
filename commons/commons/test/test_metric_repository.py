import unittest
from unittest.mock import Mock

from assertpy import assert_that

from commons.db.exception import DuplicateEntity
from commons.models.metric import MetricDefinition
from commons.models.plugin import VampyPlugin
from commons.repository.metric import MetricDefinitionRepository
from commons.repository.vampy_plugin import VampyPluginRepository
from commons.test.utils import setup_db_repository_test_class, tear_down_db_repository_test_class, \
    fake_function_from_method


class MetricDefinitionDbRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_db_repository_test_class(cls)

    @classmethod
    def tearDownClass(cls):
        tear_down_db_repository_test_class(cls)

    def setUp(self):
        self.metric_definition_1 = MetricDefinition(name="first_metric",
                                                    plugin_key="vamp-example-plugins:amplitudefollower:amplitude",
                                                    function="select_row", kwargs={"row_index": 3})
        self.metric_definition_2 = MetricDefinition(name="second_metric",
                                                    plugin_key="vamp-example-plugins:amplitudefollower:amplitude",
                                                    function="none", kwargs={})
        self.metric_definition_3 = MetricDefinition(name="first_metric",
                                                    plugin_key="vamp-example-plugins:amplitudefollower:amplitude2",
                                                    function="none", kwargs={})
        self.plugin_1 = VampyPlugin("vamp-example-plugins", "amplitudefollower", "amplitude", "")
        self.plugin_2 = VampyPlugin("vamp-example-plugins", "amplitudefollower", "amplitude2", "")
        self.plugin_repo_mock = Mock(VampyPluginRepository)
        self.definition_repo = MetricDefinitionRepository(self.session_provider, self.plugin_repo_mock)

    def tearDown(self):
        self.definition_repo.delete_all()

    def test_should_insert_and_retrieve_by_id(self):
        self.plugin_repo_mock.get_id_by_params.return_value = 1
        self.plugin_repo_mock.get_by_id.return_value = self.plugin_1
        self.definition_repo.insert(self.metric_definition_1)
        identifier = self.definition_repo.get_id_by_model(self.metric_definition_1)
        assert_that(identifier).is_not_none().is_greater_than_or_equal_to(0)

        retrieved = self.definition_repo.get_by_id(identifier)
        assert_that(retrieved).is_equal_to(self.metric_definition_1)

    def test_should_insert_multiple_for_single_plugin(self):
        self.plugin_repo_mock.get_id_by_params.return_value = 1
        self.plugin_repo_mock.get_by_id.return_value = self.plugin_1
        self.definition_repo.insert(self.metric_definition_1)
        self.definition_repo.insert(self.metric_definition_2)
        all_models = self.definition_repo.get_all()
        assert_that(all_models).is_length(2)

    def test_should_fail_on_same_metric_name(self):
        self.plugin_repo_mock.get_id_by_params.return_value = 1
        self.plugin_repo_mock.get_by_id.return_value = self.plugin_1
        self.definition_repo.insert(self.metric_definition_1)
        assert_that(fake_function_from_method).raises(DuplicateEntity).when_called_with(self.definition_repo.insert,
                                                                                        self.metric_definition_3)
