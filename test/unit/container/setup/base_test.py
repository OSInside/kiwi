from unittest.mock import patch, call, mock_open
from pytest import raises

from kiwi.container.setup.base import ContainerSetupBase

from kiwi.exceptions import KiwiContainerSetupError


class TestContainerSetupBase:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True

        self.container = ContainerSetupBase('root_dir')

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('os.path.exists')
    def test_container_root_dir_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiContainerSetupError):
            ContainerSetupBase('root_dir')

    def test_setup(self):
        with raises(NotImplementedError):
            self.container.setup()

    def test_post_init(self):
        self.container.custom_args == {}

    def test_get_container_name(self):
        assert self.container.get_container_name() == 'system-container'

    @patch('os.path.exists')
    def test_deactivate_bootloader_setup(self, mock_exists):
        mock_exists.return_value = True

        m_open = mock_open(read_data='LOADER_LOCATION="mylocation"')
        with patch('builtins.open', m_open, create=True):
            self.container.deactivate_bootloader_setup()

        assert m_open.call_args_list[0] == call(
            'root_dir/etc/sysconfig/bootloader', 'r'
        )
        assert m_open.return_value.write.call_args_list == [
            call('LOADER_LOCATION="none"\nLOADER_TYPE="none"\n')
        ]

    @patch('os.path.exists')
    def test_deactivate_root_filesystem_check(self, mock_exists):
        mock_exists.return_value = True

        m_open = mock_open(read_data=None)
        with patch('builtins.open', m_open, create=True):
            self.container.deactivate_root_filesystem_check()

        assert m_open.call_args_list[0] == call(
            'root_dir/etc/sysconfig/boot', 'r'
        )
        assert m_open.return_value.write.call_args_list == [
            call('ROOTFS_BLKDEV="/dev/null"\n')
        ]

    @patch('os.path.exists')
    @patch('kiwi.container.setup.base.Command.run')
    def test_deactivate_systemd_service(self, mock_command, mock_exists):
        mock_exists.return_value = True
        self.container.deactivate_systemd_service('my.service')
        mock_command.assert_called_once_with(
            [
                'ln',
                '-s',
                '-f',
                '/dev/null',
                'root_dir/usr/lib/systemd/system/my.service',
            ]
        )

    @patch('os.readlink')
    @patch('os.path.islink')
    @patch('kiwi.container.setup.base.Command.run')
    def test_deactivate_systemd_service_already_deactivated(
        self, mock_command, mock_islink, mock_readlink
    ):
        mock_islink.return_value = True
        mock_readlink.return_value = '/dev/null'
        self.container.deactivate_systemd_service('my.service')
        mock_readlink.assert_called_once_with(
            'root_dir/usr/lib/systemd/system/my.service'
        )
        # the existing link is kept as it is
        assert not mock_command.called

    @patch('os.path.exists')
    @patch('kiwi.container.setup.base.Command.run')
    def test_deactivate_systemd_service_failed(self, mock_command, mock_exists):
        mock_exists.return_value = True
        mock_command.side_effect = Exception
        with raises(KiwiContainerSetupError):
            self.container.deactivate_systemd_service('my.service')

    @patch('os.path.exists')
    def test_setup_root_console(self, mock_exists):
        mock_exists.return_value = False

        m_open = mock_open(read_data=None)
        with patch('builtins.open', m_open, create=True):
            self.container.setup_root_console()

        assert m_open.call_args_list == [
            call('root_dir/etc/securetty', 'w'),
            call('root_dir/etc/securetty', 'r'),
            call('root_dir/etc/securetty', 'w'),
        ]
        assert m_open.return_value.write.call_args_list == [call('console\n')]

    def test_update_config_unchanged(self):
        # a config file which is already setup, e.g by a former
        # container setup on the same root tree, is not written
        m_open = mock_open(read_data='console\ntty1\n')
        with patch('builtins.open', m_open, create=True):
            self.container._update_config(
                'root_dir/etc/securetty', {'console': 'console'}
            )
        assert m_open.call_args_list == [call('root_dir/etc/securetty', 'r')]
        assert not m_open.return_value.write.called

    def test_update_config_changed(self):
        m_open = mock_open(
            read_data='LOADER_TYPE="grub2"\nLOADER_LOCATION="mbr"\n'
        )
        with patch('builtins.open', m_open, create=True):
            self.container._update_config(
                'root_dir/etc/sysconfig/bootloader',
                {'LOADER_TYPE': 'LOADER_TYPE="none"'},
            )
        # the file keeps its layout, no empty line is added
        assert m_open.return_value.write.call_args_list == [
            call('LOADER_TYPE="none"\nLOADER_LOCATION="mbr"\n')
        ]
