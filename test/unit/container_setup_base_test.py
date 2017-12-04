from mock import patch
from mock import call
import mock

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiContainerSetupError
from kiwi.container.setup.base import ContainerSetupBase


class TestContainerSetupBase(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.context_manager_mock = mock.MagicMock()
        self.file_mock = mock.MagicMock()
        self.enter_mock = mock.MagicMock()
        self.exit_mock = mock.MagicMock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.container = ContainerSetupBase('root_dir')

    @patch('os.path.exists')
    @raises(KiwiContainerSetupError)
    def test_container_root_dir_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        ContainerSetupBase('root_dir')

    @raises(NotImplementedError)
    def test_setup(self):
        self.container.setup()

    def test_post_init(self):
        self.container.custom_args == {}

    def test_get_container_name(self):
        assert self.container.get_container_name() == 'systemContainer'

    @patch_open
    def test_create_fstab(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.container.create_fstab()
        mock_open.assert_called_once_with(
            'root_dir/etc/fstab', 'w'
        )
        assert self.file_mock.call_args_list == []

    @patch_open
    @patch('os.path.exists')
    def test_deactivate_bootloader_setup(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = 'LOADER_LOCATION="mylocation"'
        self.container.deactivate_bootloader_setup()
        assert mock_open.call_args_list[0] == call(
            'root_dir/etc/sysconfig/bootloader', 'r'
        )
        assert self.file_mock.write.call_args_list == [
            call('LOADER_LOCATION="none"\nLOADER_TYPE="none"\n')
        ]

    @patch_open
    @patch('os.path.exists')
    def test_deactivate_root_filesystem_check(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = None
        self.container.deactivate_root_filesystem_check()
        assert mock_open.call_args_list[0] == call(
            'root_dir/etc/sysconfig/boot', 'r'
        )
        assert self.file_mock.write.call_args_list == [
            call('ROOTFS_BLKDEV="/dev/null"\n')
        ]

    @patch('os.path.exists')
    @patch('kiwi.container.setup.base.Command.run')
    def test_deactivate_systemd_service(self, mock_command, mock_exists):
        mock_exists.return_value = True
        self.container.deactivate_systemd_service('my.service')
        mock_command.assert_called_once_with(
            [
                'ln', '-s', '-f', '/dev/null',
                'root_dir/usr/lib/systemd/system/my.service'
            ]
        )

    @patch('os.path.exists')
    @patch('kiwi.container.setup.base.Command.run')
    @raises(KiwiContainerSetupError)
    def test_deactivate_systemd_service_failed(self, mock_command, mock_exists):
        mock_exists.return_value = True
        mock_command.side_effect = Exception
        self.container.deactivate_systemd_service('my.service')

    @patch_open
    @patch('os.path.exists')
    def test_setup_root_console(self, mock_exists, mock_open):
        mock_exists.return_value = False
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = None
        self.container.setup_root_console()
        assert mock_open.call_args_list == [
            call('root_dir/etc/securetty', 'w'),
            call('root_dir/etc/securetty', 'r'),
            call('root_dir/etc/securetty', 'w')
        ]
        assert self.file_mock.write.call_args_list == [
            call('console\n')
        ]

    @patch('kiwi.container.setup.base.Command.run')
    @patch('kiwi.container.setup.base.DataSync')
    def test_setup_static_device_nodes(self, mock_DataSync, mock_command):
        data = mock.Mock()
        mock_DataSync.return_value = data
        self.container.setup_static_device_nodes()
        mock_DataSync.assert_called_once_with(
            '/dev/', 'root_dir/dev/'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a', '-x', '--devices', '--specials']
        )

    @patch('kiwi.container.setup.base.Command.run')
    @raises(KiwiContainerSetupError)
    def test_setup_static_device_nodes_failed(self, mock_command):
        mock_command.side_effect = Exception
        self.container.setup_static_device_nodes()
