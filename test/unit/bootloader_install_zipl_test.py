from nose.tools import *
from mock import patch
from mock import call

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install_zipl import BootLoaderInstallZipl


class TestBootLoaderInstallZipl(object):
    @patch('kiwi.bootloader_install_zipl.mkdtemp')
    def setup(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        self.bootloader = BootLoaderInstallZipl(
            'root_dir', device_provider, {'boot_device': '/dev/mapper/loop0p1'}
        )

    @raises(KiwiBootLoaderZiplInstallError)
    def test_post_init_missing_boot_mount_path(self):
        self.bootloader.post_init(None)

    @patch('kiwi.bootloader_install_zipl.Command.run')
    @patch('kiwi.bootloader_install_zipl.Path.remove')
    def test_install(self, mock_path, mock_command):
        self.bootloader.install()
        assert mock_command.call_args_list == [
            call(
                ['mount', '/dev/mapper/loop0p1', 'tmpdir']
            ),
            call(
                ['bash', '-c', 'cd tmpdir && zipl -V -c tmpdir/config -m menu']
            ),
            call(
                ['umount', 'tmpdir']
            )
        ]
        mock_path.assert_called_once_with('tmpdir')

    @patch('kiwi.bootloader_install_zipl.Command.run')
    def test_destructor_valid_mountpoint(self, mock_command):
        self.bootloader.is_mounted = True
        self.bootloader.__del__()
        self.bootloader.is_mounted = False
        mock_command.call_args_list == [
            call(['umount', 'tmpdir']),
            call(['rmdir', 'tmpdir'])
        ]

    @patch('kiwi.bootloader_install_zipl.Command.run')
    @patch('kiwi.logger.log.warning')
    @patch('kiwi.bootloader_install_zipl.Path.remove')
    @patch('time.sleep')
    def test_destructor_mountpoint_busy(
        self, mock_sleep, mock_path, mock_warn, mock_command
    ):
        self.bootloader.is_mounted = True
        mock_command.side_effect = Exception
        self.bootloader.__del__()
        self.bootloader.is_mounted = False
        assert mock_warn.called
