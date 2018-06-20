from mock import patch
from mock import call

import mock

import kiwi

from .test_helper import raises, patch_open

from kiwi.xml_state import XMLState

from kiwi.xml_description import XMLDescription

from kiwi.exceptions import (
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubSecureBootError,
    KiwiTemplateError,
    KiwiBootLoaderGrubDataError,
    KiwiBootLoaderGrubFontError,
    KiwiBootLoaderGrubModulesError
)

from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2


class TestBootLoaderConfigGrub2(object):
    @patch('kiwi.bootloader.config.grub2.FirmWare')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_theme')
    @patch('platform.machine')
    def setup(
        self, mock_machine, mock_theme, mock_firmware
    ):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        self.os_exists = {
            'root_dir/boot/unicode.pf2': True,
            'root_dir/boot/grub2/themes/some-theme/background.png': True,
            'root_dir/usr/share/grub2': True,
            'root_dir/usr/share/grub': False,
            'root_dir/boot/grub2/themes': False,
            'root_dir/boot/grub/themes': False,
            'root_dir/boot/grub/unicode.pf2': False,
            'root_dir/usr/lib/grub2': True,
            'root_dir/usr/lib/grub': False,
            'root_dir/boot/grub2/x86_64-efi': False,
            'root_dir/boot/grub2/i386-pc': False,
            'root_dir/boot/grub2/x86_64-xen': False,
            'root_dir/usr/lib64/efi/shim.efi': True,
            'root_dir/usr/lib64/efi/grub.efi': True,
            'root_dir/usr/lib64/efi/does-not-exist': False,
            'root_dir/boot/efi/': True
        }
        self.glob_iglob = [
            ['root_dir/usr/lib64/efi/grub.efi'],
            ['root_dir/usr/lib64/efi/shim.efi']
        ]
        mock_machine.return_value = 'x86_64'
        mock_theme.return_value = None
        kiwi.bootloader.config.grub2.Path = mock.Mock()
        kiwi.bootloader.config.base.Path = mock.Mock()

        self.firmware = mock.Mock()
        self.firmware.ec2_mode = mock.Mock(
            return_value=None
        )
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        mock_firmware.return_value = self.firmware

        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )

        self.grub2 = mock.Mock()
        kiwi.bootloader.config.grub2.BootLoaderTemplateGrub2 = mock.Mock(
            return_value=self.grub2
        )

        self.state = XMLState(
            XMLDescription('../data/example_config.xml').load()
        )
        self.state.is_xen_server = mock.Mock(
            return_value=False
        )
        self.state.is_xen_guest = mock.Mock(
            return_value=False
        )
        self.bootloader = BootLoaderConfigGrub2(
            self.state, 'root_dir', {'grub_directory_name': 'grub2'}
        )

    @patch('platform.machine')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    def test_post_init_grub2_boot_directory(self, mock_which, mock_machine):
        xml_state = mock.MagicMock()
        xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        mock_machine.return_value = 'i686'
        mock_which.return_value = None
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.boot_directory_name == 'grub'

    @raises(KiwiBootLoaderGrubPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigGrub2(mock.Mock(), 'root_dir')

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.defaults.Defaults.get_shim_loader')
    @patch('kiwi.defaults.Defaults.get_signed_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('builtins.open')
    @patch('os.path.exists')
    @patch('platform.machine')
    @raises(KiwiBootLoaderGrubSecureBootError)
    def test_setup_install_boot_images_raises_no_shim(
        self, mock_machine, mock_exists, mock_open,
        mock_sync, mock_command, mock_grub, mock_shim, mock_warn
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_shim.return_value = None
        mock_grub.return_value = 'grub.efi'
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['root_dir/usr/share/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.defaults.Defaults.get_shim_loader')
    @patch('kiwi.defaults.Defaults.get_signed_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('builtins.open')
    @patch('os.path.exists')
    @patch('platform.machine')
    @raises(KiwiBootLoaderGrubSecureBootError)
    def test_setup_install_boot_images_raises_no_efigrub(
        self, mock_machine, mock_exists, mock_open,
        mock_sync, mock_command, mock_grub, mock_shim, mock_warn
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_shim.return_value = 'shim.efi'
        mock_grub.return_value = None
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['root_dir/usr/share/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)

    @patch('platform.machine')
    def test_post_init_ix86_platform(self, mock_machine):
        xml_state = mock.MagicMock()
        xml_state.get_initrd_system = mock.Mock(
            return_value='dracut'
        )
        xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        mock_machine.return_value = 'i686'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == 'ix86'

    @patch('platform.machine')
    def test_post_init_ppc_platform(self, mock_machine):
        xml_state = mock.MagicMock()
        xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        mock_machine.return_value = 'ppc64'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == mock_machine.return_value

    @patch('platform.machine')
    def test_post_init_arm64_platform(self, mock_machine):
        xml_state = mock.MagicMock()
        xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        mock_machine.return_value = 'arm64'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == mock_machine.return_value

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_post_init_dom0(self, mock_machine, mock_exists):
        self.state.is_xen_server = mock.Mock(
            return_value=True
        )
        self.state.is_xen_guest = mock.Mock(
            return_value=False
        )
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is True
        assert self.bootloader.hybrid_boot is False
        assert self.bootloader.xen_guest is False

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_post_init_domU(self, mock_machine, mock_exists):
        self.state.is_xen_server = mock.Mock(
            return_value=False
        )
        self.state.is_xen_guest = mock.Mock(
            return_value=True
        )
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is False
        assert self.bootloader.hybrid_boot is False
        assert self.bootloader.xen_guest is True

    @patch_open
    @patch('os.path.exists')
    @patch.object(BootLoaderConfigGrub2, '_setup_default_grub')
    @patch.object(BootLoaderConfigGrub2, 'setup_sysconfig_bootloader')
    @patch('glob.iglob')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_write(
        self, mock_command, mock_glob, mock_setup_sysconfig_bootloader,
        mock_setup_default_grub, mock_exists, mock_open
    ):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.bootloader.config = 'some-data'
        self.bootloader.efi_boot_path = 'root_dir/boot/efi/EFI/BOOT/'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        self.bootloader.iso_boot = True
        mock_glob.return_value = []
        self.bootloader.write()
        assert mock_open.call_args_list == [
            call('root_dir/boot/grub2/grub.cfg', 'w'),
            call('root_dir/boot/efi/EFI/BOOT/grub.cfg', 'w')
        ]
        assert self.file_mock.write.call_args_list == [
            call('some-data'),
            call('some-data')
        ]
        assert mock_command.call_args_list == [
            call([
                'qemu-img', 'create', 'root_dir/boot/x86_64/efi', '15M'
            ]),
            call([
                'mkdosfs', '-n', 'BOOT', 'root_dir/boot/x86_64/efi'
            ]),
            call([
                'mcopy', '-Do', '-s', '-i', 'root_dir/boot/x86_64/efi',
                'root_dir/EFI', '::'
            ])
        ]
        mock_setup_default_grub.assert_called_once_with()
        mock_setup_sysconfig_bootloader.assert_called_once_with()

    @patch_open
    @patch('os.path.exists')
    @patch.object(BootLoaderConfigGrub2, '_setup_default_grub')
    @patch.object(BootLoaderConfigGrub2, 'setup_sysconfig_bootloader')
    @patch('glob.iglob')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_write_efi_for_vendor(
        self, mock_command, mock_glob, mock_setup_sysconfig_bootloader,
        mock_setup_default_grub, mock_exists, mock_open
    ):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.bootloader.config = 'some-data'
        self.bootloader.efi_boot_path = 'root_dir/boot/efi/EFI/BOOT/'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        self.bootloader.iso_boot = True
        mock_glob.return_value = ['root_dir/boot/efi/EFI/fedora/shim.efi']
        self.bootloader.write()
        assert mock_open.call_args_list == [
            call('root_dir/boot/grub2/grub.cfg', 'w'),
            call('root_dir/boot/efi/EFI/fedora/grub.cfg', 'w')
        ]

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.SysConfig')
    def test__setup_default_grub(self, mock_sysconfig, mock_exists):
        grub_default = mock.MagicMock()
        mock_sysconfig.return_value = grub_default
        mock_exists.return_value = True
        self.bootloader.cmdline = 'some-cmdline'
        self.bootloader.terminal = 'serial'
        self.bootloader.theme = 'openSUSE'
        self.firmware.efi_mode.return_value = 'efi'
        self.bootloader._setup_default_grub()

        mock_sysconfig.assert_called_once_with('root_dir/etc/default/grub')
        grub_default.write.assert_called_once_with()
        assert grub_default.__setitem__.call_args_list == [
            call('GRUB_BACKGROUND', '/boot/grub2/themes/openSUSE/background.png'),
            call('GRUB_CMDLINE_LINUX_DEFAULT', '"some-cmdline"'),
            call('GRUB_SERIAL_COMMAND', '"serial --speed=38400 --unit=0 --word=8 --parity=no --stop=1"'),
            call('GRUB_THEME', '/boot/grub2/themes/openSUSE/theme.txt'),
            call('GRUB_TIMEOUT', 10),
            call('GRUB_USE_INITRDEFI', 'true'),
            call('GRUB_USE_LINUXEFI', 'true'),
            call('SUSE_BTRFS_SNAPSHOT_BOOTING', 'true')
        ]

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.SysConfig')
    def test_setup_sysconfig_bootloader(self, mock_sysconfig, mock_exists):
        sysconfig_bootloader = mock.MagicMock()
        mock_sysconfig.return_value = sysconfig_bootloader
        mock_exists.return_value = True
        self.bootloader.cmdline = 'some-cmdline'
        self.bootloader.cmdline_failsafe = 'some-failsafe-cmdline'
        self.bootloader.setup_sysconfig_bootloader()
        mock_sysconfig.assert_called_once_with(
            'root_dir/etc/sysconfig/bootloader'
        )
        sysconfig_bootloader.write.assert_called_once_with()
        assert sysconfig_bootloader.__setitem__.call_args_list == [
            call('DEFAULT_APPEND', '"some-cmdline"'),
            call('FAILSAFE_APPEND', '"some-failsafe-cmdline"'),
            call('LOADER_LOCATION', 'mbr'),
            call('LOADER_TYPE', 'grub2')
        ]
        self.firmware.efi_mode = mock.Mock(
            return_value=True
        )
        sysconfig_bootloader.__setitem__.reset_mock()
        self.bootloader.setup_sysconfig_bootloader()
        assert sysconfig_bootloader.__setitem__.call_args_list == [
            call('DEFAULT_APPEND', '"some-cmdline"'),
            call('FAILSAFE_APPEND', '"some-failsafe-cmdline"'),
            call('LOADER_LOCATION', 'none'),
            call('LOADER_TYPE', 'grub2-efi')
        ]

    def test_setup_live_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_multiboot_iso_template.assert_called_once_with(
            True, 'gfxterm', None
        )

    def test_setup_live_image_config_standard(self):
        self.bootloader.multiboot = False
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_iso_template.assert_called_once_with(
            True, True, 'gfxterm', None
        )

    def test_setup_disk_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_disk_image_config('boot_uuid', 'root_uuid')
        self.grub2.get_multiboot_disk_template.assert_called_once_with(
            True, 'gfxterm'
        )

    def test_setup_install_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_install_image_config(self.mbrid)
        self.grub2.get_multiboot_install_template.assert_called_once_with(
            True, 'gfxterm'
        )

    def test_setup_disk_image_config_standard(self):
        self.bootloader.multiboot = False
        self.bootloader.setup_disk_image_config('boot_uuid', 'root_uuid')
        self.grub2.get_disk_template.assert_called_once_with(
            True, True, 'gfxterm'
        )

    def test_setup_disk_image_config_custom_boot_options(self):
        self.bootloader.multiboot = False
        template = mock.Mock()
        template.substitute = mock.Mock()
        self.grub2.get_disk_template = mock.Mock(
            return_value=template
        )
        self.bootloader.setup_disk_image_config(
            boot_uuid='boot_uuid', root_uuid='root_uuid', boot_options='foo'
        )
        template.substitute.assert_called_once_with(
            {
                'title': 'Bob',
                'boot_directory_name': 'grub2',
                'kernel_file': 'linux.vmx',
                'failsafe_boot_options': 'splash foo ide=nodma apm=off '
                'noresume edd=off nomodeset 3 foo',
                'default_boot': '0',
                'boot_options': 'splash foo',
                'boot_timeout': 10,
                'gfxmode': '800x600',
                'bootpath': '/',
                'search_params': '--fs-uuid --set=root boot_uuid',
                'initrd_file': 'initrd.vmx',
                'theme': None
            }
        )

    def test_setup_install_image_config_standard(self):
        self.bootloader.multiboot = False
        self.bootloader.setup_install_image_config(self.mbrid)
        self.grub2.get_install_template.assert_called_once_with(
            True, True, 'gfxterm'
        )

    @raises(KiwiTemplateError)
    def test_setup_iso_image_config_substitute_error(self):
        self.bootloader.multiboot = True
        template = mock.Mock()
        template.substitute = mock.Mock()
        template.substitute.side_effect = Exception
        self.grub2.get_multiboot_iso_template = mock.Mock(
            return_value=template
        )
        self.bootloader.setup_live_image_config(self.mbrid)

    @raises(KiwiTemplateError)
    def test_setup_disk_image_config_substitute_error(self):
        self.bootloader.multiboot = True
        template = mock.Mock()
        template.substitute = mock.Mock()
        template.substitute.side_effect = Exception
        self.grub2.get_multiboot_disk_template = mock.Mock(
            return_value=template
        )
        self.bootloader.setup_disk_image_config('boot_uuid', 'root_uuid')

    @raises(KiwiTemplateError)
    def test_setup_install_image_config_substitute_error(self):
        self.bootloader.multiboot = True
        template = mock.Mock()
        template.substitute = mock.Mock()
        template.substitute.side_effect = Exception
        self.grub2.get_multiboot_install_template = mock.Mock(
            return_value=template
        )
        self.bootloader.setup_install_image_config(self.mbrid)

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @raises(KiwiBootLoaderGrubDataError)
    def test_no_grub_installation_found(self, mock_exists, mock_command):
        self.os_exists['root_dir/boot/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2'] = False
        self.os_exists['root_dir/usr/share/grub'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @raises(KiwiBootLoaderGrubFontError)
    def test_setup_disk_boot_images_raises_font_does_not_exist(
        self, mock_exists, mock_command
    ):
        self.os_exists['root_dir/boot/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        mock_command.side_effect = Exception
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('platform.machine')
    @patch('os.path.exists')
    @patch.object(BootLoaderConfigGrub2, '_copy_theme_data_to_boot_directory')
    @raises(KiwiBootLoaderGrubModulesError)
    def test_setup_disk_boot_images_raises_grub_modules_does_not_exist(
        self, mock_copy_theme_data, mock_exists, mock_machine, mock_command
    ):
        mock_exists.return_value = True
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value=False
        )
        mock_command.side_effect = Exception
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_xen_guest_efi_image_needs_multiboot(
        self, mock_machine, mock_exists, mock_open, mock_sync,
        mock_command, mock_get_unsigned_grub_loader
    ):
        mock_get_unsigned_grub_loader.return_value = None
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        self.bootloader.xen_guest = True
        self.os_exists['root_dir/boot/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-efi',
                '-o', 'root_dir/boot/efi/EFI/BOOT/bootx64.efi',
                '-c', 'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/usr/lib/grub2/x86_64-efi',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'all_video', 'xfs',
                'btrfs', 'lvm', 'test', 'true', 'multiboot', 'part_gpt',
                'part_msdos', 'efi_gop', 'efi_uga', 'linuxefi'
            ])
        ]

    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_bios_plus_efi(
        self, mock_machine, mock_exists, mock_open, mock_sync,
        mock_command, mock_get_unsigned_grub_loader
    ):
        mock_get_unsigned_grub_loader.return_value = None
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        self.os_exists['root_dir/boot/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.bootloader.setup_disk_boot_images('0815')

        mock_open.assert_called_once_with(
            'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg', 'w'
        )
        assert file_mock.write.call_args_list == [
            call('set btrfs_relative_path="yes"\n'),
            call('search --fs-uuid --set=root 0815\n'),
            call('set prefix=($root)//grub2\n')
        ]
        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-efi',
                '-o', 'root_dir/boot/efi/EFI/BOOT/bootx64.efi',
                '-c', 'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/usr/lib/grub2/x86_64-efi',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'all_video', 'xfs',
                'btrfs', 'lvm', 'test', 'true', 'part_gpt', 'part_msdos',
                'efi_gop', 'efi_uga', 'linuxefi'
            ])
        ]
        assert mock_sync.call_args_list == [
            call(
                'root_dir/usr/lib/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ),
            call(
                'root_dir/usr/lib/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            )
        ]
        assert data.sync_data.call_args_list == [
            call(exclude=['*.module'], options=['-z', '-a']),
            call(exclude=['*.module'], options=['-z', '-a'])
        ]

        mock_get_unsigned_grub_loader.return_value = 'custom_grub_image'
        mock_command.reset_mock()
        file_mock.write.reset_mock()
        mock_open.reset_mock()
        self.bootloader.setup_disk_boot_images('0815')

        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'cp', 'custom_grub_image',
                'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
            ])
        ]
        assert file_mock.write.call_args_list == [
            call('set btrfs_relative_path="yes"\n'),
            call('search --fs-uuid --set=root 0815\n'),
            call('set prefix=($root)//grub2\n'),
            call('normal\n')
        ]
        assert mock_open.call_args_list == [
            call('root_dir/boot/efi/EFI/BOOT/grub.cfg', 'w'),
            call('root_dir/boot/efi/EFI/BOOT/grub.cfg', 'a')
        ]

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_xen_guest(
        self, mock_machine, mock_exists, mock_sync, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        self.bootloader.xen_guest = True
        self.os_exists['root_dir/boot/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        mock_command.assert_called_once_with(
            [
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]
        )
        mock_sync.assert_called_once_with(
            'root_dir/usr/lib/grub2/x86_64-xen/',
            'root_dir/boot/grub2/x86_64-xen'
        )

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_ppc(
        self, mock_machine, mock_exists, mock_sync, mock_command
    ):
        mock_machine.return_value = 'ppc64le'
        self.bootloader.arch = 'ppc64le'
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        self.bootloader.xen_guest = False
        self.os_exists['root_dir/boot/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        mock_command.assert_called_once_with(
            [
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]
        )

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.logger.log.info')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot(
        self, mock_stat, mock_chmod, mock_log, mock_machine,
        mock_exists, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_disk_boot_images('uuid')
        assert mock_command.call_args_list == [
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ]),
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi']
            )]
        assert mock_log.called

    @patch('kiwi.bootloader.config.grub2.Path.which')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.logger.log.info')
    @patch('glob.iglob')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot_no_shim_install(
        self, mock_stat, mock_chmod, mock_glob, mock_log, mock_machine,
        mock_exists, mock_command, mock_which
    ):
        # we expect the copy of shim.efi and grub.efi from the fallback
        # code if no shim_install was found for building the disk image
        mock_which.return_value = None
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )

        def side_effect(arg):
            return self.os_exists[arg]

        def side_effect_glob(arg):
            return self.glob_iglob.pop()

        mock_glob.side_effect = side_effect_glob
        mock_exists.side_effect = side_effect
        self.bootloader.setup_disk_boot_images('uuid')
        assert mock_command.call_args_list == [
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ]),
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            ]),
            call([
                'cp', 'root_dir/usr/lib64/efi/shim.efi',
                'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
            ]),
            call([
                'cp', 'root_dir/usr/lib64/efi/grub.efi',
                'root_dir/boot/efi/EFI/BOOT'
            ])
        ]
        assert mock_log.called

    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_install_boot_images_efi(
        self, mock_machine, mock_exists, mock_open, mock_sync,
        mock_command, mock_get_unsigned_grub_loader
    ):
        mock_get_unsigned_grub_loader.return_value = None
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        self.os_exists['root_dir/boot/unicode.pf2'] = False
        self.os_exists['root_dir/boot/efi/'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.bootloader.setup_install_boot_images(self.mbrid)

        assert mock_open.call_args_list == [
            call('root_dir//EFI/BOOT/earlyboot.cfg', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('set btrfs_relative_path="yes"\n'),
            call('search --file --set=root /boot/0xffffffff\n'),
            call('set prefix=($root)/boot/grub2\n')
        ]
        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-efi',
                '-o', 'root_dir//EFI/BOOT/bootx64.efi',
                '-c', 'root_dir//EFI/BOOT/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/usr/lib/grub2/x86_64-efi',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'all_video', 'xfs',
                'btrfs', 'lvm', 'test', 'true', 'part_gpt', 'part_msdos',
                'efi_gop', 'efi_uga', 'linuxefi'
            ])
        ]
        assert mock_sync.call_args_list == [
            call(
                'root_dir/usr/lib/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ),
            call(
                'root_dir/usr/lib/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            )
        ]
        assert data.sync_data.call_args_list == [
            call(exclude=['*.module'], options=['-z', '-a']),
            call(exclude=['*.module'], options=['-z', '-a'])
        ]

        mock_get_unsigned_grub_loader.return_value = 'custom_grub_image'
        mock_command.reset_mock()
        file_mock.write.reset_mock()
        mock_open.reset_mock()
        self.bootloader.setup_install_boot_images(self.mbrid)

        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'cp', 'custom_grub_image', 'root_dir//EFI/BOOT/bootx64.efi'
            ])
        ]
        assert file_mock.write.call_args_list == [
            call('set btrfs_relative_path="yes"\n'),
            call('search --file --set=root /boot/0xffffffff\n'),
            call('set prefix=($root)/boot/grub2\n'),
            call('normal\n')
        ]
        assert mock_open.call_args_list == [
            call('root_dir//EFI/BOOT/grub.cfg', 'w'),
            call('root_dir//EFI/BOOT/grub.cfg', 'a')
        ]

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.logger.log.info')
    @patch('glob.iglob')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_install_boot_images_efi_secure_boot(
        self, mock_stat, mock_chmod, mock_glob, mock_log,
        mock_machine, mock_exists, mock_command
    ):
        self.os_exists['root_dir'] = True
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )

        def side_effect_exists(arg):
            return self.os_exists[arg]

        def side_effect_glob(arg):
            return self.glob_iglob.pop()

        mock_glob.side_effect = side_effect_glob
        mock_exists.side_effect = side_effect_exists
        self.bootloader.setup_install_boot_images(self.mbrid, 'root_dir')
        assert mock_command.call_args_list == [
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ]),
            call([
                'rsync', '-a', 'root_dir/boot/efi/', 'root_dir'
            ]),
            call([
                'rsync', '-z', '-a', '--exclude', '/*.module',
                'root_dir/usr/lib/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            ]),
            call([
                'cp', 'root_dir/usr/lib64/efi/shim.efi',
                'root_dir//EFI/BOOT/bootx64.efi'
            ]),
            call([
                'cp', 'root_dir/usr/lib64/efi/grub.efi', 'root_dir//EFI/BOOT'
            ])
        ]
        assert mock_log.called

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch('platform.machine')
    @patch('glob.iglob')
    def test_setup_install_boot_images_with_theme_from_usr_share(
        self, mock_glob, mock_machine, mock_warn, mock_exists, mock_open,
        mock_sync, mock_command
    ):
        mock_glob.return_value = [
            'root_dir/boot/grub2/themes/some-theme/background.png'
        ]
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['lookup_path/usr/share/grub2'] = True
        self.os_exists['lookup_path/usr/lib/grub2'] = True
        self.os_exists['lookup_path/usr/share/grub2/themes/some-theme'] = True
        self.os_exists['lookup_path/boot/grub2/themes/some-theme'] = True
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(
            self.mbrid, lookup_path='lookup_path'
        )
        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/boot/grub2/themes/some-theme/background.png',
                'root_dir/background.png'
            ]),
            call([
                'mv', 'root_dir/background.png',
                'root_dir/boot/grub2/themes/some-theme'
            ])
        ]
        assert mock_sync.call_args_list[0] == call(
            'lookup_path/usr/share/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        )
        assert data.sync_data.call_args_list[0] == call(
            options=['-z', '-a']
        )

    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch('platform.machine')
    @patch('glob.iglob')
    def test_setup_install_boot_images_with_theme_from_boot(
        self, mock_glob, mock_machine, mock_warn, mock_exists,
        mock_open, mock_sync
    ):
        mock_glob.return_value = [
            'lookup_path/boot/grub2/themes/some-theme/background.png'
        ]
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'

        self.os_exists['lookup_path/usr/share/grub2'] = True
        self.os_exists['lookup_path/usr/lib/grub2'] = True
        self.os_exists['lookup_path/usr/share/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(
            self.mbrid, lookup_path='lookup_path'
        )
        assert mock_sync.call_args_list[0] == call(
            'lookup_path/boot/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        )
        assert data.sync_data.call_args_list[0] == call(
            options=['-z', '-a']
        )

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('builtins.open')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch('platform.machine')
    def test_setup_install_boot_images_with_theme_not_existing(
        self, mock_machine, mock_warn, mock_exists, mock_open,
        mock_sync, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['root_dir/usr/share/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_warn.called
        assert self.bootloader.terminal == 'console'

    @patch('kiwi.bootloader.config.grub2.BootLoaderConfigGrub2.setup_install_boot_images')
    def test_setup_live_boot_images(self, mock_setup_install_boot_images):
        self.bootloader.setup_live_boot_images(self.mbrid)
        mock_setup_install_boot_images.assert_called_once_with(
            self.mbrid, None
        )
