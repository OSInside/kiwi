from mock import patch
from mock import call
import mock
import os

from .test_helper import raises, patch_open

from kiwi.exceptions import (
    KiwiTemplateError
)

from kiwi.storage.subformat.vmdk import DiskFormatVmdk


class TestDiskFormatVmdk(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        mock_machine.return_value = 'x86_64'
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        xml_data.get_displayname = mock.Mock(
            return_value=None
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )

        self.xml_state.get_build_type_vmconfig_entries = mock.Mock(
            return_value=['custom entry 1', 'custom entry 2']
        )

        self.machine_setup = mock.Mock()
        self.xml_state.get_build_type_machine_section = mock.Mock(
            return_value=self.machine_setup
        )
        self.machine_setup.get_HWversion = mock.Mock(
            return_value='42'
        )
        self.machine_setup.get_guestOS = mock.Mock(
            return_value='suse'
        )
        self.machine_setup.get_memory = mock.Mock(
            return_value='4096'
        )
        self.machine_setup.get_ncpus = mock.Mock(
            return_value='2'
        )

        self.iso_setup = mock.Mock()
        self.xml_state.get_build_type_vmdvd_section = mock.Mock(
            return_value=self.iso_setup
        )
        self.iso_setup.get_controller = mock.Mock(
            return_value='ide'
        )
        self.iso_setup.get_id = mock.Mock(
            return_value='0'
        )

        self.network_setup = [mock.Mock()]
        self.xml_state.get_build_type_vmnic_entries = mock.Mock(
            return_value=self.network_setup
        )
        self.network_setup[0].get_interface = mock.Mock(
            return_value='0'
        )
        self.network_setup[0].get_mac = mock.Mock(
            return_value='98:90:96:a0:3c:58'
        )
        self.network_setup[0].get_mode = mock.Mock(
            return_value='bridged'
        )
        self.network_setup[0].get_driver = mock.Mock(
            return_value='e1000'
        )

        self.disk_setup = mock.Mock()
        self.xml_state.get_build_type_vmdisk_section = mock.Mock(
            return_value=self.disk_setup
        )
        self.disk_setup.get_controller = mock.Mock(
            return_value='lsilogic'
        )
        self.disk_setup.get_id = mock.Mock(
            return_value='0'
        )

        self.disk_format = DiskFormatVmdk(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init(
            {'option': 'value', 'adapter_type=pvscsi': None}
        )
        assert self.disk_format.options == [
            '-o', 'adapter_type=lsilogic', '-o', 'option=value'
        ]
        assert self.disk_format.patch_header_for_pvscsi is True

    def test_store_to_result(self):
        result = mock.Mock()
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

    @raises(KiwiTemplateError)
    @patch('kiwi.storage.subformat.vmdk.VmwareSettingsTemplate.get_template')
    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format_template_error(
        self, mock_open, mock_exists, mock_command, mock_get_template
    ):
        template = mock.Mock()
        mock_get_template.return_value = template
        template.substitute.side_effect = Exception
        self.disk_format.create_image_format()

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_exists, mock_command
    ):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w')
        ]

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format_encoding_exists(
        self, mock_open, mock_exists, mock_command
    ):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w')
        ]
        assert self.file_mock.write.call_args_list[2] == call(
            'custom entry 2' + os.linesep
        )

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format_pvscsi_adapter(
        self, mock_open, mock_exists, mock_command
    ):
        self.disk_format.patch_header_for_pvscsi = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = b'ddb.adapterType = "lsilogic"'

        self.disk_format.create_image_format()

        assert mock_open.call_args_list[0:2] == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vmdk', 'rb'),
            call('target_dir/some-disk-image.x86_64-1.2.3.vmdk', 'r+b')
        ]
        assert self.file_mock.seek.called_once_with(512, 0)
        assert self.file_mock.read.called_once_with(1024)
        assert self.file_mock.write.call_args_list[0] == call(
            b'ddb.adapterType = "pvscsi"'
        )
