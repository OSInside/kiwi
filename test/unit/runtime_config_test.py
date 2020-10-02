import logging
from mock import patch
from pytest import (
    raises, fixture
)

from kiwi.runtime_config import RuntimeConfig
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiRuntimeConfigFormatError


class TestRuntimeConfig:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.runtime_config = RuntimeConfig()

        # pretend that none of the runtime config files exist, even if they do
        # (e.g. the system wide config file in /etc/kiwi.yml)
        # => this will give us the defaults
        with patch('os.path.exists', return_value=False):
            self.default_runtime_config = RuntimeConfig()

    @patch('os.path.exists')
    @patch('yaml.safe_load')
    def test_reading_system_wide_config_file(self, mock_yaml, mock_exists):
        exists_call_results = [True, False]

        def os_path_exists(config):
            return exists_call_results.pop()

        mock_exists.side_effect = os_path_exists
        with patch('builtins.open') as m_open:
            self.runtime_config = RuntimeConfig()
            m_open.assert_called_once_with('/etc/kiwi.yml', 'r')

    def test_invalid_yaml_format(self):
        self.runtime_config.config_data = {'xz': None}
        with raises(KiwiRuntimeConfigFormatError):
            self.runtime_config.get_xz_options()

    def test_get_xz_options(self):
        assert self.runtime_config.get_xz_options() == ['-a', '-b', 'xxx']

    def test_is_obs_public(self):
        assert self.runtime_config.is_obs_public() is True

    def test_get_bundle_compression(self):
        assert self.runtime_config.get_bundle_compression() is True

    def test_get_bundle_compression_default(self):
        assert self.default_runtime_config.get_bundle_compression(
            default=True
        ) is True
        assert self.default_runtime_config.get_bundle_compression(
            default=False
        ) is False

    def test_is_obs_public_default(self):
        assert self.default_runtime_config.is_obs_public() is True

    def test_get_obs_download_server_url(self):
        assert self.runtime_config.get_obs_download_server_url() == \
            'http://example.com'

    def test_get_obs_download_server_url_default(self):
        assert self.default_runtime_config.get_obs_download_server_url() == \
            Defaults.get_obs_download_server_url()

    def test_get_container_compression(self):
        assert self.runtime_config.get_container_compression() is None

    def test_get_container_compression_default(self):
        assert self.default_runtime_config.get_container_compression() == 'xz'

    @patch.object(RuntimeConfig, '_get_attribute')
    def test_get_container_compression_invalid(self, mock_get_attribute):
        mock_get_attribute.return_value = 'foo'
        with self._caplog.at_level(logging.WARNING):
            assert self.runtime_config.get_container_compression() == 'xz'
            assert 'Skipping invalid container compression: foo' in \
                self._caplog.text

    @patch.object(RuntimeConfig, '_get_attribute')
    def test_get_container_compression_xz(self, mock_get_attribute):
        mock_get_attribute.return_value = 'xz'
        assert self.runtime_config.get_container_compression() == 'xz'

    def test_get_iso_tool_category(self):
        assert self.runtime_config.get_iso_tool_category() == 'cdrtools'

    def test_get_iso_tool_category_default(self):
        assert self.default_runtime_config.get_iso_tool_category() == 'xorriso'

    @patch.object(RuntimeConfig, '_get_attribute')
    def test_get_iso_tool_category_invalid(self, mock_get_attribute):
        mock_get_attribute.return_value = 'foo'
        with self._caplog.at_level(logging.WARNING):
            assert self.runtime_config.get_iso_tool_category() == 'xorriso'
            assert 'Skipping invalid iso tool category: foo' in \
                self._caplog.text

    def test_get_oci_archive_tool(self):
        assert self.runtime_config.get_oci_archive_tool() == 'umoci'

    def test_get_oci_archive_tool_default(self):
        assert self.default_runtime_config.get_oci_archive_tool() == 'umoci'

    def test_get_disabled_runtime_checks(self):
        assert self.runtime_config.get_disabled_runtime_checks() == [
            'check_dracut_module_for_oem_install_in_package_list',
            'check_container_tool_chain_installed'
        ]

    def test_get_package_changes_default(self):
        assert self.runtime_config.get_package_changes() is True

    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    def test_get_packages_changes_default_for_obs(
        self, mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = True
        assert self.runtime_config.get_package_changes() is False

    @patch.object(RuntimeConfig, '_get_attribute')
    def test_get_packages_changes_explicit_setup(self, mock_get_attribute):
        mock_get_attribute.return_value = False
        assert self.runtime_config.get_package_changes() is False
        mock_get_attribute.return_value = True
        assert self.runtime_config.get_package_changes() is True
