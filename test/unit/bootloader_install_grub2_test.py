from nose.tools import *
from mock import patch
from mock import call

import mock
import kiwi
from . import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install_grub2 import BootLoaderInstallGrub2
from kiwi.defaults import Defaults


class TestBootLoaderInstallGrub2(object):
    @patch('kiwi.bootloader_install_grub2.mkdtemp')
    def setup(self, mock_mkdtemp):
        tmpdirs = ['tmp_boot', 'tmp_root']

        def side_effect():
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = side_effect
        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        self.path = mock.Mock()
        kiwi.bootloader_install_grub2.Path = self.path
        self.bootloader = BootLoaderInstallGrub2(
            'root_dir', device_provider, {
                'boot_device': '/dev/mapper/loop0p2',
                'root_device': '/dev/mapper/loop0p1'
            }
        )
        assert self.bootloader.mountpoint_root == 'tmp_root'
        assert self.bootloader.mountpoint_boot == 'tmp_boot'
        assert self.bootloader.extra_boot_partition is True

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_boot_device(self):
        self.bootloader.post_init({})

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_root_device(self):
        self.bootloader.post_init({'boot_device': 'a'})

    @patch('kiwi.bootloader_install_grub2.Command.run')
    def test_install_with_extra_boot_partition(self, mock_command):
        self.bootloader.install()
        assert mock_command.call_args_list == [
            call(['mount', '/dev/mapper/loop0p2', 'tmp_boot']),
            call(['mount', '/dev/mapper/loop0p1', 'tmp_root']),
            call([
                'grub2-install', '--skip-fs-probe',
                '--directory', 'tmp_root/usr/lib/grub2/i386-pc',
                '--boot-directory', 'tmp_boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                '/dev/some-device'
            ])
        ]

    @patch('kiwi.bootloader_install_grub2.Command.run')
    def test_install(self, mock_command):
        self.bootloader.extra_boot_partition = False
        self.bootloader.install()
        assert mock_command.call_args_list == [
            call(['mount', '/dev/mapper/loop0p1', 'tmp_root']),
            call([
                'grub2-install', '--skip-fs-probe',
                '--directory', 'tmp_root/usr/lib/grub2/i386-pc',
                '--boot-directory', 'tmp_root/boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                '/dev/some-device'
            ])
        ]

    @patch('kiwi.bootloader_install_grub2.Command.run')
    @patch('kiwi.logger.log.warning')
    @patch('time.sleep')
    def test_desstructor(self, mock_sleep, mock_warn, mock_command):
        command_return_values = [False, False, False, True, True, True]

        def side_effect(arg):
            if not command_return_values.pop():
                raise Exception

        mock_command.side_effect = side_effect
        self.bootloader.__del__()
        self.path.remove.assert_called_once_with('tmp_root')
        assert mock_command.call_args_list == [
            call(['mountpoint', 'tmp_root']),
            call(['umount', 'tmp_root']),
            call(['mountpoint', 'tmp_boot']),
            call(['umount', 'tmp_boot']),
            call(['umount', 'tmp_boot']),
            call(['umount', 'tmp_boot'])
        ]

    @patch('kiwi.bootloader_install_grub2.Command.run')
    def test_desstructor_nothing_mounted(self, mock_command):
        mock_command.side_effect = Exception
        self.bootloader.__del__()
        assert mock_command.call_args_list == [
            call(['mountpoint', 'tmp_root']),
            call(['mountpoint', 'tmp_boot'])
        ]
