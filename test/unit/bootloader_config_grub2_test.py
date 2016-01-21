from nose.tools import *
from mock import patch
from mock import call

import mock

import kiwi

import nose_helper

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import *
from kiwi.bootloader_config_grub2 import BootLoaderConfigGrub2


class TestBootLoaderConfigGrub2(object):
    @patch('os.path.exists')
    @patch('kiwi.bootloader_config_grub2.FirmWare')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_firmware, mock_exists):
        mock_machine.return_value = 'x86_64'
        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        self.firmware = mock.Mock()
        self.firmware.ec2_mode = mock.Mock(
            return_value=None
        )
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        mock_firmware.return_value = self.firmware
        mock_exists.return_value = True
        description = XMLDescription(
            '../data/example_config.xml'
        )
        self.state = XMLState(
            description.load()
        )
        kiwi.bootloader_config_grub2.Path = mock.Mock()
        kiwi.bootloader_config_base.Path = mock.Mock()
        self.grub2 = mock.Mock()
        kiwi.bootloader_config_grub2.BootLoaderTemplateGrub2 = mock.Mock(
            return_value=self.grub2
        )
        kiwi.bootloader_config_grub2.Command = mock.Mock()
        self.bootloader = BootLoaderConfigGrub2(
            self.state, 'root_dir'
        )
        self.bootloader.get_hypervisor_domain = mock.Mock(
            return_value='domU'
        )
        self.bootloader.theme = None

    @raises(KiwiBootLoaderGrubPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigGrub2(mock.Mock(), 'root_dir')

    @patch('os.path.exists')
    def test_post_init_dom0(self, mock_exists):
        self.bootloader.get_hypervisor_domain.return_value = 'dom0'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is True

    @patch('__builtin__.open')
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
        call = mock_open.call_args_list[0]
        assert mock_open.call_args_list[0] == \
            call('root_dir/boot/grub2/grub.cfg', 'w')
        call = mock_open.call_args_list[1]
        assert mock_open.call_args_list[1] == \
            call('root_dir/boot/efi/EFI/BOOT//grub.cfg', 'w')
        assert file_mock.write.call_args_list == [
            call('some-data'),
            call('some-data')
        ]

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
            True, False, 'gfxterm'
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

    @patch('kiwi.defaults.Defaults.get_shim_name')
    @patch('kiwi.defaults.Defaults.get_signed_grub_name')
    @patch('kiwi.bootloader_config_grub2.Command.run')
    @raises(KiwiBootLoaderGrubSecureBootError)
    def test_setup_disk_boot_images_raises_no_shim(
        self, mock_command, mock_grub, mock_shim
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_shim.return_value = 'does-not-exist'
        mock_grub.return_value = '/'
        self.bootloader.setup_disk_boot_images('uuid', '/')

    @patch('kiwi.defaults.Defaults.get_shim_name')
    @patch('kiwi.defaults.Defaults.get_signed_grub_name')
    @patch('kiwi.bootloader_config_grub2.Command.run')
    @raises(KiwiBootLoaderGrubSecureBootError)
    def test_setup_disk_boot_images_raises_no_efigrub(
        self, mock_command, mock_grub, mock_shim
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_shim.return_value = '/'
        mock_grub.return_value = 'does-not-exist'
        self.bootloader.setup_disk_boot_images('uuid', '/')

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('os.path.exists')
    @raises(KiwiBootLoaderGrubFontError)
    def test_setup_disk_boot_images_raises_font_does_not_exist(
        self, mock_exists, mock_command
    ):
        mock_exists.return_value = False
        mock_command.side_effect = Exception
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @raises(KiwiBootLoaderGrubModulesError)
    def test_setup_disk_boot_images_raises_grub_modules_does_not_exist(
        self, mock_command
    ):
        self.bootloader.root_dir = '../data/root-dir'
        mock_command.side_effect = Exception
        self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    def test_setup_disk_boot_images_bios_plus_efi(
        self, mock_exists, mock_open, mock_command
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        mock_exists.return_value = False
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.bootloader.setup_disk_boot_images('0815')

        assert mock_open.call_args_list == [
            call('root_dir/boot/efi/EFI/BOOT/earlyboot.cfg', 'w'),
            call('root_dir/boot/grub2/earlyboot.cfg', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('search --fs-uuid --set=root 0815\n'),
            call('set prefix=($root)//grub2\n'),
            call('search --fs-uuid --set=root 0815\n'),
            call('set prefix=($root)//grub2\n')
        ]
        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'cp', '-a', 'root_dir/usr/lib/grub2/x86_64-efi',
                'root_dir/boot/grub2/x86_64-efi'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-efi',
                '-o', 'root_dir/boot/efi/EFI/BOOT/bootx64.efi',
                '-c', 'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/boot/grub2/x86_64-efi',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb', 'xfs',
                'btrfs', 'lvm', 'multiboot', 'part_gpt', 'efi_gop',
                'efi_uga', 'linuxefi'
            ]),
            call([
                'cp', '-a', 'root_dir/usr/lib/grub2/i386-pc',
                'root_dir/boot/grub2/i386-pc'
            ]),
            call([
                'grub2-mkimage', '-O', 'i386-pc',
                '-o', 'root_dir/boot/grub2/i386-pc/core.img',
                '-c', 'root_dir/boot/grub2/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/boot/grub2/i386-pc',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb',
                'xfs', 'btrfs', 'lvm', 'multiboot', 'part_gpt',
                'part_msdos', 'biosdisk', 'vga', 'vbe', 'chain',
                'boot'
            ])
        ]

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    def test_setup_disk_boot_images_ec2(
        self, mock_exists, mock_open, mock_command
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        self.firmware.ec2_mode = mock.Mock(
            return_value='ec2'
        )
        mock_exists.return_value = False
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
            'root_dir/boot/grub2/earlyboot.cfg', 'w'
        )
        assert file_mock.write.call_args_list == [
            call('search --fs-uuid --set=root 0815\n'),
            call('set prefix=($root)//grub2\n'),
        ]
        assert mock_command.call_args_list == [
            call([
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/unicode.pf2'
            ]),
            call([
                'cp', '-a', 'root_dir/usr/lib/grub2/x86_64-xen',
                'root_dir/boot/grub2/x86_64-xen'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-xen',
                '-o', 'root_dir/boot/grub2/x86_64-xen/core.img',
                '-c', 'root_dir/boot/grub2/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/boot/grub2/x86_64-xen',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb',
                'xfs', 'btrfs', 'lvm', 'multiboot', 'part_gpt',
                'part_msdos', 'biosdisk', 'vga', 'vbe', 'chain',
                'boot'
            ])
        ]

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot(
        self, mock_exists, mock_open, mock_command
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_exists.return_value = True
        self.bootloader.setup_disk_boot_images('uuid')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'cp', 'root_dir/usr/lib64/efi/shim.efi',
                'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'cp', 'root_dir/usr/lib64/efi/grub.efi',
                'root_dir/boot/efi/EFI/BOOT'
            ])

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    def test_setup_install_boot_images_efi(
        self, mock_exists, mock_open, mock_command
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value=None
        )
        mock_exists.return_value = False
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
                'cp', '-a', 'root_dir/usr/lib/grub2/x86_64-efi',
                'root_dir/boot/grub2/x86_64-efi'
            ]),
            call([
                'grub2-mkimage', '-O', 'x86_64-efi',
                '-o', 'root_dir//EFI/BOOT/bootx64.efi',
                '-c', 'root_dir//EFI/BOOT/earlyboot.cfg',
                '-p', '//grub2',
                '-d', 'root_dir/boot/grub2/x86_64-efi',
                'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                'search_label', 'search_fs_file', 'search', 'search_fs_uuid',
                'ls', 'normal', 'gzio', 'png', 'fat', 'gettext', 'font',
                'minicmd', 'gfxterm', 'gfxmenu', 'video', 'video_fb', 'xfs',
                'btrfs', 'lvm', 'multiboot', 'part_gpt', 'efi_gop',
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

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    def test_setup_install_boot_images_efi_secure_boot(
        self, mock_exists, mock_open, mock_command
    ):
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        mock_exists.return_value = True
        self.bootloader.setup_install_boot_images(self.mbrid)
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'cp', 'root_dir/usr/lib64/efi/shim.efi',
                'root_dir//EFI/BOOT/bootx64.efi'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'cp', 'root_dir/usr/lib64/efi/grub.efi',
                'root_dir//EFI/BOOT'
            ])

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_setup_install_boot_images_with_theme(
        self, mock_warn, mock_exists, mock_open, mock_command
    ):
        self.bootloader.theme = 'some-theme'
        exists_results = [False, True, False, False]

        def side_effect(arg):
            return exists_results.pop()

        mock_exists.side_effect = side_effect
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_command.call_args_list[1] == call([
            'rsync', '-zav',
            'root_dir/usr/share/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        ])

    @patch('kiwi.bootloader_config_grub2.Command.run')
    @patch('__builtin__.open')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_setup_install_boot_images_with_theme_not_existing(
        self, mock_warn, mock_exists, mock_open, mock_command
    ):
        self.bootloader.theme = 'some-theme'
        mock_exists.return_value = False
        self.bootloader.setup_install_boot_images(self.mbrid)
        assert mock_warn.called

    @patch('kiwi.bootloader_config_grub2.BootLoaderConfigGrub2.setup_install_boot_images')
    def test_setup_live_boot_images(self, mock_setup_install_boot_images):
        self.bootloader.setup_live_boot_images(self.mbrid)
        mock_setup_install_boot_images.assert_called_once_with(
            self.mbrid, None
        )
