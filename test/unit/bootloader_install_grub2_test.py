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
    @patch('platform.machine')
    def setup(self, mock_machine, mock_mount):
        mock_machine.return_value = 'x86_64'
        self.custom_args = {
            'boot_device': '/dev/mapper/loop0p2',
            'root_device': '/dev/mapper/loop0p1'
        }
        root_mount = mock.Mock()
        root_mount.device = self.custom_args['root_device']
        root_mount.mountpoint = 'tmp_root'

        boot_mount = mock.Mock()
        boot_mount.device = self.custom_args['boot_device']
        boot_mount.mountpoint = 'tmp_boot'
        
        self.mount_managers = [boot_mount, root_mount]

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount.side_effect = side_effect

        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )

        self.bootloader = BootLoaderInstallGrub2(
            'root_dir', device_provider, self.custom_args
        )
        self.bootloader.device_mount = mock.Mock()
        self.bootloader.proc_mount = mock.Mock()
        self.bootloader.sysfs_mount = mock.Mock()
        self.bootloader.efi_mount = mock.Mock()

        assert self.bootloader.target == 'i386-pc'
        assert self.bootloader.install_arguments == [
            '--skip-fs-probe'
        ]

    @patch('platform.machine')
    def test_post_init_ppc(self, mock_machine):
        mock_machine.return_value = 'ppc64'
        self.custom_args.update(
            {'prep_device': '/dev/mapper/loop0p2'}
        )
        self.bootloader.post_init(self.custom_args)
        assert self.bootloader.target == 'powerpc-ieee1275'
        assert self.bootloader.install_arguments == [
            '--skip-fs-probe', '--no-nvram'
        ]

    @patch('platform.machine')
    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_ppc_no_prep_device(self, mock_machine):
        mock_machine.return_value = 'ppc64'
        self.bootloader.post_init(self.custom_args)

    @patch('platform.machine')
    @raises(KiwiBootLoaderGrubPlatformError)
    def test_unsupported_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported'
        self.bootloader.post_init(self.custom_args)

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_boot_device(self):
        self.bootloader.post_init({})

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_no_root_device(self):
        self.bootloader.post_init({'boot_device': 'a'})

    @raises(KiwiBootLoaderGrubInstallError)
    def test_post_init_secure_boot_no_efi_device(self):
        self.custom_args.update({'firmware': 'uefi'})
        self.bootloader.post_init(self.custom_args)

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

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    def test_install_secure_boot(self, mock_mount_manager, mock_command):
        self.custom_args.update({
            'efi_device': '/dev/mapper/loop0p3',
            'firmware': 'uefi'
        })
        root_mount = mock.Mock()
        root_mount.device = self.custom_args['root_device']
        root_mount.mountpoint = 'tmp_root'

        boot_mount = mock.Mock()
        boot_mount.device = self.custom_args['boot_device']
        boot_mount.mountpoint = 'tmp_boot'

        efi_mount = mock.Mock()
        efi_mount.device = self.custom_args['efi_device']
        efi_mount.mountpoint = 'tmp_efi'

        dev_mount = mock.Mock()
        dev_mount.device = 'devtmpfs'
        dev_mount.mountpoint = 'dev'

        proc_mount = mock.Mock()
        proc_mount.device = 'proc'
        proc_mount.mountpoint = 'proc'

        sys_mount = mock.Mock()
        sys_mount.device = 'sysfs'
        sys_mount.mountpoint = 'sys'

        mount_managers = [
            sys_mount, proc_mount, dev_mount, efi_mount, boot_mount, root_mount
        ]

        def side_effect(device, mountpoint=None):
            return mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.post_init(self.custom_args)
        self.bootloader.boot_mount.device = self.bootloader.root_mount.device
        self.bootloader.install()

        assert mock_command.call_args_list == [
            call([
                'grub2-install', '--skip-fs-probe',
                '--directory', 'tmp_root/usr/lib/grub2/i386-pc',
                '--boot-directory', 'tmp_root/boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                '/dev/some-device'
            ]),
            call([
                'cp', 'tmp_root/usr/sbin/grub2-install',
                'tmp_root/usr/sbin/grub2-install.orig'
            ]),
            call([
                'cp', 'tmp_root/bin/true', 'tmp_root/usr/sbin/grub2-install'
            ]),
            call([
                'chroot', 'tmp_root', 'shim-install', '--removable',
                '/dev/some-device'
            ]),
            call([
                'cp', 'tmp_root/usr/sbin/grub2-install.orig',
                'tmp_root/usr/sbin/grub2-install'
            ])
        ]
        dev_mount.bind_mount.assert_called_once_with()
        proc_mount.bind_mount.assert_called_once_with()
        sys_mount.bind_mount.assert_called_once_with()
        efi_mount.mount.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('platform.machine')
    def test_install_ppc_ieee1275(
        self, mock_machine, mock_mount_manager, mock_command
    ):
        mock_machine.return_value = 'ppc64'
        self.custom_args.update(
            {'prep_device': '/dev/mapper/loop0p2'}
        )
        self.bootloader.boot_mount.device = self.bootloader.root_mount.device
        self.bootloader.post_init(self.custom_args)

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
        self.bootloader.device_mount.umount.assert_called_once_with(
            delete_mountpoint=False
        )
        self.bootloader.proc_mount.umount.assert_called_once_with(
            delete_mountpoint=False
        )
        self.bootloader.sysfs_mount.umount.assert_called_once_with(
            delete_mountpoint=False
        )
        self.bootloader.efi_mount.umount.assert_called_once_with(
            delete_mountpoint=False
        )
        self.bootloader.boot_mount.umount.assert_called_once_with(
            delete_mountpoint=False
        )
        self.bootloader.root_mount.umount.assert_called_once_with()
