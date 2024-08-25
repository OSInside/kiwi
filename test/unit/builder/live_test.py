from unittest.mock import (
    MagicMock, patch, call, Mock
)
from pytest import raises, mark
import sys
from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2
import kiwi.builder.live

from ..test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.builder.live import LiveImageBuilder
from kiwi.exceptions import KiwiLiveBootImageError


class TestLiveImageBuilder:
    def setup(self):
        Defaults.set_platform_name('x86_64')

        self.firmware = Mock()
        self.firmware.legacy_bios_mode = Mock(
            return_value=True
        )
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        kiwi.builder.live.FirmWare = Mock(
            return_value=self.firmware
        )

        self.setup = Mock()
        kiwi.builder.live.SystemSetup = Mock(
            return_value=self.setup
        )

        self.filesystem_setup = Mock()
        kiwi.builder.live.FileSystemSetup = Mock(
            return_value=self.filesystem_setup
        )

        self.bootloader = MagicMock(spec=BootLoaderConfigGrub2)
        create_boot_loader_config_mock = Mock(
            return_value=MagicMock()
        )
        create_boot_loader_config_mock.return_value.__enter__.return_value = \
            MagicMock()
        kiwi.builder.live.create_boot_loader_config = \
            create_boot_loader_config_mock

        self.boot_image_task = Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        kiwi.builder.live.BootImageDracut = Mock(
            return_value=self.boot_image_task
        )

        self.mbrid = Mock()
        self.mbrid.get_id = Mock(
            return_value='0xffffffff'
        )
        kiwi.builder.live.SystemIdentifier = Mock(
            return_value=self.mbrid
        )

        kiwi.builder.live.Path = Mock()

        self.kernel = Mock()
        self.kernel.get_kernel = Mock()
        self.kernel.get_xen_hypervisor = Mock()
        self.kernel.copy_kernel = Mock()
        self.kernel.copy_xen_hypervisor = Mock()
        kiwi.builder.live.Kernel = Mock(
            return_value=self.kernel
        )

        self.xml_state = Mock()
        self.xml_state.get_fs_mount_option_list = Mock(
            return_value=['async']
        )
        self.xml_state.get_fs_create_option_list = Mock(
            return_value=['-O', 'option']
        )
        self.xml_state.build_type.get_application_id = Mock(
            return_value='0xffffffff'
        )
        self.xml_state.build_type.get_flags = Mock(
            return_value=None
        )
        self.xml_state.build_type.get_squashfscompression = Mock(
            return_value='lzo'
        )
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='result-image'
        )
        self.xml_state.build_type.get_volid = Mock(
            return_value='volid'
        )
        self.xml_state.build_type.get_kernelcmdline = Mock(
            return_value='custom_cmdline'
        )
        self.xml_state.build_type.get_mediacheck = Mock(
            return_value=True
        )
        self.xml_state.build_type.get_publisher = Mock(
            return_value='Custom publisher'
        )

        self.live_image = LiveImageBuilder(
            self.xml_state, 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )

        self.result = Mock()
        self.live_image.result = self.result

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def test_init_for_ix86_platform(self):
        Defaults.set_platform_name('i686')
        xml_state = Mock()
        xml_state.xml_data.get_name = Mock(
            return_value='some-image'
        )
        xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        live_image = LiveImageBuilder(
            xml_state, 'target_dir', 'root_dir'
        )
        assert live_image.arch == 'ix86'

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.live.LoopDevice')
    @patch('kiwi.builder.live.Command.run')
    @patch('kiwi.builder.live.DeviceProvider')
    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.Temporary')
    @patch('kiwi.builder.live.shutil')
    @patch('kiwi.builder.live.Iso.set_media_tag')
    @patch('kiwi.builder.live.Iso')
    @patch('kiwi.builder.live.FileSystemIsoFs')
    @patch('kiwi.builder.live.FileSystem.new')
    @patch('kiwi.builder.live.SystemSize')
    @patch('kiwi.builder.live.Defaults.get_grub_boot_directory_name')
    @patch('os.unlink')
    @patch('os.path.exists')
    @patch('os.chmod')
    def test_create_overlay_structure_boot_on_systemd_boot(
        self, mock_chmod, mock_exists, mock_unlink, mock_grub_dir, mock_size,
        mock_filesystem, mock_isofs, mock_Iso, mock_tag, mock_shutil,
        mock_Temporary, mock_setup_media_loader_directory, mock_DeviceProvider,
        mock_Command_run, mock_LoopDevice, mock_create_boot_loader_config
    ):
        boot_names = Mock()
        boot_names.initrd_name = 'dracut_initrd_name'
        self.live_image.boot_image.get_boot_names.return_value = boot_names
        self.live_image.boot_image.initrd_filename = 'kiwi_used_initrd_name'
        self.live_image.bootloader = 'systemd_boot'

        rootsize = Mock()
        rootsize.accumulate_mbyte_file_sizes = Mock(
            return_value=8192
        )
        mock_size.return_value = rootsize

        self.live_image.create()
        mock_Command_run.assert_called_once_with(
            ['mv', 'kiwi_used_initrd_name', 'root_dir/boot/dracut_initrd_name']
        )

    @mark.parametrize('xml_filesystem', [None, 'squashfs'])
    @patch('kiwi.builder.live.create_boot_loader_config')
    @patch('kiwi.builder.live.LoopDevice')
    @patch('kiwi.builder.live.DeviceProvider')
    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.Temporary')
    @patch('kiwi.builder.live.shutil')
    @patch('kiwi.builder.live.Iso.set_media_tag')
    @patch('kiwi.builder.live.Iso')
    @patch('kiwi.builder.live.FileSystemIsoFs')
    @patch('kiwi.builder.live.FileSystem.new')
    @patch('kiwi.builder.live.SystemSize')
    @patch('kiwi.builder.live.Defaults.get_grub_boot_directory_name')
    @patch('os.unlink')
    @patch('os.path.exists')
    @patch('os.chmod')
    def test_create_overlay_structure_boot_on_grub(
        self, mock_chmod, mock_exists, mock_unlink, mock_grub_dir, mock_size,
        mock_filesystem, mock_isofs, mock_Iso, mock_tag, mock_shutil,
        mock_Temporary, mock_setup_media_loader_directory, mock_DeviceProvider,
        mock_LoopDevice, mock_create_boot_loader_config, xml_filesystem
    ):
        bootloader_config = Mock()
        mock_create_boot_loader_config.return_value.__enter__.return_value = \
            bootloader_config
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        mock_exists.return_value = True
        mock_unlink.return_value = True
        mock_grub_dir.return_value = 'grub2'

        temp_squashfs = Mock()
        temp_squashfs.name = 'temp-squashfs'

        temp_media_dir = Mock()
        temp_media_dir.name = 'temp_media_dir'

        tmpdir_name = [temp_squashfs, temp_media_dir]

        filesystem = Mock()
        mock_filesystem.return_value.__enter__.return_value = filesystem

        def side_effect():
            return tmpdir_name.pop()

        mock_Temporary.return_value.new_dir.side_effect = side_effect
        mock_Temporary.return_value.new_file.return_value.name = 'kiwi-tmpfile'

        self.live_image.live_type = 'overlay'

        self.xml_state.build_type.get_filesystem = Mock(
            return_value=xml_filesystem
        )

        iso_image = Mock()
        iso_image.create_on_file.return_value = 'offset'
        mock_isofs.return_value.__enter__.return_value = iso_image

        rootsize = Mock()
        rootsize.accumulate_mbyte_file_sizes = Mock(
            return_value=8192
        )
        mock_size.return_value = rootsize

        self.setup.export_package_changes.return_value = '.changes'
        self.setup.export_package_verification.return_value = '.verified'
        self.setup.export_package_list.return_value = '.packages'

        self.firmware.bios_mode.return_value = False
        self.live_image.create()

        self.setup.import_cdroot_files.assert_called_once_with('temp_media_dir')

        if xml_filesystem == 'squashfs':
            assert kiwi.builder.live.FileSystem.new.call_args_list == [
                call(
                    device_provider=mock_DeviceProvider.return_value,
                    name='squashfs',
                    root_dir='root_dir/',
                    custom_args={'compression': 'lzo'}
                )
            ]

            filesystem.create_on_file.assert_called_once_with('kiwi-tmpfile')

            assert mock_shutil.copy.call_args_list == [
                call('kiwi-tmpfile', 'temp_media_dir/LiveOS/squashfs.img')
            ]
        else:
            assert kiwi.builder.live.FileSystem.new.call_args_list == [
                call(
                    device_provider=loop_provider, name='ext4',
                    root_dir='root_dir/',
                    custom_args={
                        'mount_options': ['async'],
                        'create_options': ['-O', 'option']
                    }
                ),
                call(
                    device_provider=mock_DeviceProvider.return_value,
                    name='squashfs',
                    root_dir='temp-squashfs',
                    custom_args={'compression': 'lzo'}
                )
            ]

            filesystem.create_on_device.assert_called_once_with()
            filesystem.sync_data.assert_called_once_with([
                'image', '.kconfig',
                'run/*', 'tmp/*', '.buildenv', 'var/cache/kiwi'
            ])

            filesystem.create_on_file.assert_called_once_with('kiwi-tmpfile')

            assert mock_shutil.copy.call_args_list == [
                call('kiwi-tmpfile', 'temp-squashfs/LiveOS/rootfs.img'),
                call('kiwi-tmpfile', 'temp_media_dir/LiveOS/squashfs.img')
            ]

        assert mock_chmod.call_args_list == [
            call('initrd', 0o644), call('kiwi-tmpfile', 0o644)
        ]

        self.setup.call_edit_boot_config_script.assert_called_once_with(
            boot_part_id=1, filesystem='iso:temp_media_dir',
            working_directory='root_dir'
        )

        assert self.boot_image_task.include_module.call_args_list == [
            call('kiwi-live'), call('pollcdrom')
        ]
        self.boot_image_task.omit_module.assert_called_once_with('multipath')
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={
                'modules': ['kiwi-live', 'pollcdrom'],
                'omit_modules': ['multipath']
            },
            config_file='root_dir/etc/dracut.conf.d/02-livecd.conf'
        )

        kiwi.builder.live.create_boot_loader_config.assert_called_once_with(
            name='grub2', xml_state=self.xml_state, root_dir='root_dir',
            boot_dir='temp_media_dir', custom_args={
                'grub_directory_name': 'grub2',
                'grub_load_command': 'configfile'
            }
        )
        bootloader_config.setup_live_boot_images.assert_called_once_with(
            lookup_path='root_dir', mbrid=self.mbrid
        )
        mock_setup_media_loader_directory.assert_called_once_with(
            'initrd_dir', 'temp_media_dir',
            bootloader_config.get_boot_theme.return_value
        )
        bootloader_config.write_meta_data.assert_called_once_with()
        bootloader_config.setup_live_image_config.assert_called_once_with(
            mbrid=self.mbrid
        )
        bootloader_config.write.assert_called_once_with()

        self.boot_image_task.prepare.assert_called_once_with()
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid
        )
        self.kernel.copy_kernel.assert_called_once_with(
            'temp_media_dir/boot/x86_64/loader', '/linux'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'temp_media_dir/boot/x86_64/loader', '/xen.gz'
        )
        mock_shutil.move.assert_called_once_with(
            'initrd', 'temp_media_dir/boot/x86_64/loader/initrd'
        )
        mock_size.assert_called_once_with(
            'temp_media_dir'
        )
        rootsize.accumulate_mbyte_file_sizes.assert_called_once_with()
        mock_isofs.assert_called_once_with(
            custom_args={
                'meta_data': {
                    'mbr_id': '0xffffffff',
                    'application_id': '0xffffffff',
                    'preparer': 'KIWI - https://github.com/OSInside/kiwi',
                    'publisher': 'Custom publisher',
                    'volume_id': 'volid',
                    'efi_mode': 'uefi',
                    'efi_loader': 'kiwi-tmpfile',
                    'udf': True,
                    'legacy_bios_mode': True
                }
            },
            device_provider=mock_DeviceProvider.return_value,
            root_dir='temp_media_dir'
        )
        iso_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.iso'
        )
        assert self.result.add.call_args_list == [
            call(
                key='live_image',
                filename='target_dir/result-image.x86_64-1.2.3.iso',
                use_for_bundle=True,
                compress=False,
                shasum=True
            ),
            call(
                key='image_packages',
                filename='.packages',
                use_for_bundle=True,
                compress=False,
                shasum=False
            ),
            call(
                key='image_changes',
                filename='.changes',
                use_for_bundle=True,
                compress=True,
                shasum=False
            ),
            call(
                key='image_verified',
                filename='.verified',
                use_for_bundle=True,
                compress=False,
                shasum=False
            )
        ]
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.Temporary')
    @patch('kiwi.builder.live.shutil')
    @patch('os.unlink')
    def test_create_no_kernel_found(
        self, mock_unlink, mock_shutil, mock_Temporary,
        mock_setup_media_loader_directory, mock_create_boot_loader_config
    ):
        self.firmware.bios_mode.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        self.kernel.get_kernel.return_value = False
        with raises(KiwiLiveBootImageError):
            self.live_image.create()

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.Temporary')
    @patch('kiwi.builder.live.shutil')
    @patch('os.unlink')
    def test_create_no_hypervisor_found(
        self, mock_unlink, mock_shutil, mock_Temporary,
        mock_setup_media_loader_directory, mock_create_boot_loader_config
    ):
        self.firmware.bios_mode.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        self.kernel.get_xen_hypervisor.return_value = False
        with raises(KiwiLiveBootImageError):
            self.live_image.create()

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.Temporary')
    @patch('kiwi.builder.live.shutil')
    @patch('os.unlink')
    @patch('os.path.exists')
    def test_create_no_initrd_found(
        self, mock_exists, mock_unlink, mock_shutil, mock_Temporary,
        mock_setup_media_loader_directory,
        mock_create_boot_loader_config
    ):
        self.firmware.bios_mode.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        mock_exists.return_value = False
        mock_unlink.return_value = True
        with raises(KiwiLiveBootImageError):
            self.live_image.create()
