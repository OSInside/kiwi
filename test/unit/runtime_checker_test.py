import sys

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

    def test_check_image_include_repos_http_resolvable(self):
        self.runtime_checker.check_image_include_repos_http_resolvable()

    def test_check_target_directory_not_in_shared_cache(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            'target-dir'
        )
