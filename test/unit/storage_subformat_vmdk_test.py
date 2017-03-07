from mock import patch
from mock import call
import mock
import os

from .test_helper import raises, patch_open

from textwrap import dedent

from kiwi.exceptions import (
    KiwiVmdkToolsError,
    KiwiTemplateError
)

from kiwi.storage.subformat.vmdk import DiskFormatVmdk

from builtins import bytes


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

        self.network_setup = mock.Mock()
        self.xml_state.get_build_type_vmnic_section = mock.Mock(
            return_value=self.network_setup
        )
        self.network_setup.get_interface = mock.Mock(
            return_value='0'
        )
        self.network_setup.get_mac = mock.Mock(
            return_value='98:90:96:a0:3c:58'
        )
        self.network_setup.get_mode = mock.Mock(
            return_value='bridged'
        )
        self.network_setup.get_driver = mock.Mock(
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
        self.vmdk_header_update = dedent('''
            encoding="UTF-8"
            dd-out
            ddb.toolsInstallType = "4"
            ddb.toolsVersion = "9350"
        ''').strip()
        self.vmdk_header_update = bytes(self.vmdk_header_update, 'utf-8')

        self.vmdk_settings_formatted = dedent('''
            #!/usr/bin/env vmware
            # kiwi generated VMware settings file
            config.version = "8"
            tools.syncTime = "true"
            uuid.action = "create"
            virtualHW.version = "42"
            displayName = "some-disk-image"
            guestOS = "suse"
            priority.grabbed = "normal"
            priority.ungrabbed = "normal"
            powerType.powerOff = "soft"
            powerType.powerOn  = "soft"
            powerType.suspend  = "soft"
            powerType.reset    = "soft"
            memsize = "4096"
            numvcpus = "2"
            scsi0.present = "true"
            scsi0.sharedBus = "none"
            scsi0.virtualDev = "lsilogic"
            scsi0:0.present = "true"
            scsi0:0.fileName = "target_dir/some-disk-image.x86_64-1.2.3.vmdk"
            scsi0:0.deviceType = "scsi-hardDisk"
            ethernet0.present = "true"
            ethernet0.allow64bitVmxnet = "true"
            ethernet0.addressType = "static"
            ethernet0.address = "98:90:96:a0:3c:58"
            ethernet0.virtualDev = "e1000"
            ethernet0.connectionType = "bridged"
            ide0:0.present = "true"
            ide0:0.deviceType = "cdrom-raw"
            ide0:0.autodetect = "true"
            ide0:0.startConnected = "true"
            usb.present = "true"
        ''').strip() + '\n'

        self.vmdk_settings = ''
        for entry in self.vmdk_settings_formatted.split('\n'):
            if entry:
                self.vmdk_settings += entry.strip() + '\n'

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value'})
        assert self.disk_format.options == ['-o', 'option', 'value']

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

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch_open
    def test_create_image_format_skip_descriptor_update(
        self, mock_open, mock_log_warn, mock_exists, mock_command
    ):
        mock_exists.return_value = False
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-f', 'raw',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '-O', 'vmdk',
                'target_dir/some-disk-image.x86_64-1.2.3.vmdk'
            ]
        )
        assert mock_log_warn.called

    @raises(KiwiVmdkToolsError)
    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    def test_create_image_format_invalid_tools_version(
        self, mock_exists, mock_command
    ):
        command = mock.Mock()
        command.output = 'bogus-version'
        mock_command.return_value = command
        mock_exists.return_value = True
        self.disk_format.create_image_format()

    @raises(KiwiTemplateError)
    @patch('kiwi.storage.subformat.vmdk.VmwareSettingsTemplate.get_template')
    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format_template_error(
        self, mock_open, mock_exists, mock_command, mock_get_template
    ):
        qemu_img_result = mock.Mock()
        vmtoolsd_result = mock.Mock()
        vmtoolsd_result.output = \
            'VMware Tools daemon, version 9.4.6.33107 (build-0815)'
        dd_result = mock.Mock()
        dd_result.output = 'dd-out\0\0\0\0\0'

        command_results = [
            dd_result, vmtoolsd_result, qemu_img_result
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
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
        qemu_img_result = mock.Mock()
        vmtoolsd_result = mock.Mock()
        vmtoolsd_result.output = \
            'VMware Tools daemon, version 9.4.6.33107 (build-0815)'
        dd_result = mock.Mock()
        dd_result.output = 'dd-out\0\0\0\0\0'

        command_results = [
            dd_result, vmtoolsd_result, qemu_img_result
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vmdk', 'ab'),
            call('target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w')
        ]
        assert self.file_mock.write.call_args_list[0] == call(
            self.vmdk_header_update
        )
        assert self.file_mock.write.call_args_list[1] == call(
            self.vmdk_settings
        )
        assert self.file_mock.seek.call_args_list == [
            call(512, 0), call(0, 2)
        ]

    @patch('kiwi.storage.subformat.vmdk.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_create_image_format_encoding_exists(
        self, mock_open, mock_exists, mock_command
    ):
        qemu_img_result = mock.Mock()
        vmtoolsd_result = mock.Mock()
        vmtoolsd_result.output = \
            'VMware Tools daemon, version 9.4.6.33107 (build-0815)'
        dd_result = mock.Mock()
        dd_result.output = 'encoding="UTF-8"\ndd-out\0\0\0\0\0'

        command_results = [
            dd_result, vmtoolsd_result, qemu_img_result
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vmdk', 'ab'),
            call('target_dir/some-disk-image.x86_64-1.2.3.vmx', 'w')
        ]
        assert self.file_mock.write.call_args_list[0] == call(
            self.vmdk_header_update
        )
        assert self.file_mock.write.call_args_list[1] == call(
            self.vmdk_settings
        )
        assert self.file_mock.write.call_args_list[2] == call(
            'custom entry 1' + os.linesep
        )
        assert self.file_mock.write.call_args_list[3] == call(
            'custom entry 2' + os.linesep
        )
        assert self.file_mock.seek.call_args_list == [
            call(512, 0), call(0, 2)
        ]
