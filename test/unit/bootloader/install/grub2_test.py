import io
from unittest.mock import (
    patch, call, MagicMock, Mock
)
from pytest import raises
import unittest.mock as mock

from kiwi.bootloader.install.grub2 import BootLoaderInstallGrub2
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiBootLoaderGrubInstallError,
    KiwiBootLoaderGrubDataError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderDiskPasswordError
)


class TestBootLoaderInstallGrub2:
    def setup(self):
        Defaults.set_platform_name('x86_64')

        self.firmware = mock.Mock()
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )

        self.custom_args = {
            'boot_device': '/dev/mapper/loop0p2',
            'root_device': '/dev/mapper/loop0p1',
            'efi_device': '/dev/mapper/loop0p3',
            'prep_device': '/dev/mapper/loop0p2',
            'system_root_volume': 'root',
            'system_volumes': {'boot/grub2': {
                'volume_options': 'subvol=@/boot/grub2',
                'volume_device': 'device'
            }},
            'firmware': self.firmware,
            'target_removable': None,
            'install_options': [],
            'shim_options': []
        }

        self.root_mount = mock.Mock()
        self.root_mount.device = self.custom_args['root_device']
        self.root_mount.mountpoint = 'tmp_root'

        self.volume_mount = mock.Mock()
        self.volume_mount.device = self.custom_args['root_device']
        self.volume_mount.mountpoint = 'tmp_volume'

        self.boot_mount = mock.Mock()
        self.boot_mount.device = self.custom_args['boot_device']
        self.boot_mount.mountpoint = 'tmp_boot'

        self.efi_mount = mock.Mock()
        self.efi_mount.device = self.custom_args['efi_device']
        self.efi_mount.mountpoint = 'tmp_efi'

        self.device_mount = mock.Mock()
        self.device_mount.device = 'devtmpfs'
        self.device_mount.mountpoint = 'dev'

        self.proc_mount = mock.Mock()
        self.proc_mount.device = 'proc'
        self.proc_mount.mountpoint = 'proc'

        self.sysfs_mount = mock.Mock()
        self.sysfs_mount.device = 'sysfs'
        self.sysfs_mount.mountpoint = 'sys'

        # the order of mount manager is reverse the order in the code
        self.mount_managers = [
            self.sysfs_mount,
            self.proc_mount,
            self.device_mount,
            self.volume_mount,
            self.efi_mount,
            self.boot_mount,
            self.root_mount
        ]

        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )

        self.bootloader = BootLoaderInstallGrub2(
            Mock(), 'root_dir', device_provider, self.custom_args
        )

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    def test_post_init_ppc_no_prep_device(self, mock_grub_path):
        self.bootloader.arch = 'ppc64'
        del self.custom_args['prep_device']
        with raises(KiwiBootLoaderGrubInstallError):
            self.bootloader.install()

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    def test_grub2_bootloader_not_installed(
        self, mock_grub_path, mock_mount_manager, mock_command
    ):
        mock_grub_path.return_value = None
        self.bootloader.arch = 'x86_64'
        with raises(KiwiBootLoaderGrubDataError):
            self.bootloader.install()

    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    def test_unsupported_platform(self, mock_grub_path):
        self.bootloader.arch = 'unsupported'
        with raises(KiwiBootLoaderGrubPlatformError):
            self.bootloader.install()

    def test_post_init_no_boot_device(self):
        with raises(KiwiBootLoaderGrubInstallError):
            self.bootloader.post_init({})

    def test_post_init_no_root_device(self):
        with raises(KiwiBootLoaderGrubInstallError):
            self.bootloader.post_init({'boot_device': 'a'})

    def test_post_init_secure_boot_no_efi_device(self):
        self.firmware.efi_mode.return_value = 'uefi'
        del self.custom_args['efi_device']
        with raises(KiwiBootLoaderGrubInstallError):
            self.bootloader.post_init(self.custom_args)

    def test_install_required(self):
        assert self.bootloader.install_required() is True

    def test_install_required_ppc_opal(self):
        self.bootloader.arch = 'ppc64'
        self.bootloader.firmware = mock.Mock()
        self.bootloader.firmware.opal_mode = mock.Mock(
            return_value=True
        )
        assert self.bootloader.install_required() is False

    def test_install_required_efi_no_csm(self):
        self.bootloader.arch = 'x86_64'
        self.bootloader.firmware = mock.Mock()
        self.bootloader.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        self.bootloader.firmware.legacy_bios_mode = mock.Mock(
            return_value=False
        )
        assert self.bootloader.install_required() is False

    def test_install_required_arm64(self):
        self.bootloader.arch = 'arm64'
        assert self.bootloader.install_required() is False

    def test_install_required_riscv64(self):
        self.bootloader.arch = 'riscv64'
        assert self.bootloader.install_required() is False

    @patch('kiwi.bootloader.install.grub2.Path.wipe')
    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    @patch('kiwi.bootloader.install.grub2.glob.glob')
    @patch('kiwi.bootloader.install.grub2.SystemSetup')
    def test_install_with_extra_boot_partition(
        self, mock_SystemSetup, mock_glob, mock_grub_path,
        mock_mount_manager, mock_command, mock_which, mock_wipe
    ):
        setup = Mock()
        mock_SystemSetup.return_value = setup
        mock_glob.return_value = ['tmp_root/boot/grub2/grubenv']
        mock_grub_path.return_value = \
            self.root_mount.mountpoint + '/usr/lib/grub2/i386-pc'

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.install()
        self.bootloader.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.boot_mount.mount.assert_called_once_with()
        mock_glob.assert_called_once_with(
            'tmp_root/boot/*/grubenv'
        )
        mock_wipe.assert_called_once_with(
            'tmp_root/boot/grub2/grubenv'
        )
        mock_which.assert_called_once_with(
            root_dir='tmp_root', filename='grub2-install'
        )
        mock_command.assert_called_once_with(
            [
                'chroot', 'tmp_root', 'grub2-install', '--skip-fs-probe',
                '--directory', '/usr/lib/grub2/i386-pc',
                '--boot-directory', '/boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(
                    Defaults.get_grub_bios_modules(multiboot=True)
                ),
                '/dev/some-device'
            ]
        )
        setup.setup_selinux_file_contexts.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Path.wipe')
    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    @patch('kiwi.bootloader.install.grub2.glob.glob')
    @patch('os.path.exists')
    def test_install_on_dasd_disk(
        self, mock_os_path_exists, mock_glob, mock_grub_path,
        mock_mount_manager, mock_command, mock_which, mock_wipe
    ):
        mock_os_path_exists.return_value = True
        self.firmware.get_partition_table_type = mock.Mock(
            return_value='dasd'
        )

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.install()
        self.bootloader.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.boot_mount.mount.assert_called_once_with()
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot', 'tmp_root', 'grub2-zipl-setup', '--keep'
                ]
            ),
            call(
                [
                    'mv',
                    'tmp_root/etc/default/zipl2grub.conf.in.orig',
                    'tmp_root/etc/default/zipl2grub.conf.in'
                ]
            ),
            call(
                [
                    'mv',
                    'tmp_root/boot/zipl/config',
                    'tmp_root/boot/zipl/config.kiwi'
                ]
            )
        ]

    @patch('kiwi.bootloader.install.grub2.Path.wipe')
    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    @patch('kiwi.bootloader.install.grub2.glob.glob')
    @patch('kiwi.bootloader.install.grub2.SystemSetup')
    def test_install_ppc_ieee1275(
        self, mock_SystemSetup, mock_glob, mock_grub_path, mock_mount_manager,
        mock_command, mock_which, mock_wipe
    ):
        setup = Mock()
        mock_SystemSetup.return_value = setup
        mock_glob.return_value = ['tmp_root/boot/grub2/grubenv']
        mock_grub_path.return_value = \
            self.root_mount.mountpoint + '/usr/lib/grub2/powerpc-ieee1275'
        self.bootloader.arch = 'ppc64'

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.install()
        self.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.boot_mount.mount.assert_called_once_with()
        mock_wipe.assert_called_once_with(
            'tmp_root/boot/grub2/grubenv'
        )
        mock_command.assert_called_once_with(
            [
                'chroot', 'tmp_root', 'grub2-install', '--skip-fs-probe',
                '--no-nvram', '--directory', '/usr/lib/grub2/powerpc-ieee1275',
                '--boot-directory', '/boot',
                '--target', 'powerpc-ieee1275',
                '--modules', ' '.join(
                    Defaults.get_grub_ofw_modules()
                ),
                self.custom_args['prep_device']
            ]
        )
        setup.setup_selinux_file_contexts.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Path.wipe')
    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    @patch('kiwi.bootloader.install.grub2.glob.glob')
    @patch('kiwi.bootloader.install.grub2.SystemSetup')
    def test_install_s390_emu(
        self, mock_SystemSetup, mock_glob, mock_grub_path, mock_mount_manager,
        mock_command, mock_which, mock_wipe
    ):
        setup = Mock()
        mock_SystemSetup.return_value = setup
        mock_glob.return_value = ['tmp_root/boot/grub2/grubenv']
        mock_grub_path.return_value = \
            self.root_mount.mountpoint + '/usr/lib/grub2/s390x-emu'
        self.bootloader.arch = 's390x'

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.install()
        self.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.boot_mount.mount.assert_called_once_with()
        mock_wipe.assert_called_once_with(
            'tmp_root/boot/grub2/grubenv'
        )
        mock_command.assert_called_once_with(
            [
                'chroot', 'tmp_root', 'grub2-install', '--skip-fs-probe',
                '--no-nvram', '--directory', '/usr/lib/grub2/s390x-emu',
                '--boot-directory', '/boot',
                '--target', 's390x-emu',
                '--modules', ' '.join(
                    Defaults.get_grub_s390_modules()
                ),
                '/dev/some-device'
            ]
        )
        setup.setup_selinux_file_contexts.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Path.wipe')
    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.Defaults.get_grub_path')
    @patch('kiwi.bootloader.install.grub2.glob.glob')
    @patch('kiwi.bootloader.install.grub2.SystemSetup')
    def test_install(
        self, mock_SystemSetup, mock_glob, mock_grub_path, mock_mount_manager,
        mock_command, mock_which, mock_wipe
    ):
        setup = Mock()
        mock_SystemSetup.return_value = setup
        mock_which.return_value = None
        mock_glob.return_value = ['tmp_root/boot/grub2/grubenv']
        mock_grub_path.return_value = \
            self.root_mount.mountpoint + '/usr/lib/grub2/i386-pc'
        self.boot_mount.device = self.root_mount.device

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect
        self.bootloader.target_removable = True

        self.bootloader.install()
        self.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.volume_mount.mount.assert_called_once_with(
            options=['subvol=@/boot/grub2']
        )
        mock_wipe.assert_called_once_with(
            'tmp_root/boot/grub2/grubenv'
        )
        mock_command.assert_called_once_with(
            [
                'chroot', 'tmp_root', 'grub2-install',
                '--removable', '--skip-fs-probe',
                '--directory', '/usr/lib/grub2/i386-pc',
                '--boot-directory', '/boot',
                '--target', 'i386-pc',
                '--modules', ' '.join(
                    Defaults.get_grub_bios_modules(multiboot=True)
                ),
                '/dev/some-device'
            ]
        )
        setup.setup_selinux_file_contexts.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('os.path.exists')
    @patch('os.access')
    def test_secure_boot_install(
        self, mock_access, mock_exists,
        mock_mount_manager, mock_command
    ):
        mock_access.return_value = True
        mock_exists.return_value = True
        self.firmware.efi_mode.return_value = 'uefi'
        self.boot_mount.device = self.root_mount.device

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.secure_boot_install()

        assert mock_command.call_args_list == [
            call([
                'chroot', 'tmp_root',
                'cp', '-p', '/usr/sbin/grub2-install',
                '/usr/sbin/grub2-install.orig'
            ]),
            call([
                'chroot', 'tmp_root',
                'cp', '/bin/true', '/usr/sbin/grub2-install'
            ]),
            call([
                'chroot', 'tmp_root', 'shim-install', '--removable',
                '/dev/some-device'
            ]),
            call([
                'chroot', 'tmp_root',
                'mv', '/usr/sbin/grub2-install.orig',
                '/usr/sbin/grub2-install'
            ])
        ]
        self.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.volume_mount.mount.assert_called_once_with(
            options=['subvol=@/boot/grub2']
        )
        self.device_mount.bind_mount.assert_called_once_with()
        self.proc_mount.bind_mount.assert_called_once_with()
        self.sysfs_mount.bind_mount.assert_called_once_with()
        self.efi_mount.mount.assert_called_once_with()

    @patch('kiwi.bootloader.install.grub2.Path.which')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    def test_secure_boot_install_no_shim_install(
        self, mock_mount_manager, mock_which
    ):
        mock_which.return_value = None
        self.firmware.efi_mode.return_value = 'uefi'

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.secure_boot_install()
        self.root_mount.mount.assert_called_once_with(
            options=['subvol=root']
        )
        self.volume_mount.mount.assert_called_once_with(
            options=['subvol=@/boot/grub2']
        )
        self.device_mount.bind_mount.assert_called_once_with()
        self.proc_mount.bind_mount.assert_called_once_with()
        self.sysfs_mount.bind_mount.assert_called_once_with()
        self.efi_mount.mount.assert_called_once_with()
        mock_which.assert_called_once_with(
            filename='shim-install', root_dir='tmp_root'
        )

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    def test_set_disk_password(self, mock_mount_manager, mock_command):
        self.boot_mount.device = self.root_mount.device

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect

        self.bootloader.root_mount = MagicMock()
        self.bootloader.root_mount.mountpoint = 'root_mountpoint'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = 'data__cryptomount__data'
            self.bootloader.set_disk_password('credentials')
            file_handle.write.assert_called_once_with(
                'data__cryptomount -p "credentials"__data'
            )

    @patch('kiwi.bootloader.install.grub2.Command.run')
    @patch('kiwi.bootloader.install.grub2.MountManager')
    @patch('kiwi.bootloader.install.grub2.ExitStack')
    def test_set_disk_password_failed_to_open_grub_config(
        self, mock_ExitStack, mock_mount_manager, mock_command
    ):
        self.boot_mount.device = self.root_mount.device

        def side_effect(device, mountpoint=None):
            return self.mount_managers.pop()

        mock_mount_manager.side_effect = side_effect
        self.bootloader.root_mount = MagicMock()
        self.bootloader.root_mount.mountpoint = 'root_mountpoint'

        with patch('builtins.open', create=True) as mock_open:
            mock_open.side_effect = IOError()
            with raises(KiwiBootLoaderDiskPasswordError):
                self.bootloader.set_disk_password('credentials')
