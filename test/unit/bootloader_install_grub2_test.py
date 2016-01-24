from nose.tools import *
from mock import patch
from mock import call

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install_grub2 import BootLoaderInstallGrub2


class TestBootLoaderInstallGrub2(object):
    def setup(self):
        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        self.bootloader = BootLoaderInstallGrub2(
            'root_dir', device_provider
        )

    def test_post_init(self):
        self.bootloader.post_init(None)
        assert self.bootloader.temporary_boot_dir is None

    @patch('__builtin__.open')
    @patch('kiwi.bootloader_install_grub2.Command.run')
    @patch('kiwi.bootloader_install_grub2.mkdtemp')
    @patch('kiwi.bootloader_install_grub2.NamedTemporaryFile')
    def test_install(self, mock_tmpfile, mock_mkdtemp, mock_command, mock_open):
        mock_mkdtemp.return_value = 'tmpdir'
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_tmpfile.return_value = tmpfile
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.bootloader.install()

        mock_open.assert_called_once_with('tmpfile', 'w')
        file_mock.write.assert_called_once_with(
            '(hd0) /dev/some-device\n'
        )
        assert mock_command.call_args_list == [
            call(['cp', '-a', 'root_dir/boot/', 'tmpdir']),
            call([
                'grub2-bios-setup', '-f',
                '-d', 'tmpdir/boot/grub2/i386-pc',
                '-m', 'tmpfile',
                '/dev/some-device'
            ])
        ]

    @patch('kiwi.bootloader_install_grub2.Path.wipe')
    def test_desstructor(self, mock_wipe):
        self.bootloader.temporary_boot_dir = 'tmpdir'
        self.bootloader.__del__()
        mock_wipe.assert_called_once_with('tmpdir')
        self.bootloader.temporary_boot_dir = None
