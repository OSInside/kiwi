from mock import patch

from .test_helper import raises

from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import KiwiRuntimeConfigFormatError
from kiwi.defaults import Defaults


class TestRuntimeConfig(object):
    def setup(self):
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.runtime_config = RuntimeConfig()

    @raises(KiwiRuntimeConfigFormatError)
    def test_invalid_yaml_format(self):
        self.runtime_config.config_data = {'xz': None}
        self.runtime_config.get_xz_options()

    def test_get_xz_options(self):
        assert self.runtime_config.get_xz_options() == ['-a', '-b', 'xxx']

    def test_is_obs_public(self):
        assert self.runtime_config.is_obs_public() is True

    def test_is_obs_public_default(self):
        with patch.dict('os.environ', {'HOME': './'}):
            runtime_config = RuntimeConfig()
            assert runtime_config.is_obs_public() is True

    def test_get_obs_download_server_url(self):
        assert self.runtime_config.get_obs_download_server_url() == \
            'http://example.com'

    def test_get_obs_download_server_url_default(self):
        with patch.dict('os.environ', {'HOME': './'}):
            runtime_config = RuntimeConfig()
            assert runtime_config.get_obs_download_server_url() == \
                Defaults.get_obs_download_server_url()
