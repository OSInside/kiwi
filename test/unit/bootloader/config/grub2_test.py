import io
import os
import logging
from collections import namedtuple
from mock import (
    patch, call, MagicMock, Mock
)
from pytest import (
    raises, fixture
)

import kiwi

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2
from kiwi.bootloader.template.grub2 import BootLoaderTemplateGrub2

from kiwi.exceptions import (
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubSecureBootError,
    KiwiTemplateError,
    KiwiBootLoaderGrubDataError,
    KiwiBootLoaderGrubFontError,
    KiwiBootLoaderGrubModulesError,
    KiwiDiskGeometryError
)


class TestBootLoaderConfigGrub2:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.bootloader.config.grub2.FirmWare')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_theme')
    @patch('platform.machine')
    def setup(
        self, mock_machine, mock_theme, mock_firmware
    ):
        self.command_type = namedtuple(
            'command_return_type', ['output']
        )
        self.find_grub = {}
        self.os_exists = {
            'root_dir/boot/grub2/fonts/unicode.pf2': True,
            'root_dir/boot/x86_64/loader/grub2/fonts/unicode.pf2': True,
            'root_dir/boot/grub2/themes/some-theme/background.png': True,
            'root_dir/usr/share/grub2': True,
            'root_dir/usr/share/grub': False,
            'root_dir/boot/grub2/themes': False,
            'root_dir/boot/grub/themes': False,
            'root_dir/boot/grub/fonts/unicode.pf2': False,
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
            ['root_dir/usr/lib64/efi/shim.efi'],
            ['root_dir/usr/lib64/efi/grub.efi'],
            ['root_dir/boot/efi/EFI/DIST/fonts']
        ]
        mock_machine.return_value = 'x86_64'
        mock_theme.return_value = None
        kiwi.bootloader.config.grub2.Path = Mock()
        kiwi.bootloader.config.base.Path = Mock()

        self.firmware = Mock()
        self.firmware.ec2_mode = Mock(
            return_value=None
        )
        self.firmware.efi_mode = Mock(
            return_value=None
        )
        mock_firmware.return_value = self.firmware

        self.mbrid = Mock()
        self.mbrid.get_id = Mock(
            return_value='0xffffffff'
        )

        grub_template = BootLoaderTemplateGrub2()
        self.grub2 = Mock()
        self.grub2.header_hybrid = grub_template.header_hybrid
        kiwi.bootloader.config.grub2.BootLoaderTemplateGrub2 = Mock(
            return_value=self.grub2
        )

        self.state = XMLState(
            XMLDescription('../data/example_config.xml').load()
        )
        self.state.is_xen_server = Mock(
            return_value=False
        )
        self.state.is_xen_guest = Mock(
            return_value=False
        )
        self.state.get_build_type_bootloader_serial_line_setup = Mock(
            return_value='serial --speed=38400'
        )
        self.state.get_build_type_bootloader_timeout_style = Mock(
            return_value='countdown'
        )
        self.bootloader = BootLoaderConfigGrub2(
            self.state, 'root_dir', None, {
                'grub_directory_name': 'grub2',
                'boot_is_crypto': True,
                'targetbase': 'rootdev'
            }
        )
        self.bootloader.cmdline = 'some-cmdline root=UUID=foo'
        self.bootloader.cmdline_failsafe = ' '.join(
            [self.bootloader.cmdline, 'failsafe-options']
        )

    @patch('platform.machine')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    def test_post_init_grub2_boot_directory(self, mock_which, mock_machine):
        xml_state = MagicMock()
        xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        mock_machine.return_value = 'i686'
        mock_which.return_value = None
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.boot_directory_name == 'grub'

    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        with raises(KiwiBootLoaderGrubPlatformError):
            BootLoaderConfigGrub2(Mock(), 'root_dir')

    @patch('kiwi.defaults.Defaults.get_shim_loader')
    @patch('kiwi.defaults.Defaults.get_signed_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_install_boot_images_raises_no_efigrub(
        self, mock_machine, mock_exists,
        mock_sync, mock_command, mock_grub, mock_shim
    ):
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        mock_shim.return_value = 'shim.efi'
        mock_grub.return_value = None
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['root_dir/usr/share/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/usr/lib/grub2/themes/some-theme'] = True
        self.os_exists['root_dir/usr/lib/grub/themes/some-theme'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        with patch('builtins.open'):
            with raises(KiwiBootLoaderGrubSecureBootError):
                self.bootloader.setup_install_boot_images(self.mbrid)

    @patch('platform.machine')
    def test_post_init_ix86_platform(self, mock_machine):
        xml_state = MagicMock()
        xml_state.get_initrd_system = Mock(
            return_value='dracut'
        )
        xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        mock_machine.return_value = 'i686'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == 'ix86'

    @patch('platform.machine')
    def test_post_init_ppc_platform(self, mock_machine):
        xml_state = MagicMock()
        xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        mock_machine.return_value = 'ppc64'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == mock_machine.return_value

    @patch('platform.machine')
    def test_post_init_s390_platform(self, mock_machine):
        xml_state = MagicMock()
        xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        mock_machine.return_value = 's390x'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == mock_machine.return_value

    @patch('platform.machine')
    def test_post_init_arm64_platform(self, mock_machine):
        xml_state = MagicMock()
        xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        mock_machine.return_value = 'arm64'
        bootloader = BootLoaderConfigGrub2(xml_state, 'root_dir')
        assert bootloader.arch == mock_machine.return_value

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_post_init_dom0(self, mock_machine, mock_exists):
        self.state.is_xen_server = Mock(
            return_value=True
        )
        self.state.is_xen_guest = Mock(
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
        self.state.is_xen_server = Mock(
            return_value=False
        )
        self.state.is_xen_guest = Mock(
            return_value=True
        )
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is False
        assert self.bootloader.hybrid_boot is False
        assert self.bootloader.xen_guest is True

    @patch.object(BootLoaderConfigGrub2, '_setup_default_grub')
    @patch.object(BootLoaderConfigGrub2, '_setup_sysconfig_bootloader')
    def test_write_meta_data(
        self, mock_setup_sysconfig_bootloader,
        mock_setup_default_grub
    ):
        self.bootloader.write_meta_data()
        mock_setup_default_grub.assert_called_once_with()
        mock_setup_sysconfig_bootloader.assert_called_once_with()

    @patch.object(BootLoaderConfigGrub2, '_setup_default_grub')
    @patch.object(BootLoaderConfigGrub2, '_setup_sysconfig_bootloader')
    @patch.object(BootLoaderConfigGrub2, '_setup_zipl2grub_conf')
    def test_write_meta_data_s390(
        self, mock_setup_zipl2grub_conf, mock_setup_sysconfig_bootloader,
        mock_setup_default_grub
    ):
        self.bootloader.arch = 's390x'
        self.bootloader.write_meta_data()
        mock_setup_default_grub.assert_called_once_with()
        mock_setup_sysconfig_bootloader.assert_called_once_with()
        mock_setup_zipl2grub_conf.assert_called_once_with()

    @patch('os.path.exists')
    @patch.object(BootLoaderConfigGrub2, '_copy_grub_config_to_efi_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_write(
        self, mock_command, mock_copy_grub_config_to_efi_path, mock_exists
    ):
        mock_exists.return_value = True
        self.bootloader.config = 'some-data'
        self.bootloader.iso_boot = True
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader.write()

            mock_open.assert_called_once_with(
                'root_dir/boot/grub2/grub.cfg', 'w'
            )
            file_handle.write.assert_called_once_with(
                'some-data'
            )
        assert mock_command.call_args_list == [
            call(
                [
                    'qemu-img', 'create', 'root_dir/boot/x86_64/efi', '15M'
                ]
            ),
            call(
                [
                    'mkdosfs', '-n', 'BOOT', 'root_dir/boot/x86_64/efi'
                ]
            ),
            call(
                [
                    'mcopy', '-Do', '-s', '-i', 'root_dir/boot/x86_64/efi',
                    'root_dir/EFI', '::'
                ]
            )
        ]

    @patch('glob.iglob')
    @patch('shutil.copy')
    @patch('kiwi.bootloader.config.grub2.Path.create')
    def test_copy_grub_config_to_efi_path(
        self, mock_Path_create, mock_shutil_copy, mock_glob
    ):
        mock_glob.return_value = []

        self.bootloader._copy_grub_config_to_efi_path(
            'root_dir', 'config_file'
        )

        mock_Path_create.assert_called_once_with(
            'root_dir/EFI/BOOT'
        )
        mock_shutil_copy.assert_called_once_with(
            'config_file', 'root_dir/EFI/BOOT/grub.cfg'
        )
        mock_shutil_copy.reset_mock()
        mock_Path_create.reset_mock()
        mock_glob.return_value = ['root_dir/EFI/fedora/shim.efi']

        self.bootloader._copy_grub_config_to_efi_path(
            'root_dir', 'config_file'
        )

        mock_Path_create.assert_called_once_with(
            'root_dir/EFI/fedora'
        )
        mock_shutil_copy.assert_called_once_with(
            'config_file', 'root_dir/EFI/fedora/grub.cfg'
        )

    @patch('shutil.copy')
    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_setup_zipl2grub_conf_512_byte_target(
        self, mock_Command_run, mock_exists, mock_shutil_copy
    ):
        path_return_values = [True, False]

        def path_exists(arg):
            return path_return_values.pop(0)

        command = Mock()
        command.output = '  2048'
        self.bootloader.target_table_type = 'msdos'
        mock_Command_run.return_value = command
        mock_exists.side_effect = path_exists
        xml_state = MagicMock()
        xml_state.get_build_type_bootloader_targettype = Mock(
            return_value='FBA'
        )
        xml_state.build_type.get_target_blocksize = Mock(
            return_value=None
        )
        self.bootloader.xml_state = xml_state
        with open('../data/etc/default/zipl2grub.conf.in') as zipl_grub:
            zipl_config = zipl_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = zipl_config
            self.bootloader._setup_zipl2grub_conf()
            assert \
                '    targettype = FBA\n' \
                '    targetbase = rootdev\n' \
                '    targetblocksize = 512\n' \
                '    targetoffset = 2048' \
                in file_handle.write.call_args[0][0]
        mock_shutil_copy.assert_called_once_with(
            'root_dir/etc/default/zipl2grub.conf.in',
            'root_dir/etc/default/zipl2grub.conf.in.orig'
        )
        path_return_values = [True, True]
        mock_shutil_copy.reset_mock()
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = zipl_config
            self.bootloader._setup_zipl2grub_conf()
        mock_shutil_copy.assert_called_once_with(
            'root_dir/etc/default/zipl2grub.conf.in.orig',
            'root_dir/etc/default/zipl2grub.conf.in'
        )

    @patch('shutil.copy')
    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_setup_zipl2grub_conf_4096_byte_target(
        self, mock_Command_run, mock_exists, mock_shutil_copy
    ):
        path_return_values = [True, False]
        command_return_values = [
            self.command_type(
                output='  blocks per track .....: 12\n'
            ),
            self.command_type(
                output=' /dev/loop01 2 6401 6400 1 Linux native\n'
            ),
            self.command_type(
                output='  cylinders ............: 10017\n'
            ),
            self.command_type(
                output='  tracks per cylinder ..: 15\n'
            ),
            self.command_type(
                output='  blocks per track .....: 12\n'
            )
        ]

        def path_exists(arg):
            return path_return_values.pop(0)

        def command_run(arg):
            return command_return_values.pop(0)

        self.bootloader.target_table_type = 'dasd'
        mock_Command_run.side_effect = command_run
        mock_exists.side_effect = path_exists
        xml_state = MagicMock()
        xml_state.get_build_type_bootloader_targettype = Mock(
            return_value='CDL'
        )
        xml_state.build_type.get_target_blocksize = Mock(
            return_value=4096
        )
        self.bootloader.xml_state = xml_state
        with open('../data/etc/default/zipl2grub.conf.in') as zipl_grub:
            zipl_config = zipl_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = zipl_config
            self.bootloader._setup_zipl2grub_conf()
            assert \
                '    targettype = CDL\n' \
                '    targetbase = rootdev\n' \
                '    targetblocksize = 4096\n' \
                '    targetoffset = 24\n' \
                '    targetgeometry = 10017,15,12' \
                in file_handle.write.call_args[0][0]

        assert mock_Command_run.call_args_list == [
            call(
                [
                    'bash', '-c',
                    'fdasd -f -p rootdev | grep "blocks per track"'
                ]
            ),
            call(
                [
                    'bash', '-c',
                    'fdasd -f -s -p rootdev | grep "^ " | '
                    'head -n 1 | tr -s " "'
                ]
            ),
            call(
                [
                    'bash', '-c', 'fdasd -f -p rootdev | grep "cylinders"'
                ]
            ),
            call(
                [
                    'bash', '-c',
                    'fdasd -f -p rootdev | grep "tracks per cylinder"'
                ]
            ),
            call(
                [
                    'bash', '-c',
                    'fdasd -f -p rootdev | grep "blocks per track"'
                ]
            )
        ]

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch.object(BootLoaderConfigGrub2, '_get_dasd_disk_geometry_element')
    def test_get_partition_start_raises(
        self, mock_get_dasd_disk_geometry_element, mock_Command_run
    ):
        self.bootloader.target_table_type = 'dasd'
        mock_Command_run.return_value = self.command_type(
            output='bogus data'
        )
        with raises(KiwiDiskGeometryError):
            self.bootloader._get_partition_start('/dev/disk')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_get_dasd_disk_geometry_element_raises(
        self, mock_Command_run
    ):
        self.bootloader.target_table_type = 'dasd'
        mock_Command_run.return_value = self.command_type(
            output='bogus data'
        )
        with raises(KiwiDiskGeometryError):
            self.bootloader._get_dasd_disk_geometry_element(
                '/dev/disk', 'tracks per cylinder'
            )

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.SysConfig')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_setup_default_grub(
        self, mock_Command_run, mock_sysconfig, mock_exists
    ):
        grep_grub_option = Mock()
        grep_grub_option.returncode = 0
        mock_Command_run.return_value = grep_grub_option
        grub_default = MagicMock()
        mock_sysconfig.return_value = grub_default
        mock_exists.return_value = True
        self.bootloader.terminal = 'serial'
        self.bootloader.theme = 'openSUSE'
        self.bootloader.displayname = 'Bob'
        self.firmware.efi_mode.return_value = 'efi'
        self.bootloader._setup_default_grub()

        mock_sysconfig.assert_called_once_with('root_dir/etc/default/grub')
        grub_default.write.assert_called_once_with()
        assert grub_default.__setitem__.call_args_list == [
            call(
                'GRUB_BACKGROUND',
                '/boot/grub2/themes/openSUSE/background.png'
            ),
            call('GRUB_CMDLINE_LINUX_DEFAULT', '"some-cmdline"'),
            call('GRUB_DISTRIBUTOR', '"Bob"'),
            call('GRUB_ENABLE_BLSCFG', 'true'),
            call('GRUB_ENABLE_CRYPTODISK', 'y'),
            call('GRUB_GFXMODE', '800x600'),
            call(
                'GRUB_SERIAL_COMMAND', '"serial --speed=38400"'
            ),
            call('GRUB_TERMINAL', '"serial"'),
            call('GRUB_THEME', '/boot/grub2/themes/openSUSE/theme.txt'),
            call('GRUB_TIMEOUT', 10),
            call('GRUB_TIMEOUT_STYLE', 'countdown'),
            call('GRUB_USE_INITRDEFI', 'true'),
            call('GRUB_USE_LINUXEFI', 'true'),
            call('SUSE_BTRFS_SNAPSHOT_BOOTING', 'true')
        ]

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.SysConfig')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    def test_setup_default_grub_empty_kernelcmdline(
        self, mock_Command_run, mock_sysconfig, mock_exists
    ):
        grep_grub_option = Mock()
        grep_grub_option.returncode = 0
        mock_Command_run.return_value = grep_grub_option
        grub_default = MagicMock()
        mock_sysconfig.return_value = grub_default
        mock_exists.return_value = True
        self.bootloader.terminal = 'serial'
        self.bootloader.theme = 'openSUSE'
        self.bootloader.displayname = 'Bob'
        self.bootloader.cmdline = 'root=UUID=foo'

        self.bootloader._setup_default_grub()

        # Must not contain GRUB_CMDLINE_LINUX_DEFAULT
        assert grub_default.__setitem__.call_args_list == [
            call(
                'GRUB_BACKGROUND',
                '/boot/grub2/themes/openSUSE/background.png'
            ),
            call('GRUB_DISTRIBUTOR', '"Bob"'),
            call('GRUB_ENABLE_BLSCFG', 'true'),
            call('GRUB_ENABLE_CRYPTODISK', 'y'),
            call('GRUB_GFXMODE', '800x600'),
            call(
                'GRUB_SERIAL_COMMAND', '"serial --speed=38400"'
            ),
            call('GRUB_TERMINAL', '"serial"'),
            call('GRUB_THEME', '/boot/grub2/themes/openSUSE/theme.txt'),
            call('GRUB_TIMEOUT', 10),
            call('GRUB_TIMEOUT_STYLE', 'countdown'),
            call('SUSE_BTRFS_SNAPSHOT_BOOTING', 'true')
        ]

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.grub2.SysConfig')
    def test_setup_sysconfig_bootloader(self, mock_sysconfig, mock_exists):
        sysconfig_bootloader = MagicMock()
        mock_sysconfig.return_value = sysconfig_bootloader
        mock_exists.return_value = True
        self.bootloader._setup_sysconfig_bootloader()
        mock_sysconfig.assert_called_once_with(
            'root_dir/etc/sysconfig/bootloader'
        )
        sysconfig_bootloader.write.assert_called_once_with()
        assert sysconfig_bootloader.__setitem__.call_args_list == [
            call('DEFAULT_APPEND', '"some-cmdline root=UUID=foo"'),
            call(
                'FAILSAFE_APPEND',
                '"some-cmdline root=UUID=foo failsafe-options"'
            ),
            call('LOADER_LOCATION', 'mbr'),
            call('LOADER_TYPE', 'grub2')
        ]
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        sysconfig_bootloader.__setitem__.reset_mock()
        self.bootloader._setup_sysconfig_bootloader()
        assert sysconfig_bootloader.__setitem__.call_args_list == [
            call('DEFAULT_APPEND', '"some-cmdline root=UUID=foo"'),
            call(
                'FAILSAFE_APPEND',
                '"some-cmdline root=UUID=foo failsafe-options"'
            ),
            call('LOADER_LOCATION', 'none'),
            call('LOADER_TYPE', 'grub2-efi'),
            call('SECURE_BOOT', 'yes')
        ]

    def test_setup_live_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_multiboot_iso_template.assert_called_once_with(
            True, 'gfxterm', None
        )

    @patch.object(BootLoaderConfigGrub2, '_copy_grub_config_to_efi_path')
    def test_setup_live_image_config_standard(
        self, mock_copy_grub_config_to_efi_path
    ):
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.bootloader.early_boot_script_efi = 'earlyboot.cfg'
        self.bootloader.multiboot = False
        self.bootloader.setup_live_image_config(self.mbrid)
        self.grub2.get_iso_template.assert_called_once_with(
            True, True, 'gfxterm', None
        )
        mock_copy_grub_config_to_efi_path.assert_called_once_with(
            'root_dir', 'earlyboot.cfg'
        )

    def test_setup_install_image_config_multiboot(self):
        self.bootloader.multiboot = True
        self.bootloader.setup_install_image_config(self.mbrid)
        self.grub2.get_multiboot_install_template.assert_called_once_with(
            True, 'gfxterm', True
        )

    @patch.object(BootLoaderConfigGrub2, '_mount_system')
    @patch.object(BootLoaderConfigGrub2, '_copy_grub_config_to_efi_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    @patch('kiwi.defaults.Defaults.get_vendor_grubenv')
    @patch('glob.iglob')
    def test_setup_disk_image_config(
        self, mock_iglob, mock_get_vendor_grubenv, mock_Path_which,
        mock_Command_run, mock_copy_grub_config_to_efi_path,
        mock_mount_system
    ):
        mock_iglob.return_value = ['some_entry.conf']
        mock_get_vendor_grubenv.return_value = 'grubenv'
        mock_Path_which.return_value = '/path/to/grub2-mkconfig'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.bootloader.root_filesystem_is_overlay = True
        self.bootloader.root_reference = 'root=overlay:UUID=ID'
        self.bootloader.root_mount = Mock()
        self.bootloader.root_mount.mountpoint = 'root_mount_point'
        self.bootloader.efi_mount = Mock()
        self.bootloader.efi_mount.mountpoint = 'efi_mount_point'
        self.bootloader.early_boot_script_efi = 'earlyboot.cfg'
        with patch('builtins.open', create=True) as mock_open:
            mock_open_grub = MagicMock(spec=io.IOBase)
            mock_open_menu = MagicMock(spec=io.IOBase)
            mock_open_grubenv = MagicMock(spec=io.IOBase)

            def open_file(filename, mode=None):
                if filename == 'root_mount_point/boot/grub2/grub.cfg':
                    return mock_open_grub.return_value
                elif filename == 'some_entry.conf':
                    return mock_open_menu.return_value
                elif filename == 'grubenv':
                    return mock_open_grubenv.return_value

            mock_open.side_effect = open_file

            file_handle_grub = \
                mock_open_grub.return_value.__enter__.return_value
            file_handle_menu = \
                mock_open_menu.return_value.__enter__.return_value
            file_handle_grubenv = \
                mock_open_grubenv.return_value.__enter__.return_value

            file_handle_grub.read.return_value = \
                'root=rootdev nomodeset console=ttyS0 console=tty0\n' \
                'root=PARTUUID=xx'
            file_handle_grubenv.read.return_value = 'root=rootdev'
            file_handle_menu.read.return_value = 'options foo bar'

            self.bootloader.setup_disk_image_config(
                boot_options={
                    'root_device': 'rootdev', 'boot_device': 'bootdev'
                }
            )
            mock_mount_system.assert_called_once_with(
                'rootdev', 'bootdev', None, None
            )
            assert mock_Command_run.call_args_list == [
                call(
                    [
                        'chroot', self.bootloader.root_mount.mountpoint,
                        'grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'
                    ]
                ),
                call(
                    [
                        'bash', '-c',
                        'cd root_mount_point/boot && rm -f boot && ln -s . boot'
                    ]
                )
            ]
            mock_copy_grub_config_to_efi_path.assert_called_once_with(
                'efi_mount_point', 'earlyboot.cfg'
            )
            assert file_handle_grub.write.call_args_list == [
                # first write of grub.cfg, adapting to linux/initrd as variables
                call(
                    'set linux=linux\n'
                    'set initrd=initrd\n'
                    'if [ "${grub_cpu}" = "x86_64" -o '
                    '"${grub_cpu}" = "i386" ];then\n'
                    '    if [ "${grub_platform}" = "efi" ]; then\n'
                    '        set linux=linuxefi\n'
                    '        set initrd=initrdefi\n'
                    '    fi\n'
                    'fi\n'
                ),
                call(
                    'root=rootdev nomodeset console=ttyS0 console=tty0'
                    '\n'
                    'root=PARTUUID=xx'
                ),
                # second write of grub.cfg, setting overlay root
                call(
                    'root=overlay:UUID=ID nomodeset console=ttyS0 console=tty0'
                    '\n'
                    'root=overlay:UUID=ID'
                )
            ]
            file_handle_grubenv.write.assert_called_once_with(
                'root=overlay:UUID=ID'
            )
            file_handle_menu.write.assert_called_once_with(
                'options some-cmdline root=UUID=foo'
            )

    @patch.object(BootLoaderConfigGrub2, '_mount_system')
    @patch.object(BootLoaderConfigGrub2, '_copy_grub_config_to_efi_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    def test_setup_disk_image_config_validate_linuxefi(
        self, mock_Path_which, mock_Command_run,
        mock_copy_grub_config_to_efi_path, mock_mount_system
    ):
        mock_Path_which.return_value = '/path/to/grub2-mkconfig'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.bootloader.root_mount = Mock()
        self.bootloader.root_mount.mountpoint = 'root_mount_point'
        self.bootloader.efi_mount = Mock()
        self.bootloader.efi_mount.mountpoint = 'efi_mount_point'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = os.linesep.join(
                [
                    '\tlinuxefi ${rel_dirname}/${basename} ...',
                    '\tlinux ${rel_dirname}/${basename} ...',
                    '\tlinux16 ${rel_dirname}/${basename} ...',
                    '\tinitrdefi ${rel_dirname}/${initrd}',
                    '\tinitrd ${rel_dirname}/${initrd}',
                    '\tinitrd16 ${rel_dirname}/${initrd}'
                ]
            )
            self.bootloader.setup_disk_image_config(
                boot_options={
                    'root_device': 'rootdev', 'boot_device': 'bootdev'
                }
            )
            assert file_handle.write.call_args_list == [
                call(
                    'set linux=linux\n'
                    'set initrd=initrd\n'
                    'if [ "${grub_cpu}" = "x86_64" -o '
                    '"${grub_cpu}" = "i386" ];then\n'
                    '    if [ "${grub_platform}" = "efi" ]; then\n'
                    '        set linux=linuxefi\n'
                    '        set initrd=initrdefi\n'
                    '    fi\n'
                    'fi\n'
                ),
                call(
                    '\t$linux ${rel_dirname}/${basename} ...\n'
                    '\t$linux ${rel_dirname}/${basename} ...\n'
                    '\t$linux ${rel_dirname}/${basename} ...\n'
                    '\t$initrd ${rel_dirname}/${initrd}\n'
                    '\t$initrd ${rel_dirname}/${initrd}\n'
                    '\t$initrd ${rel_dirname}/${initrd}'
                )
            ]

    @patch.object(BootLoaderConfigGrub2, '_copy_grub_config_to_efi_path')
    def test_setup_install_image_config_standard(
        self, mock_copy_grub_config_to_efi_path
    ):
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.bootloader.early_boot_script_efi = 'earlyboot.cfg'
        self.bootloader.multiboot = False
        self.bootloader.setup_install_image_config(self.mbrid)
        self.grub2.get_install_template.assert_called_once_with(
            True, True, 'gfxterm', True
        )
        mock_copy_grub_config_to_efi_path.assert_called_once_with(
            'root_dir', 'earlyboot.cfg'
        )

    def test_setup_iso_image_config_substitute_error(self):
        self.bootloader.multiboot = True
        template = Mock()
        template.substitute = Mock()
        template.substitute.side_effect = Exception
        self.grub2.get_multiboot_iso_template = Mock(
            return_value=template
        )
        with raises(KiwiTemplateError):
            self.bootloader.setup_live_image_config(self.mbrid)

    def test_setup_install_image_config_substitute_error(self):
        self.bootloader.multiboot = True
        template = Mock()
        template.substitute = Mock()
        template.substitute.side_effect = Exception
        self.grub2.get_multiboot_install_template = Mock(
            return_value=template
        )
        with raises(KiwiTemplateError):
            self.bootloader.setup_install_image_config(self.mbrid)

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('os.path.exists')
    def test_no_grub_installation_found(
        self, mock_exists, mock_get_boot_path, mock_command
    ):
        mock_get_boot_path.return_value = '/boot'
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = False
        self.os_exists['root_dir/usr/lib/grub2/i386-pc'] = False
        self.os_exists['root_dir/usr/share/grub/i386-pc'] = False
        self.os_exists['root_dir/usr/lib/grub/i386-pc'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        with raises(KiwiBootLoaderGrubDataError):
            self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('os.path.exists')
    @patch('kiwi.defaults.Defaults.get_grub_path')
    def test_setup_disk_boot_images_raises_font_does_not_exist(
        self, mock_get_grub_path, mock_exists, mock_get_boot_path, mock_command
    ):
        mock_get_boot_path.return_value = '/boot'
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub/unicode.pf2'] = False
        self.os_exists['root_dir/usr/lib/grub2/unicode.pf2'] = False
        self.os_exists['root_dir/usr/lib/grub/unicode.pf2'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        mock_command.side_effect = Exception
        with raises(KiwiBootLoaderGrubFontError):
            self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('platform.machine')
    @patch('os.path.exists')
    @patch.object(BootLoaderConfigGrub2, '_copy_theme_data_to_boot_directory')
    def test_setup_disk_boot_images_raises_grub_modules_does_not_exist(
        self, mock_copy_theme_data, mock_exists, mock_machine, mock_command
    ):
        mock_exists.return_value = True
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value=False
        )
        mock_command.side_effect = Exception
        with raises(KiwiBootLoaderGrubModulesError):
            self.bootloader.setup_disk_boot_images('0815')

    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_xen_guest_efi_image_needs_multiboot(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_boot_path, mock_get_unsigned_grub_loader
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_get_unsigned_grub_loader.return_value = None
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='efi'
        )
        self.bootloader.xen_guest = True
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-xen'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi/linuxefi.mod'] = \
            True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        with patch('builtins.open'):
            self.bootloader.setup_disk_boot_images('0815')

        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                    'root_dir/boot/grub2/fonts'
                ]
            ),
            call(
                [
                    'grub2-mkimage', '-O', 'x86_64-efi',
                    '-o', 'root_dir/boot/efi/EFI/BOOT/bootx64.efi',
                    '-c', 'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg',
                    '-p', '/boot/grub2',
                    '-d', 'root_dir/usr/share/grub2/x86_64-efi',
                    'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                    'search_label', 'search_fs_file', 'search',
                    'search_fs_uuid', 'ls', 'normal', 'gzio', 'png', 'fat',
                    'gettext', 'font', 'minicmd', 'gfxterm', 'gfxmenu',
                    'all_video', 'xfs', 'btrfs', 'lvm', 'luks',
                    'gcry_rijndael', 'gcry_sha256', 'gcry_sha512', 'crypto',
                    'cryptodisk', 'test', 'true', 'loadenv', 'multiboot',
                    'part_gpt', 'part_msdos', 'efi_gop', 'efi_uga', 'linuxefi'
                ]
            )
        ]

    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_bios_plus_efi(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_unsigned_grub_loader
    ):
        mock_get_unsigned_grub_loader.return_value = None
        data = Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='efi'
        )
        self.os_exists['root_dir/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi/linuxefi.mod'] = \
            True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader.setup_disk_boot_images('0815')

            mock_open.assert_called_once_with(
                'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg', 'w'
            )
            assert file_handle.write.call_args_list == [
                call('set btrfs_relative_path="yes"\n'),
                call('insmod cryptodisk\n'),
                call('insmod luks\n'),
                call('cryptomount -u 0815\n'),
                call('set root="cryptouuid/0815"\n'),
                call('search --fs-uuid --set=root 0815\n'),
                call('set prefix=($root)//grub2\n'),
                call('configfile ($root)//grub2/grub.cfg\n')
            ]
        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                    'root_dir/grub2/fonts'
                ]
            ),
            call(
                [
                    'grub2-mkimage', '-O', 'x86_64-efi',
                    '-o', 'root_dir/boot/efi/EFI/BOOT/bootx64.efi',
                    '-c', 'root_dir/boot/efi/EFI/BOOT/earlyboot.cfg',
                    '-p', '//grub2',
                    '-d', 'root_dir/usr/share/grub2/x86_64-efi',
                    'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                    'search_label', 'search_fs_file', 'search',
                    'search_fs_uuid', 'ls', 'normal', 'gzio', 'png', 'fat',
                    'gettext', 'font', 'minicmd', 'gfxterm', 'gfxmenu',
                    'all_video', 'xfs', 'btrfs', 'lvm', 'luks',
                    'gcry_rijndael', 'gcry_sha256', 'gcry_sha512', 'crypto',
                    'cryptodisk', 'test', 'true', 'loadenv', 'part_gpt',
                    'part_msdos', 'efi_gop', 'efi_uga', 'linuxefi'
                ]
            )
        ]
        assert mock_sync.call_args_list == [
            call(
                'root_dir/usr/share/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ),
            call(
                'root_dir/usr/share/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            )
        ]
        assert data.sync_data.call_args_list == [
            call(exclude=['*.module'], options=['-a']),
            call(exclude=['*.module'], options=['-a'])
        ]

        mock_get_unsigned_grub_loader.return_value = 'custom_grub_image'
        mock_command.reset_mock()

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader.setup_disk_boot_images('0815')

            assert file_handle.write.call_args_list == [
                call('set btrfs_relative_path="yes"\n'),
                call('insmod cryptodisk\n'),
                call('insmod luks\n'),
                call('cryptomount -u 0815\n'),
                call('set root="cryptouuid/0815"\n'),
                call('search --fs-uuid --set=root 0815\n'),
                call('set prefix=($root)//grub2\n'),
                call('configfile ($root)//grub2/grub.cfg\n')
            ]
            mock_open.assert_called_once_with(
                'root_dir/boot/efi/EFI/BOOT/grub.cfg', 'w'
            )

        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                    'root_dir/grub2/fonts'
                ]
            ),
            call(
                [
                    'cp', 'custom_grub_image',
                    'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
                ]
            )
        ]

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_xen_guest(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_boot_path
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value=None
        )
        self.bootloader.xen_guest = True
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-xen'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        mock_command.assert_called_once_with(
            [
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/grub2/fonts'
            ]
        )
        mock_sync.assert_called_once_with(
            'root_dir/usr/share/grub2/x86_64-xen/',
            'root_dir/boot/grub2/x86_64-xen'
        )

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_ppc(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_boot_path
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_machine.return_value = 'ppc64le'
        self.bootloader.arch = 'ppc64le'
        self.firmware.efi_mode = Mock(
            return_value=None
        )
        self.bootloader.xen_guest = False
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        mock_command.assert_called_once_with(
            [
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/grub2/fonts'
            ]
        )

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_disk_boot_images_s390(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_boot_path
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_machine.return_value = 's390x'
        self.bootloader.arch = 's390x'
        self.firmware.efi_mode = Mock(
            return_value=None
        )
        self.bootloader.xen_guest = False
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        self.bootloader.setup_disk_boot_images('0815')

        mock_command.assert_called_once_with(
            [
                'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                'root_dir/boot/grub2/fonts'
            ]
        )

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot(
        self, mock_stat, mock_chmod, mock_machine,
        mock_exists, mock_command, mock_get_boot_path
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect
        self.bootloader.setup_disk_boot_images('uuid')
        with self._caplog.at_level(logging.INFO):
            assert mock_command.call_args_list == [
                call(
                    [
                        'rsync', '-a', '--exclude', '/*.module',
                        'root_dir/usr/share/grub2/i386-pc/',
                        'root_dir/boot/grub2/i386-pc'
                    ]
                ),
                call(
                    [
                        'rsync', '-a', '--exclude', '/*.module',
                        'root_dir/usr/share/grub2/x86_64-efi/',
                        'root_dir/boot/grub2/x86_64-efi'
                    ]
                )
            ]

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('glob.iglob')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot_no_shim_install(
        self, mock_stat, mock_chmod, mock_glob, mock_machine,
        mock_exists, mock_command, mock_which, mock_get_boot_path
    ):
        # we expect the copy of shim.efi and grub.efi from the fallback
        # code if no shim_install was found for building the disk image
        mock_get_boot_path.return_value = '/boot'
        mock_which.return_value = None
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        def side_effect_glob(arg):
            return self.glob_iglob.pop()

        mock_glob.side_effect = side_effect_glob
        mock_exists.side_effect = side_effect
        with self._caplog.at_level(logging.WARNING):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value = MagicMock(spec=io.IOBase)
                file_handle = mock_open.return_value.__enter__.return_value
                self.bootloader.setup_disk_boot_images('uuid')

                assert file_handle.write.call_args_list == [
                    call('set btrfs_relative_path="yes"\n'),
                    call('insmod cryptodisk\n'),
                    call('insmod luks\n'),
                    call('cryptomount -u uuid\n'),
                    call('set root="cryptouuid/uuid"\n'),
                    call('search --fs-uuid --set=root uuid\n'),
                    call('set prefix=($root)/boot/grub2\n'),
                    call('configfile ($root)/boot/grub2/grub.cfg\n')
                ]
                mock_open.assert_called_once_with(
                    'root_dir/boot/efi/EFI/BOOT/grub.cfg', 'w'
                )

                assert mock_command.call_args_list == [
                    call(
                        [
                            'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                            'root_dir/boot/efi/EFI/DIST/fonts'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', '--exclude', '/*.module',
                            'root_dir/usr/share/grub2/i386-pc/',
                            'root_dir/boot/grub2/i386-pc'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', '--exclude', '/*.module',
                            'root_dir/usr/share/grub2/x86_64-efi/',
                            'root_dir/boot/grub2/x86_64-efi'
                        ]
                    ),
                    call(
                        [
                            'cp', 'root_dir/usr/lib64/efi/shim.efi',
                            'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
                        ]
                    ),
                    call(
                        [
                            'cp', 'root_dir/usr/lib64/efi/grub.efi',
                            'root_dir/boot/efi/EFI/BOOT'
                        ]
                    )
                ]

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Path.which')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('glob.iglob')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_disk_boot_images_bios_plus_efi_secure_boot_no_shim_at_all(
        self, mock_stat, mock_chmod, mock_glob, mock_machine,
        mock_exists, mock_command, mock_which, mock_get_boot_path
    ):
        # we expect the copy of grub.efi from the fallback
        # code if no shim was found at all
        self.glob_iglob[0] = [None]

        mock_get_boot_path.return_value = '/boot'
        mock_which.return_value = None
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        def side_effect_glob(arg):
            return self.glob_iglob.pop()

        mock_glob.side_effect = side_effect_glob
        mock_exists.side_effect = side_effect
        with self._caplog.at_level(logging.WARNING):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value = MagicMock(spec=io.IOBase)
                file_handle = mock_open.return_value.__enter__.return_value
                self.bootloader.setup_disk_boot_images('uuid')

                assert file_handle.write.call_args_list == [
                    call('set btrfs_relative_path="yes"\n'),
                    call('insmod cryptodisk\n'),
                    call('insmod luks\n'),
                    call('cryptomount -u uuid\n'),
                    call('set root="cryptouuid/uuid"\n'),
                    call('search --fs-uuid --set=root uuid\n'),
                    call('set prefix=($root)/boot/grub2\n'),
                    call('configfile ($root)/boot/grub2/grub.cfg\n')
                ]
                mock_open.assert_called_once_with(
                    'root_dir/boot/efi/EFI/BOOT/grub.cfg', 'w'
                )
                assert mock_command.call_args_list == [
                    call(
                        [
                            'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                            'root_dir/boot/efi/EFI/DIST/fonts'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', '--exclude', '/*.module',
                            'root_dir/usr/share/grub2/i386-pc/',
                            'root_dir/boot/grub2/i386-pc'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', '--exclude', '/*.module',
                            'root_dir/usr/share/grub2/x86_64-efi/',
                            'root_dir/boot/grub2/x86_64-efi'
                        ]
                    ),
                    call(
                        [
                            'cp', 'root_dir/usr/lib64/efi/grub.efi',
                            'root_dir/boot/efi/EFI/BOOT/bootx64.efi'
                        ]
                    )
                ]

    @patch('kiwi.bootloader.config.base.BootLoaderConfigBase.get_boot_path')
    @patch('kiwi.bootloader.config.grub2.Defaults.get_unsigned_grub_loader')
    @patch('kiwi.bootloader.config.grub2.Defaults.get_grub_bios_core_loader')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_install_boot_images_efi(
        self, mock_machine, mock_exists, mock_sync,
        mock_command, mock_get_grub_bios_core_loader,
        mock_get_unsigned_grub_loader, mock_get_boot_path
    ):
        mock_get_boot_path.return_value = '/boot'
        mock_get_unsigned_grub_loader.return_value = None
        mock_get_grub_bios_core_loader.return_value = None
        data = Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='efi'
        )
        self.os_exists['root_dir/boot/grub2/fonts/unicode.pf2'] = False
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi/linuxefi.mod'] = \
            True
        self.os_exists['root_dir/boot/efi/'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader.setup_install_boot_images(self.mbrid)

            assert mock_open.call_args_list == [
                call('root_dir/boot/grub2/earlyboot.cfg', 'w'),
                call('root_dir/EFI/BOOT/earlyboot.cfg', 'w')
            ]
            assert file_handle.write.call_args_list == [
                call('set btrfs_relative_path="yes"\n'),
                call('search --file --set=root /boot/0xffffffff\n'),
                call('set prefix=($root)/boot/grub2\n'),
                call('configfile ($root)/boot/grub2/grub.cfg\n'),
                call('set btrfs_relative_path="yes"\n'),
                call('search --file --set=root /boot/0xffffffff\n'),
                call('set prefix=($root)/boot/grub2\n'),
                call('configfile ($root)/boot/grub2/grub.cfg\n')
            ]

        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                    'root_dir/boot/grub2/fonts'
                ]
            ),
            call(
                [
                    'grub2-mkimage', '-O', 'i386-pc',
                    '-o', 'root_dir/usr/share/grub2/i386-pc/core.img',
                    '-c', 'root_dir/boot/grub2/earlyboot.cfg',
                    '-p', '/boot/grub2',
                    '-d', 'root_dir/usr/share/grub2/i386-pc',
                    'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                    'search_label', 'search_fs_file', 'search',
                    'search_fs_uuid', 'ls', 'normal', 'gzio', 'png', 'fat',
                    'gettext', 'font', 'minicmd', 'gfxterm', 'gfxmenu',
                    'all_video', 'xfs', 'btrfs', 'lvm', 'luks',
                    'gcry_rijndael', 'gcry_sha256', 'gcry_sha512',
                    'crypto', 'cryptodisk', 'test', 'true', 'loadenv',
                    'part_gpt', 'part_msdos', 'biosdisk', 'vga', 'vbe',
                    'chain', 'boot'
                ]
            ),
            call(
                [
                    'bash', '-c', 'cat root_dir/usr/share/grub2/i386-pc/'
                    'cdboot.img root_dir/usr/share/grub2/i386-pc/core.img > '
                    'root_dir/usr/share/grub2/i386-pc/eltorito.img'
                ]
            ),
            call(
                [
                    'grub2-mkimage', '-O', 'x86_64-efi',
                    '-o', 'root_dir/EFI/BOOT/bootx64.efi',
                    '-c', 'root_dir/EFI/BOOT/earlyboot.cfg',
                    '-p', '/boot/grub2',
                    '-d', 'root_dir/usr/share/grub2/x86_64-efi',
                    'ext2', 'iso9660', 'linux', 'echo', 'configfile',
                    'search_label', 'search_fs_file', 'search',
                    'search_fs_uuid', 'ls', 'normal', 'gzio', 'png', 'fat',
                    'gettext', 'font', 'minicmd', 'gfxterm', 'gfxmenu',
                    'all_video', 'xfs', 'btrfs', 'lvm', 'luks',
                    'gcry_rijndael', 'gcry_sha256', 'gcry_sha512',
                    'crypto', 'cryptodisk', 'test', 'true', 'loadenv',
                    'part_gpt', 'part_msdos', 'efi_gop', 'efi_uga', 'linuxefi'
                ]
            )
        ]
        assert mock_sync.call_args_list == [
            call(
                'root_dir/usr/share/grub2/i386-pc/',
                'root_dir/boot/grub2/i386-pc'
            ),
            call(
                'root_dir/usr/share/grub2/x86_64-efi/',
                'root_dir/boot/grub2/x86_64-efi'
            )
        ]
        assert data.sync_data.call_args_list == [
            call(exclude=['*.module'], options=['-a']),
            call(exclude=['*.module'], options=['-a'])
        ]

        mock_get_unsigned_grub_loader.return_value = 'custom_grub_image'
        mock_get_grub_bios_core_loader.return_value = 'custom_bios_grub_image'
        mock_command.reset_mock()

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader.setup_install_boot_images(self.mbrid)

            assert file_handle.write.call_args_list == [
                call('set btrfs_relative_path="yes"\n'),
                call('search --file --set=root /boot/0xffffffff\n'),
                call('set prefix=($root)/boot/grub2\n'),
                call('configfile ($root)/boot/grub2/grub.cfg\n')
            ]
            mock_open.assert_called_once_with(
                'root_dir/EFI/BOOT/grub.cfg', 'w'
            )

        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                    'root_dir/boot/grub2/fonts'
                ]
            ),
            call(
                [
                    'bash', '-c', 'cat root_dir/usr/share/grub2/i386-pc/'
                    'cdboot.img custom_bios_grub_image > '
                    'root_dir/usr/share/grub2/i386-pc/eltorito.img'
                ]
            ),
            call(
                [
                    'cp', 'custom_grub_image', 'root_dir/EFI/BOOT/bootx64.efi'
                ]
            )
        ]

    @patch.object(BootLoaderConfigGrub2, '_supports_bios_modules')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('glob.iglob')
    @patch('os.chmod')
    @patch('os.stat')
    def test_setup_install_boot_images_efi_secure_boot(
        self, mock_stat, mock_chmod, mock_glob, mock_machine,
        mock_exists, mock_command, mock_supports_bios_modules
    ):
        mock_supports_bios_modules.return_value = False
        self.os_exists['root_dir'] = True
        mock_machine.return_value = 'x86_64'
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        self.os_exists['root_dir/usr/share/grub2/i386-pc'] = True
        self.os_exists['root_dir/usr/share/grub2/x86_64-efi'] = True
        self.os_exists['root_dir/usr/share/grub2/unicode.pf2'] = True

        def side_effect_exists(arg):
            return self.os_exists[arg]

        def side_effect_glob(arg):
            return self.glob_iglob.pop()

        mock_glob.side_effect = side_effect_glob
        mock_exists.side_effect = side_effect_exists
        with self._caplog.at_level(logging.INFO):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value = MagicMock(spec=io.IOBase)
                file_handle = mock_open.return_value.__enter__.return_value
                self.bootloader.setup_install_boot_images(
                    self.mbrid, 'root_dir'
                )
                assert file_handle.write.call_args_list == [
                    call('set btrfs_relative_path="yes"\n'),
                    call('search --file --set=root /boot/0xffffffff\n'),
                    call('set prefix=($root)/boot/grub2\n'),
                    call('configfile ($root)/boot/grub2/grub.cfg\n')
                ]
                mock_open.assert_called_once_with(
                    'root_dir/EFI/BOOT/grub.cfg', 'w'
                )
                assert mock_command.call_args_list == [
                    call(
                        [
                            'cp', 'root_dir/usr/share/grub2/unicode.pf2',
                            'root_dir/boot/efi/EFI/DIST/fonts'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', 'root_dir/boot/efi/', 'root_dir'
                        ]
                    ),
                    call(
                        [
                            'rsync', '-a', '--exclude', '/*.module',
                            'root_dir/usr/share/grub2/x86_64-efi/',
                            'root_dir/boot/grub2/x86_64-efi'
                        ]
                    ),
                    call(
                        [
                            'cp', 'root_dir/usr/lib64/efi/shim.efi',
                            'root_dir/EFI/BOOT/bootx64.efi'
                        ]
                    ),
                    call(
                        [
                            'cp', 'root_dir/usr/lib64/efi/grub.efi',
                            'root_dir/EFI/BOOT'
                        ]
                    )
                ]

    @patch('kiwi.defaults.Defaults.get_grub_efi_font_directory')
    @patch.object(BootLoaderConfigGrub2, '_supports_bios_modules')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('glob.iglob')
    def test_setup_install_boot_images_with_theme_from_usr_share(
        self, mock_glob, mock_machine, mock_exists,
        mock_sync, mock_command, mock_supports_bios_modules,
        mock_get_grub_efi_font_directory
    ):
        mock_get_grub_efi_font_directory.return_value = None
        mock_supports_bios_modules.return_value = False
        mock_glob.return_value = [
            'root_dir/boot/grub2/themes/some-theme/background.png'
        ]
        data = Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'
        self.os_exists['lookup_path/usr/share/grub2'] = True
        self.os_exists['lookup_path/usr/lib/grub2'] = True
        self.os_exists['lookup_path/usr/share/grub2/i386-pc'] = True
        self.os_exists['lookup_path/usr/share/grub2/themes/some-theme'] = True
        self.os_exists['lookup_path/boot/grub2/themes/some-theme'] = True
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = True
        self.os_exists['lookup_path/usr/share/grub2/unicode.pf2'] = True

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        with patch('builtins.open'):
            self.bootloader.setup_install_boot_images(
                self.mbrid, lookup_path='lookup_path'
            )

        assert mock_command.call_args_list == [
            call(
                [
                    'cp',
                    'root_dir/boot/grub2/themes/some-theme/background.png',
                    'root_dir/background.png'
                ]
            ),
            call(
                [
                    'mv', 'root_dir/background.png',
                    'root_dir/boot/grub2/themes/some-theme'
                ]
            )
        ]
        assert mock_sync.call_args_list[0] == call(
            'lookup_path/usr/share/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        )
        assert data.sync_data.call_args_list[0] == call(
            options=['-a']
        )

    @patch('kiwi.defaults.Defaults.get_grub_efi_font_directory')
    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('glob.iglob')
    @patch('kiwi.defaults.Defaults.get_grub_path')
    def test_setup_install_boot_images_with_theme_from_boot(
        self, mock_get_grub_path, mock_glob, mock_machine,
        mock_exists, mock_sync, mock_command,
        mock_get_grub_efi_font_directory
    ):
        mock_get_grub_efi_font_directory.return_value = None
        mock_glob.return_value = [
            'lookup_path/boot/grub2/themes/some-theme/background.png'
        ]
        data = Mock()
        mock_sync.return_value = data
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'

        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = True
        self.os_exists['some-theme'] = False

        self.find_grub['themes/some-theme'] = 'some-theme'
        self.find_grub['i386-pc'] = 'i386-pc'
        self.find_grub['unicode.pf2'] = True

        def find_grub_data_side_effect(
            root_path, filename, raise_on_error=True
        ):
            return self.find_grub[filename]

        def side_effect(arg):
            return self.os_exists[arg]

        mock_get_grub_path.side_effect = find_grub_data_side_effect
        mock_exists.side_effect = side_effect

        with patch('builtins.open'):
            self.bootloader.setup_install_boot_images(
                self.mbrid, lookup_path='lookup_path'
            )

        assert mock_sync.call_args_list[0] == call(
            'lookup_path/boot/grub2/themes/some-theme',
            'root_dir/boot/grub2/themes'
        )
        assert data.sync_data.call_args_list[0] == call(
            options=['-a']
        )

    @patch('kiwi.bootloader.config.grub2.Command.run')
    @patch('kiwi.bootloader.config.grub2.DataSync')
    @patch('os.path.exists')
    @patch('platform.machine')
    @patch('kiwi.defaults.Defaults.get_grub_path')
    def test_setup_install_boot_images_with_theme_not_existing(
        self, mock_get_grub_path, mock_machine,
        mock_exists, mock_sync, mock_command
    ):
        mock_machine.return_value = 'x86_64'
        self.bootloader.theme = 'some-theme'

        mock_get_grub_path.return_value = 'theme-dir'

        self.os_exists['theme-dir'] = False
        self.os_exists['root_dir/boot/grub2/themes/some-theme'] = False

        def side_effect(arg):
            return self.os_exists[arg]

        mock_exists.side_effect = side_effect

        with patch('builtins.open'):
            with self._caplog.at_level(logging.WARNING):
                self.bootloader.setup_install_boot_images(self.mbrid)
                assert self.bootloader.terminal == 'console'

    @patch.object(BootLoaderConfigGrub2, 'setup_install_boot_images')
    def test_setup_live_boot_images(self, mock_setup_install_boot_images):
        self.bootloader.setup_live_boot_images(self.mbrid)
        mock_setup_install_boot_images.assert_called_once_with(
            self.mbrid, None
        )
