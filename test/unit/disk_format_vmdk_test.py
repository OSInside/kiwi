from nose.tools import *
from mock import patch
from mock import call
import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.disk_format_vmdk import DiskFormatVmdk


class TestDiskFormatVmdk(object):
    def setup(self):
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.disk_format = DiskFormatVmdk(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value'})
        assert self.disk_format.options == ['-o', 'option', 'value']

    @patch('kiwi.disk_format_vmdk.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_create_image_format_skip_descriptor_update(
        self, mock_log_warn, mock_exists, mock_command
    ):
        mock_exists.return_value = False
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-c', '-f', 'raw',
                'target_dir/some-disk-image.raw', '-O', 'vmdk',
                'target_dir/some-disk-image.vmdk'
            ]
        )
        assert mock_log_warn.called

    @raises(KiwiVmdkToolsError)
    @patch('kiwi.disk_format_vmdk.Command.run')
    @patch('os.path.exists')
    def test_create_image_format_invalid_tools_version(
        self, mock_exists, mock_command
    ):
        command = mock.Mock()
        command.output = 'bogus-version'
        mock_command.return_value = command
        mock_exists.return_value = True
        self.disk_format.create_image_format()

    @patch('kiwi.disk_format_vmdk.Command.run')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_create_image_format(
        self, mock_open, mock_exists, mock_command
    ):
        qemu_img_result = mock.Mock()
        vmtoolsd_result = mock.Mock()
        vmtoolsd_result.output = \
            'VMware Tools daemon, version 9.4.6.33107 (build-0815)'
        dd_result = mock.Mock()
        dd_result.output = 'dd-out'

        command_results = [
            dd_result, vmtoolsd_result, qemu_img_result
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        mock_exists.return_value = True

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('target_dir/some-disk-image.vmdk', 'wb')
        ]
        assert file_mock.write.call_args_list == [
            call('encoding="UTF-8"\ndd-out\nddb.toolsInstallType = "4"\nddb.toolsVersion = "9350"')
        ]
        assert file_mock.seek.call_args_list == [
            call(512, 0), call(0, 2)
        ]
