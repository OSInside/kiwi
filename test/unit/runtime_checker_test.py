import sys
import os

from mock import patch

from .test_helper import *

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.runtime_checker import RuntimeChecker
from kiwi.exceptions import *


class TestRuntimeChecker(object):
    def setup(self):
        description = XMLDescription(
            '../data/example_runtime_checker_config.xml'
        )
        self.xml_state = XMLState(
            description.load()
        )
        self.runtime_checker = RuntimeChecker(self.xml_state)

    @raises(KiwiRuntimeError)
    def test_check_image_include_repos_http_resolvable(self):
        self.runtime_checker.check_image_include_repos_http_resolvable()

    @raises(KiwiRuntimeError)
    def test_check_target_directory_not_in_shared_cache_1(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache//kiwi/foo'
        )

    @raises(KiwiRuntimeError)
    def test_check_target_directory_not_in_shared_cache_2(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache/kiwi'
        )

    @raises(KiwiRuntimeError)
    @patch('os.getcwd')
    def test_check_target_directory_not_in_shared_cache_3(self, mock_getcwd):
        mock_getcwd.return_value = '/'
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            'var/cache/kiwi'
        )

    @raises(KiwiRuntimeError)
    def test_check_target_directory_not_in_shared_cache_4(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '//var/cache//kiwi/foo'
        )

    @raises(KiwiRuntimeError)
    def test_check_repositories_configured(self):
        self.xml_state.delete_repository_sections()
        self.runtime_checker.check_repositories_configured()
