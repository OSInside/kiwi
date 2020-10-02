from mock import (
    patch, call
)
from pytest import raises
import mock
import sys
import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.builder.live import LiveImageBuilder
from kiwi.exceptions import KiwiLiveBootImageError


class TestLiveImageBuilder:
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'

        self.firmware = mock.Mock()
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        kiwi.builder.live.FirmWare = mock.Mock(
            return_value=self.firmware
        )

        self.setup = mock.Mock()
        kiwi.builder.live.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.filesystem_setup = mock.Mock()
        kiwi.builder.live.FileSystemSetup = mock.Mock(
            return_value=self.filesystem_setup
        )

        self.loop = mock.Mock()
        kiwi.builder.live.LoopDevice = mock.Mock(
            return_value=self.loop
        )

        self.bootloader = mock.Mock()
        kiwi.builder.live.BootLoaderConfig.new = mock.Mock(
            return_value=self.bootloader
        )

        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        kiwi.builder.live.BootImageDracut = mock.Mock(
            return_value=self.boot_image_task
        )

        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        kiwi.builder.live.SystemIdentifier = mock.Mock(
            return_value=self.mbrid
        )

        kiwi.builder.live.Path = mock.Mock()

        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock()
        self.kernel.get_xen_hypervisor = mock.Mock()
        self.kernel.copy_kernel = mock.Mock()
        self.kernel.copy_xen_hypervisor = mock.Mock()
        kiwi.builder.live.Kernel = mock.Mock(
            return_value=self.kernel
        )

        self.xml_state = mock.Mock()
        self.xml_state.get_fs_mount_option_list = mock.Mock(
            return_value=['async']
        )
        self.xml_state.get_fs_create_option_list = mock.Mock(
            return_value=['-O', 'option']
        )
        self.xml_state.build_type.get_flags = mock.Mock(
            return_value=None
        )
        self.xml_state.build_type.get_squashfscompression = mock.Mock(
            return_value='lzo'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='result-image'
        )
        self.xml_state.build_type.get_volid = mock.Mock(
            return_value='volid'
        )
        self.xml_state.build_type.get_kernelcmdline = mock.Mock(
            return_value='custom_cmdline'
        )
        self.xml_state.build_type.get_mediacheck = mock.Mock(
            return_value=True
        )
        self.xml_state.build_type.get_publisher = mock.Mock(
            return_value='Custom publisher'
        )

        self.live_image = LiveImageBuilder(
            self.xml_state, 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )

        self.result = mock.Mock()
        self.live_image.result = self.result

    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('platform.machine')
    def test_init_for_ix86_platform(self, mock_machine):
        xml_state = mock.Mock()
        xml_state.xml_data.get_name = mock.Mock(
            return_value='some-image'
        )
        xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        mock_machine.return_value = 'i686'
        live_image = LiveImageBuilder(
            xml_state, 'target_dir', 'root_dir'
        )
        assert live_image.arch == 'ix86'

    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.NamedTemporaryFile')
    @patch('kiwi.builder.live.shutil')
    @patch('kiwi.builder.live.Iso.set_media_tag')
    @patch('kiwi.builder.live.FileSystemIsoFs')
    @patch('kiwi.builder.live.FileSystem.new')
    @patch('kiwi.builder.live.SystemSize')
    @patch('kiwi.builder.live.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    def test_create_overlay_structure(
        self, mock_exists, mock_grub_dir, mock_size, mock_filesystem,
        mock_isofs, mock_tag, mock_shutil, mock_tmpfile, mock_dtemp,
        mock_setup_media_loader_directory
    ):
        tempfile = mock.Mock()
        tempfile.name = 'tmpfile'
        mock_tmpfile.return_value = tempfile
        mock_exists.return_value = True
        mock_grub_dir.return_value = 'grub2'
        tmpdir_name = ['temp-squashfs', 'temp_media_dir']
        filesystem = mock.Mock()
        mock_filesystem.return_value = filesystem

        def side_effect(prefix, dir):
            return tmpdir_name.pop()

        mock_dtemp.side_effect = side_effect

        self.live_image.live_type = 'overlay'

        iso_image = mock.Mock()
        iso_image.create_on_file.return_value = 'offset'
        mock_isofs.return_value = iso_image

        rootsize = mock.Mock()
        rootsize.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=8192
        )
        mock_size.return_value = rootsize

        self.setup.export_package_changes.return_value = '.changes'
        self.setup.export_package_verification.return_value = '.verified'
        self.setup.export_package_list.return_value = '.packages'

        self.live_image.create()

        self.setup.import_cdroot_files.assert_called_once_with('temp_media_dir')

        assert kiwi.builder.live.FileSystem.new.call_args_list == [
            call(
                device_provider=self.loop, name='ext4',
                root_dir='root_dir/',
                custom_args={
                    'mount_options': ['async'],
                    'create_options': ['-O', 'option']
                }
            ),
            call(
                device_provider=None, name='squashfs',
                root_dir='temp-squashfs',
                custom_args={'compression': 'lzo'}
            )
        ]

        filesystem.create_on_device.assert_called_once_with()
        filesystem.sync_data.assert_called_once_with(
            ['image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi']
        )
        filesystem.create_on_file.assert_called_once_with('tmpfile')

        assert mock_shutil.copy.call_args_list == [
            call('tmpfile', 'temp-squashfs/LiveOS/rootfs.img'),
            call('tmpfile', 'temp_media_dir/LiveOS/squashfs.img')
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

        kiwi.builder.live.BootLoaderConfig.new.assert_called_once_with(
            'grub2', self.xml_state, root_dir='root_dir',
            boot_dir='temp_media_dir', custom_args={
                'grub_directory_name': 'grub2'
            }
        )
        self.bootloader.setup_live_boot_images.assert_called_once_with(
            lookup_path='root_dir', mbrid=self.mbrid
        )
        mock_setup_media_loader_directory.assert_called_once_with(
            'initrd_dir', 'temp_media_dir',
            self.bootloader.get_boot_theme.return_value
        )
        self.bootloader.write_meta_data.assert_called_once_with()
        self.bootloader.setup_live_image_config.assert_called_once_with(
            mbrid=self.mbrid
        )
        self.bootloader.write.assert_called_once_with()

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
                    'preparer': 'KIWI - https://github.com/OSInside/kiwi',
                    'publisher': 'Custom publisher',
                    'volume_id': 'volid',
                    'efi_mode': 'uefi',
                    'udf': True
                }
            }, device_provider=None, root_dir='temp_media_dir'
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

        self.firmware.efi_mode.return_value = None
        tmpdir_name = ['temp-squashfs', 'temp_media_dir']
        kiwi.builder.live.BootLoaderConfig.new.reset_mock()
        self.live_image.create()
        kiwi.builder.live.BootLoaderConfig.new.assert_called_once_with(
            'isolinux', self.xml_state, root_dir='root_dir',
            boot_dir='temp_media_dir'
        )

    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    def test_create_no_kernel_found(
        self, mock_shutil, mock_dtemp,
        mock_setup_media_loader_directory
    ):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_kernel.return_value = False
        with raises(KiwiLiveBootImageError):
            self.live_image.create()

    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    def test_create_no_hypervisor_found(
        self, mock_shutil, mock_dtemp,
        mock_setup_media_loader_directory
    ):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_xen_hypervisor.return_value = False
        with raises(KiwiLiveBootImageError):
            self.live_image.create()

    @patch('kiwi.builder.live.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    @patch('os.path.exists')
    def test_create_no_initrd_found(
        self, mock_exists, mock_shutil, mock_dtemp,
        mock_setup_media_loader_directory
    ):
        mock_dtemp.return_value = 'tmpdir'
        mock_exists.return_value = False
        with raises(KiwiLiveBootImageError):
            self.live_image.create()

    @patch('kiwi.builder.live.Path.wipe')
    def test_destructor(self, mock_wipe):
        self.live_image.media_dir = 'media-dir'
        self.live_image.live_container_dir = 'container-dir'
        self.live_image.__del__()
        assert mock_wipe.call_args_list == [
            call('media-dir'),
            call('container-dir')
        ]
        self.live_image.media_dir = None
        self.live_image.live_container_dir = None
