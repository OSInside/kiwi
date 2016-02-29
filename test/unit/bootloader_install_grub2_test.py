from nose.tools import *
from mock import patch
from mock import call

import mock
import kiwi
from . import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader.install.grub2 import BootLoaderInstallGrub2
from kiwi.defaults import Defaults


class TestBootLoaderInstallGrub2(object):
    @patch('kiwi.bootloader.install.grub2.MountManager')
    def setup(self, mock_mount):
        custom_args = {
            'boot_device': '/dev/mapper/loop0p2',
            'root_device': '/dev/mapper/loop0p1'
        }
        root_mount = mock.Mock()
        root_mount.device = custom_args['root_device']
        root_mount.mountpoint = 'tmp_root'

        boot_mount = mock.Mock()
        boot_mount.device = custom_args['boot_device']
        boot_mount.mountpoint = 'tmp_boot'
        
        mount_managers = [boot_mount, root_mount]

        def side_effect(arg):
            return mount_managers.pop()

        mock_mount.side_effect = side_effect

        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )

        self.bootloader = BootLoaderInstallGrub2(
            'root_dir', device_provider, custom_args
        )

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_boot_device(self):
        self.bootloader.post_init({})

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_root_device(self):
        self.bootloader.post_init({'boot_device': 'a'})

    @patch('kiwi.bootloader.install.grub2.Command.run')
    def test_install_with_extra_boot_partition(self, mock_command):
        self.bootloader.install()
        self.bootloader.root_mount.mount.assert_called_once_with()
        self.bootloader.boot_mount.mount.assert_called_once_with()
        mock_command.assert_called_once_with(
            [
                'grub2-install', '--skip-fs-probe',
                '--directory', 'tmp_root/usr/lib/grub2/i386-pc',
                '--boot-directory', 'tmp_boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                '/dev/some-device'
            ]
        )

    @patch('kiwi.bootloader.install.grub2.Command.run')
    def test_install(self, mock_command):
        self.bootloader.boot_mount.device = self.bootloader.root_mount.device
        self.bootloader.install()
        self.bootloader.root_mount.mount.assert_called_once_with()
        mock_command.assert_called_once_with(
            [
                'grub2-install', '--skip-fs-probe',
                '--directory', 'tmp_root/usr/lib/grub2/i386-pc',
                '--boot-directory', 'tmp_root/boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                '/dev/some-device'
            ])

    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    def test_install_ieee1275(self, mock_command, mock_mount):
        custom_args = {
            'boot_device': '/dev/mapper/loop0p2',
            'root_device': '/dev/mapper/loop0p2',
            'prep_device': '/dev/mapper/loop0p1'
        }
        root_mount = mock.Mock()
        root_mount.device = custom_args['root_device']
        root_mount.mountpoint = 'tmp_root'

        boot_mount = mock.Mock()
        boot_mount.device = custom_args['boot_device']
        boot_mount.mountpoint = 'tmp_boot'
        
        mount_managers = [boot_mount, root_mount]

        def side_effect(arg):
            return mount_managers.pop()

        mock_mount.side_effect = side_effect

        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )

        self.bootloader = BootLoaderInstallGrub2(
            'root_dir', device_provider, custom_args
        )
        self.bootloader.extra_boot_partition = False
        self.bootloader.boot_mount.device = self.bootloader.root_mount.device
        self.bootloader.install()
        self.bootloader.root_mount.mount.assert_called_once_with()
        mock_command.assert_called_once_with == [
            call([
                'grub2-install', '--skip-fs-probe', '--no-nvram',
                '--directory', 'tmp_root/usr/lib/grub2/powerpc-ieee1275',
                '--boot-directory', 'tmp_root/boot',
                '--target', 'powerpc-ieee1275',
                '--modules', ' '.join(Defaults.get_grub_ofw_modules()),
                '/dev/mapper/loop0p1'
            ])
        ]

    def test_destructor(self):
        self.bootloader.__del__()
        self.bootloader.root_mount.umount.assert_called_once_with()
        self.bootloader.boot_mount.umount.assert_called_once_with()
