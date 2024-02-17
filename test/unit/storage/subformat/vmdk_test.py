import os
from unittest.mock import (
    patch, call, Mock, mock_open
)
from pytest import raises

import kiwi

from kiwi.defaults import Defaults
from kiwi.storage.subformat.vmdk import DiskFormatVmdk

from kiwi.exceptions import KiwiTemplateError


class TestDiskFormatVmdk:
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

        self.xml_state.get_build_type_vmconfig_entries = Mock(
            return_value=['custom entry 1', 'custom entry 2']
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

        self.iso_setup = Mock()
        self.xml_state.get_build_type_vmdvd_section = Mock(
            return_value=self.iso_setup
        )
        self.xml_state.get_luks_credentials = Mock(
            return_value=None
        )
        self.iso_setup.get_controller = Mock(
            return_value='ide'
        )
        self.iso_setup.get_id = Mock(
            return_value='0'
        )

        self.network_setup = [Mock()]
        self.xml_state.get_build_type_vmnic_entries = Mock(
            return_value=self.network_setup
        )
        self.network_setup[0].get_interface = Mock(
            return_value='0'
        )
        self.network_setup[0].get_mac = Mock(
            return_value='98:90:96:a0:3c:58'
        )
        self.network_setup[0].get_mode = Mock(
            return_value='bridged'
        )
        self.network_setup[0].get_driver = Mock(
            return_value='e1000'
        )

        self.disk_setup = Mock()
        self.xml_state.get_build_type_vmdisk_section = Mock(
            return_value=self.disk_setup
        )
        self.disk_setup.get_controller = Mock(
            return_value='lsilogic'
        )
        self.disk_setup.get_id = Mock(
            return_value='0'
        )
        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = True
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.disk_format = DiskFormatVmdk(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.disk_format.post_init(
            {'option': 'value', 'adapter_type=pvscsi': None}
        )
        assert self.disk_format.options == [
            '-o', 'adapter_type=lsilogic', '-o', 'option=value'
        ]

    def test_store_to_result_default(self):
        result = Mock()
        self.disk_format.store_to_result(result)
        assert result.add.call_args_list == [
            call(
                compress=True,
                filename='target_dir/some-disk-image.x86_64-1.2.3.vmdk',
                key='disk_format_image',
                shasum=True,
                use_for_bundle=True
            ),
            call(
                compress=False,
                filename='target_dir/some-disk-image.x86_64-1.2.3.vmx',
                key='disk_format_machine_settings',
                shasum=False,
                use_for_bundle=True
            )
        ]

    def test_store_to_result_with_luks(self):
        result = Mock()
        self.xml_state.get_luks_credentials = Mock(
            return_value='foo'
        )
        self.disk_format.store_to_result(result)
        assert result.add.call_args_list == [
            call(
                compress=False,
                filename='target_dir/some-disk-image.x86_64-1.2.3.vmdk',
                key='disk_format_image',
                shasum=True,
                use_for_bundle=True
            ),
            call(
                compress=False,
                filename='target_dir/some-disk-image.x86_64-1.2.3.vmx',
                key='disk_format_machine_settings',
                shasum=False,
                use_for_bundle=True
            )
        ]
        self.xml_state.get_luks_credentials = Mock(
            return_value=None
        )

    @patch('kiwi.storage.subformat.vmdk.VmwareSettingsTemplate.get_template')
    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    def test_create_image_format_template_error(
        self, mock_exists, mock_command, mock_get_template
    ):
        template = Mock()
        mock_get_template.return_value = template
        template.substitute.side_effect = Exception
        with patch('builtins.open'):
            with raises(KiwiTemplateError):
                self.disk_format.create_image_format()

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    def test_create_image_format(
        self, mock_exists, mock_command
    ):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        m_open.assert_called_once_with(
            'target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w'
        )

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    def test_create_image_format_encoding_exists(
        self, mock_exists, mock_command
    ):
        mock_exists.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        m_open.assert_called_once_with(
            'target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w'
        )
        assert m_open.return_value.write.call_args_list[2] == call(
            'custom entry 2' + os.linesep
        )
