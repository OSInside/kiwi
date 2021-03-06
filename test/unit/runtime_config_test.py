import logging
from mock import patch
from pytest import (
    raises, fixture
)

from kiwi.runtime_config import RuntimeConfig
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiRuntimeConfigFormatError,
    KiwiRuntimeConfigFileError
)


class TestRuntimeConfig:
    def setup(self):
        Defaults.set_custom_runtime_config_file(None)

    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test__get_attribute_raises_on_invalid_structure(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/broken'}):
            runtime_config = RuntimeConfig(reread=True)
            with raises(KiwiRuntimeConfigFormatError):
                runtime_config._get_attribute('foo', 'bar')

    def test_init_raises_custom_config_file_not_found(self):
        Defaults.set_custom_runtime_config_file('some-config-file')
        with patch('os.path.isfile', return_value=False):
            with raises(KiwiRuntimeConfigFileError):
                RuntimeConfig(reread=True)

    @patch('os.path.exists')
    @patch('yaml.safe_load')
    def test_reading_system_wide_config_file(
        self, mock_yaml, mock_exists
    ):
        exists_call_results = [True, False]

        def os_path_exists(config):
            return exists_call_results.pop()

        mock_exists.side_effect = os_path_exists
        with patch('builtins.open') as m_open:
            RuntimeConfig(reread=True)
            m_open.assert_called_once_with('/etc/kiwi.yml', 'r')

    def test_config_sections_from_home_base_config(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/ok'}):
            runtime_config = RuntimeConfig(reread=True)

        assert runtime_config.get_xz_options() == ['-a', '-b', 'xxx']
        assert runtime_config.is_obs_public() is True
        assert runtime_config.get_bundle_compression() is True
        assert runtime_config.get_obs_download_server_url() == \
            'http://example.com'
        assert runtime_config.get_obs_api_server_url() == \
            'https://api.example.com'
        assert runtime_config.get_container_compression() is None
        assert runtime_config.get_iso_tool_category() == 'cdrtools'
        assert runtime_config.get_oci_archive_tool() == 'umoci'
        assert runtime_config.get_package_changes() is True
        assert runtime_config.get_disabled_runtime_checks() == [
            'check_dracut_module_for_oem_install_in_package_list',
            'check_container_tool_chain_installed'
        ]
        assert runtime_config.get_obs_api_credentials() == [
            {'user_name': 'user_credentials'}
        ]

    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    def test_config_sections_defaults(self, mock_is_buildservice_worker):
        mock_is_buildservice_worker.return_value = True
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/defaults'}):
            runtime_config = RuntimeConfig(reread=True)

        assert runtime_config.get_bundle_compression(default=True) is True
        assert runtime_config.get_bundle_compression(default=False) is False
        assert runtime_config.is_obs_public() is True
        assert runtime_config.get_obs_download_server_url() == \
            Defaults.get_obs_download_server_url()
        assert runtime_config.get_obs_api_server_url() == \
            Defaults.get_obs_api_server_url()
        assert runtime_config.get_container_compression() == 'xz'
        assert runtime_config.get_iso_tool_category() == 'xorriso'
        assert runtime_config.get_oci_archive_tool() == 'umoci'
        assert runtime_config.get_package_changes() is False

    def test_config_sections_invalid(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/invalid'}):
            runtime_config = RuntimeConfig(reread=True)

        with self._caplog.at_level(logging.WARNING):
            assert runtime_config.get_container_compression() == 'xz'
            assert 'Skipping invalid container compression: foo' in \
                self._caplog.text
        with self._caplog.at_level(logging.WARNING):
            assert runtime_config.get_iso_tool_category() == 'xorriso'
            assert 'Skipping invalid iso tool category: foo' in \
                self._caplog.text

    def test_config_sections_other_settings(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/other'}):
            runtime_config = RuntimeConfig(reread=True)

        assert runtime_config.get_container_compression() == 'xz'
        assert runtime_config.get_package_changes() is True
