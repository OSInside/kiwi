from mock import patch

from .test_helper import (
    raises, patch_open
)

from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import KiwiRuntimeConfigFormatError
from kiwi.defaults import Defaults


class TestRuntimeConfig(object):
    def setup(self):
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.runtime_config = RuntimeConfig()

    @patch('os.path.exists')
    @patch('yaml.load')
    def test_reading_system_wide_config_file(self, mock_yaml, mock_exists):
        exists_call_results = [True, False]

        def os_path_exists(config):
            return exists_call_results.pop()

        mock_exists.side_effect = os_path_exists
        with patch_open as mock_open:
            self.runtime_config = RuntimeConfig()
            mock_open.assert_called_once_with('/etc/kiwi.yml', 'r')

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

    def test_get_container_compression(self):
        assert self.runtime_config.get_container_compression() is None

    def test_get_container_compression_default(self):
        with patch.dict('os.environ', {'HOME': './'}):
            runtime_config = RuntimeConfig()
            assert runtime_config.get_container_compression() == 'xz'

    @patch.object(RuntimeConfig, '_get_attribute')
    @patch('kiwi.logger.log.warning')
    def test_get_container_compression_invalid(
        self, mock_warning, mock_get_attribute
    ):
        mock_get_attribute.return_value = 'foo'
        assert self.runtime_config.get_container_compression() == 'xz'
        mock_warning.assert_called_once_with(
            'Skipping invalid container compression: foo'
        )

    @patch.object(RuntimeConfig, '_get_attribute')
    def test_get_container_compression_xz(self, mock_get_attribute):
        mock_get_attribute.return_value = 'xz'
        assert self.runtime_config.get_container_compression() == 'xz'

    def test_get_iso_tool_category(self):
        assert self.runtime_config.get_iso_tool_category() == 'cdrtools'

    def test_get_iso_tool_category_default(self):
        with patch.dict('os.environ', {'HOME': './'}):
            runtime_config = RuntimeConfig()
            assert runtime_config.get_iso_tool_category() == 'xorriso'

    @patch.object(RuntimeConfig, '_get_attribute')
    @patch('kiwi.logger.log.warning')
    def test_get_iso_tool_category_invalid(
        self, mock_warning, mock_get_attribute
    ):
        mock_get_attribute.return_value = 'foo'
        assert self.runtime_config.get_iso_tool_category() == 'xorriso'
        mock_warning.assert_called_once_with(
            'Skipping invalid iso tool category: foo'
        )
