
from mock import patch
from mock import call

import mock

import kiwi

from .test_helper import *

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import *
from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2


class TestBootLoaderConfigGrub2(object):
    @patch('kiwi.bootloader.config.grub2.FirmWare')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_theme')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_hypervisor_domain')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_domain, mock_theme, mock_firmware):
        self.os_exists = {
            'root_dir/boot/unicode.pf2': True,
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
            'root_dir/usr/lib64/efi/grub.efi': True
        }
        mock_machine.return_value = 'x86_64'
        mock_theme.return_value = None
        mock_domain.return_value = None
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
        self.bootloader = BootLoaderConfigGrub2(
            self.state, 'root_dir'
        )

    @raises(KiwiBootLoaderGrubPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigGrub2(mock.Mock(), 'root_dir')

    @patch('platform.machine')
    def test_post_init_ix86_platform(self, mock_machine):
        xml_state = mock.MagicMock()
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
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_hypervisor_domain')
    def test_post_init_dom0(self, mock_domain, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_domain.return_value = 'dom0'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is True
        assert self.bootloader.hybrid_boot is False
        assert self.bootloader.xen_guest is False

    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_hypervisor_domain')
    def test_post_init_domU(self, mock_domain, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_domain.return_value = 'domU'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is False
        assert self.bootloader.hybrid_boot is False
        assert self.bootloader.xen_guest is True

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_post_init_ec2(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.bootloader.firmware.ec2_mode.return_value = 'ec2hvm'
        self.bootloader.post_init(None)
        assert self.bootloader.xen_guest is True

    @patch_open
    @patch('os.path.exists')
    def test_write(self, mock_exists, mock_open):
        mock_exists.return_value = True
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.bootloader.config = 'some-data'
        self.bootloader.efi_boot_path = 'root_dir/boot/efi/EFI/BOOT/'
        self.bootloader.write()
        mock_open.assert_called_once_with(
            'root_dir/boot/grub2/grub.cfg', 'w'
        )
        file_mock.write.assert_called_once_with(
            'some-data'
        )

    def test_setup_live_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_multiboot_iso_template.assert_called_once_with(
            True, 'gfxterm'
        )

    def test_setup_live_image_config_standard(self):
        self.bootloader.multiboot = False
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_iso_template.assert_called_once_with(
            True, True, 'gfxterm'
        )

    def test_setup_disk_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_disk_image_config('uuid')
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
        self.bootloader.setup_disk_image_config('uuid')
        self.grub2.get_disk_template.assert_called_once_with(
            True, True, 'gfxterm'
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
        self.bootloader.setup_disk_image_config('uuid')

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
    @patch('os.path.exists')
    @patch_open
    @patch('platform.machine')
    @raises(KiwiBootLoaderGrubModulesError)
    def test_setup_disk_boot_images_raises_grub_modules_does_not_exist(
        self, mock_machine, mock_open, mock_exists, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        command_results = [False, True]

        def side_effect_mock_exists(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect_mock_exists

        def side_effect_mock_command(arg):
            if not command_results.pop():
                raise Exception

        mock_command.side_effect = side_effect_mock_command
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_xen_guest_efi_image_needs_multiboot(
        self, mock_machine, mock_exists, mock_open, mock_sync, mock_command
    ):
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
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb', 'xfs',
                'btrfs', 'lvm', 'multiboot', 'part_gpt', 'part_msdos',
                'efi_gop', 'efi_uga', 'linuxefi'
            ])
        ]

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_bios_plus_efi(
        self, mock_machine, mock_exists, mock_open, mock_sync, mock_command
    ):
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
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb', 'xfs',
                'btrfs', 'lvm', 'part_gpt', 'part_msdos', 'efi_gop',
                'efi_uga', 'linuxefi'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/usr/lib/grub2/x86_64-efi/',
            'root_dir/boot/grub2/x86_64-efi'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a']
        )

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

    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.logger.log.info')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot(
        self, mock_log, mock_machine, mock_exists
    ):
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_disk_boot_images('uuid')
        assert mock_log.called

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_install_boot_images_efi(
        self, mock_machine, mock_exists, mock_open, mock_sync, mock_command
    ):
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
        self.bootloader.setup_install_boot_images(self.mbrid)

        assert mock_open.call_args_list == [
            call('root_dir//EFI/BOOT/earlyboot.cfg', 'w')
        ]
        assert file_mock.write.call_args_list == [
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
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb', 'xfs',
                'btrfs', 'lvm', 'part_gpt', 'part_msdos', 'efi_gop',
                'efi_uga', 'linuxefi'
            ]),
            call([
                'qemu-img', 'create', 'root_dir/boot/x86_64/efi', '4M'
            ]),
            call([
                'mkdosfs', '-n', 'BOOT', 'root_dir/boot/x86_64/efi'
            ]),
            call([
                'mcopy', '-Do', '-s', '-i', 'root_dir/boot/x86_64/efi',
                'root_dir/EFI', '::'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/usr/lib/grub2/x86_64-efi/',
            'root_dir/boot/grub2/x86_64-efi'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a']
        )

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.logger.log.info')
    def test_setup_install_boot_images_efi_secure_boot(
        self, mock_log, mock_machine, mock_exists, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_command.call_args_list == [
            call([
                'qemu-img', 'create', 'root_dir/boot/x86_64/efi', '4M'
            ]),
            call([
                'mkdosfs', '-n', 'BOOT', 'root_dir/boot/x86_64/efi'
            ]),
            call([
                'mcopy', '-Do', '-s', '-i', 'root_dir/boot/x86_64/efi',
                'root_dir/EFI', '::'
            ])
        ]
        assert mock_log.called

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch('platform.machine')
    def test_setup_install_boot_images_with_theme(
        self, mock_machine, mock_warn, mock_exists, mock_open,
        mock_sync, mock_command
    ):
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['root_dir/boot/grub2/themes'] = False
        self.os_exists['root_dir/usr/share/grub2/themes/some-theme'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_sync.call_args_list[0] == call(
            'root_dir/usr/share/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        )
        assert data.sync_data.call_args_list[0] == call(options=['-z', '-a'])

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    @patch('platform.machine')
    @patch('shutil.copytree')
    @patch('shutil.copy')
    def test_setup_install_boot_images_with_legacy_grub_theme(
        self, mock_copy, mock_copytree, mock_machine, mock_warn,
        mock_exists, mock_open, mock_sync, mock_command
    ):
        data = mock.Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.os_exists['root_dir/boot/grub/themes'] = True
        self.os_exists['root_dir/boot/grub/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)

        mock_copytree.assert_called_once_with(
            'root_dir/boot/grub/themes', 'root_dir/boot/grub2/themes'
        )
        mock_copy.assert_called_once_with(
            'root_dir/boot/grub/unicode.pf2', 'root_dir/boot/grub2'
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

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_warn.called

    @patch('kiwi.bootloader.config.grub2.BootLoaderConfigGrub2.setup_install_boot_images')
    def test_setup_live_boot_images(self, mock_setup_install_boot_images):
        self.bootloader.setup_live_boot_images(self.mbrid)
        mock_setup_install_boot_images.assert_called_once_with(
            self.mbrid, None
        )
