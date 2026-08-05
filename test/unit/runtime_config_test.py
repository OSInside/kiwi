import logging
import yaml
from unittest.mock import (
    patch, call
)
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

    def setup_method(self, cls):
        self.setup()

    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test__get_attribute_raises_on_invalid_structure(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/broken'}):
            runtime_config = RuntimeConfig(reread=True)
            with raises(KiwiRuntimeConfigFormatError):
                runtime_config._get_attribute('foo', 'bar')

    @patch('kiwi.defaults.CUSTOM_RUNTIME_CONFIG_FILE', 'some-config-file')
    def test_init_raises_custom_config_file_not_found(self):
        with patch('os.path.isfile', return_value=False):
            with raises(KiwiRuntimeConfigFileError):
                RuntimeConfig(reread=True)

    def test_merge_strategy(self):
        with open('../data/kiwi.yml', 'r') as config:
            master = yaml.safe_load(config)
        with open('../data/kiwi_merge_ok.yml', 'r') as config:
            slave_ok = yaml.safe_load(config)
        with open('../data/kiwi_merge_invalid_dict.yml', 'r') as config:
            slave_invalid_dict = yaml.safe_load(config)
        with open('../data/kiwi_merge_invalid_list.yml', 'r') as config:
            slave_invalid_list = yaml.safe_load(config)
        assert RuntimeConfig._merge(master, slave_ok) == {
            'xz': {
                'options': '--foo'
            },
            'shasum': {
                'size': '256'
            },
            'bundle': {
                'shasum_size': '256',
                'compress': False
            },
            'runtime_checks': {
                'disable': [
                    'check_boot_description_exists',
                    'check_container_tool_chain_installed',
                    'check_repositories_configured'
                ]
            }
        }
        with raises(NotImplementedError):
            RuntimeConfig._merge(master, slave_invalid_dict)
        with raises(NotImplementedError):
            RuntimeConfig._merge(master, slave_invalid_list)

    @patch('yaml.safe_load')
    @patch('kiwi.defaults.CUSTOM_RUNTIME_CONFIG_FILE', 'some-custom-file')
    def test_reading_custom_config_file(self, mock_yaml):
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open') as m_open:
                RuntimeConfig(reread=True)
                m_open.assert_has_calls(
                    [
                        call('some-custom-file', 'r')
                    ]
                )

    @patch('os.path.exists')
    @patch('yaml.safe_load')
    @patch('os.path.isdir')
    @patch('os.listdir')
    def test_reading_system_wide_config_file_from_etc(
        self,
        mock_os_listdir,
        mock_os_path_isdir,
        mock_yaml,
        mock_exists
    ):
        mock_os_listdir.return_value = ['some.yml']

        def os_path_exists(config):
            if config == '/etc/kiwi.yml':
                return True
            return False

        def os_path_isdir(config):
            if config == '/etc/kiwi.yml.d':
                return True
            return False

        mock_exists.side_effect = os_path_exists
        mock_os_path_isdir.side_effect = os_path_isdir
        with patch('builtins.open') as m_open:
            RuntimeConfig(reread=True)
            assert m_open.call_args_list == [
                call('/etc/kiwi.yml', 'r'),
                call('/etc/kiwi.yml.d/some.yml', 'r')
            ]

    @patch('os.path.exists')
    @patch('yaml.safe_load')
    @patch('os.path.isdir')
    @patch('os.listdir')
    def test_reading_system_wide_config_file_from_usr(
        self,
        mock_os_listdir,
        mock_os_path_isdir,
        mock_yaml,
        mock_exists
    ):
        mock_os_listdir.return_value = ['some.yml']

        def os_path_exists(config):
            if config == '/usr/share/kiwi/kiwi.yml':
                return True
            return False

        def os_path_isdir(config):
            if config == '/usr/share/kiwi/kiwi.yml.d':
                return True
            return False

        mock_exists.side_effect = os_path_exists
        mock_os_path_isdir.side_effect = os_path_isdir
        with patch('builtins.open') as m_open:
            RuntimeConfig(reread=True)
            assert m_open.call_args_list == [
                call('/usr/share/kiwi/kiwi.yml', 'r'),
                call('/usr/share/kiwi/kiwi.yml.d/some.yml', 'r')
            ]

    @patch('kiwi.defaults.ETC_RUNTIME_CONFIG_FILE', '../data/kiwi.yml')
    @patch('kiwi.defaults.ETC_RUNTIME_CONFIG_DIR', '../data/kiwi.yml.d')
    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    def test_config_sections_from_system_wide_etc_config(
        self, mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = False
        runtime_config = RuntimeConfig(reread=True)
        assert runtime_config.get_xz_options() == ['-a', '-b', 'xxx']
        assert runtime_config.get_mapper_tool() == 'partx'
        assert runtime_config.get_checksum_handler(
            '../data/metalink'
        ).suffix == '.sha512'
        assert runtime_config.get_checksum_handler(
            '../data/metalink', bundle_lookup=True
        ).suffix == '.sha256'

    @patch('kiwi.defaults.ETC_RUNTIME_CONFIG_FILE', '')
    @patch('kiwi.defaults.ETC_RUNTIME_CONFIG_DIR', '')
    @patch('kiwi.defaults.USR_RUNTIME_CONFIG_FILE', '../data/kiwi.yml')
    @patch('kiwi.defaults.USR_RUNTIME_CONFIG_DIR', '../data/kiwi.yml.d')
    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    def test_config_sections_from_system_wide_usr_config(
        self,
        mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = False
        runtime_config = RuntimeConfig(reread=True)
        assert runtime_config.get_xz_options() == ['-a', '-b', 'xxx']
        assert runtime_config.get_mapper_tool() == 'partx'

    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    def test_config_sections_from_home_base_config(
        self, mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = False
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/ok'}):
            runtime_config = RuntimeConfig(reread=True)

        assert runtime_config.get_xz_options() == ['-a', '-b', 'xxx']
        assert runtime_config.is_obs_public() is True
        assert runtime_config.get_bundle_compression() is True
        assert runtime_config.get_obs_download_server_url() == \
            'http://example.com'
        assert runtime_config.get_obs_api_server_url() == \
            'https://api.example.com'
        assert runtime_config.get_container_compression() is False
        assert runtime_config.get_iso_tool_category() == 'xorriso'
        assert runtime_config.get_iso_media_tag_tool() == 'isomd5sum'
        assert runtime_config.get_oci_archive_tool() == 'umoci'
        assert runtime_config.get_mapper_tool() == 'partx'
        assert runtime_config.get_package_changes() is True
        assert runtime_config.get_disabled_runtime_checks() == [
            'check_dracut_module_for_oem_install_in_package_list',
            'check_container_tool_chain_installed'
        ]

    @patch('kiwi.runtime_checker.Defaults.is_buildservice_worker')
    @patch('kiwi.runtime_checker.Defaults.get_platform_name')
    def test_config_sections_defaults(
        self, mock_get_platform_name, mock_is_buildservice_worker
    ):
        mock_get_platform_name.return_value = 's390x'
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
        assert runtime_config.get_container_compression() is True
        assert runtime_config.get_iso_tool_category() == 'xorriso'
        assert runtime_config.get_iso_media_tag_tool() == 'checkmedia'
        assert runtime_config.get_oci_archive_tool() == 'umoci'
        assert runtime_config.get_mapper_tool() == 'kpartx'
        assert runtime_config.get_package_changes() is False
        assert runtime_config.\
            get_credentials_verification_metadata_signing_key_file() == ''

        mock_get_platform_name.return_value = 'x86_64'
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/defaults'}):
            runtime_config = RuntimeConfig(reread=True)
        assert runtime_config.get_mapper_tool() == 'partx'
        assert runtime_config.get_checksum_handler(
            '../data/metalink'
        ).suffix == '.sha256'

    def test_config_sections_invalid(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/invalid'}):
            runtime_config = RuntimeConfig(reread=True)

        with self._caplog.at_level(logging.WARNING):
            assert runtime_config.get_container_compression() is True
            assert 'Skipping invalid container compression: foo' in \
                self._caplog.text
        with self._caplog.at_level(logging.WARNING):
            assert runtime_config.get_iso_tool_category() == 'xorriso'
            assert 'Skipping invalid iso tool category: foo' in \
                self._caplog.text

        with self._caplog.at_level(logging.WARNING):
            assert runtime_config.get_iso_media_tag_tool() == "checkmedia"
            assert 'Skipping invalid iso media tag tool: foo' in \
                self._caplog.text

    def test_config_sections_other_settings(self):
        with patch.dict('os.environ', {'HOME': '../data/kiwi_config/other'}):
            runtime_config = RuntimeConfig(reread=True)

        assert runtime_config.get_container_compression() is True
        assert runtime_config.get_package_changes() is True
        assert runtime_config.get_iso_media_tag_tool() == "checkmedia"
