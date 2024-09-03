from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.storage.subformat.ova import DiskFormatOva

import kiwi

from kiwi.exceptions import (
    KiwiCommandNotFound,
    KiwiFormatSetupError
)


class TestDiskFormatOva:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.context_manager_mock = Mock()
        self.file_mock = Mock()
        self.enter_mock = Mock()
        self.exit_mock = Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        xml_data.get_displayname = Mock(
            return_value=None
        )
        self.xml_state = Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )

        self.machine_setup = Mock()
        self.xml_state.get_build_type_machine_section = Mock(
            return_value=self.machine_setup
        )
        self.machine_setup.get_HWversion = Mock(
            return_value='42'
        )
        self.machine_setup.get_guestOS = Mock(
            return_value='suse'
        )
        self.machine_setup.get_memory = Mock(
            return_value='4096'
        )
        self.machine_setup.get_ncpus = Mock(
            return_value='2'
        )

        self.machine_setup.get_ovftype = Mock(
            return_value='vmware'
        )

        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = False
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )

        self.disk_format = DiskFormatOva(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.disk_format.post_init({})

    def test_post_init_bad_ovftype(self):
        self.machine_setup.get_ovftype.return_value = 'foobar'
        with raises(KiwiFormatSetupError):
            self.disk_format.post_init({})

    def test_store_to_result(self):
        result = Mock()
        self.disk_format.store_to_result(result)
        assert result.add.call_args_list == [
            call(
                compress=False,
                filename='target_dir/some-disk-image.x86_64-1.2.3.ova',
                key='disk_format_image',
                shasum=True,
                use_for_bundle=True
            )
        ]

    @patch('kiwi.storage.subformat.ova.Path.which')
    @patch('kiwi.storage.subformat.ova.Command.run')
    @patch('kiwi.storage.subformat.vmdk.DiskFormatVmdk.create_image_format')
    @patch('kiwi.storage.subformat.ova.CommandCapabilities.has_option_in_help')
    @patch('os.stat')
    @patch('os.chmod')
    def test_create_image_format(
        self, mock_chmod, mock_stat, mock_has_option_in_help,
        mock_create_image_format, mock_command, mock_which
    ):
        mock_has_option_in_help.return_value = True
        mock_which.return_value = 'ovftool'
        mock_stat.return_value = Mock(st_mode=0o644)
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'ovftool', '--shaAlgorithm=SHA1',
                '--allowExtraConfig', '--exportFlags=extraconfig',
                'target_dir/some-disk-image.x86_64-1.2.3.vmx',
                'target_dir/some-disk-image.x86_64-1.2.3.ova'
            ]
        )

    @patch('kiwi.storage.subformat.ova.Path.which')
    def test_create_image_format_no_ovftool(self, mock_which):
        mock_which.return_value = None
        with raises(KiwiCommandNotFound):
            self.disk_format.create_image_format()
