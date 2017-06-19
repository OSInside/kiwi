from mock import patch

from .test_helper import raises

from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import KiwiRuntimeConfigFormatError


class TestRuntimeConfig(object):
    def setup(self):
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.runtime_config = RuntimeConfig()

    @raises(KiwiRuntimeConfigFormatError)
    def test_get_xz_options_invalid_yaml_format(self):
        self.runtime_config.config_data = {'xz': 'invalid'}
        self.runtime_config.get_xz_options()

    def test_get_xz_options(self):
        assert self.runtime_config.get_xz_options() == ['-a', '-b', 'xxx']
