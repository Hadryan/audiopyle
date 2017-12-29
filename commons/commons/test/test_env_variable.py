import unittest

from assertpy import assert_that

from commons.utils.env_var import get_environment_variable


class OsEnvVariableAccessingTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_should_read_existing_variable(self):
        home_value = get_environment_variable("HOME", str)
        assert_that(home_value).is_not_empty().starts_with("/")

    def test_should_fallback_to_default_on_non_existing_variable(self):
        default_value = "some_default"
        non_existing_value = get_environment_variable("NON_EXSTING_VARIABLE", str, default_value)
        assert_that(non_existing_value).is_equal_to(default_value)

    def test_should_fallback_to_default_on_non_wrong_variable_type(self):
        default_value = 1.1
        wrong_type_variable = get_environment_variable("HOME", float, default_value)
        assert_that(wrong_type_variable).is_equal_to(default_value)
