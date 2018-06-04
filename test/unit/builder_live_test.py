from mock import patch
from mock import call
import mock
import kiwi

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiLiveBootImageError

from kiwi.builder.live import LiveImageBuilder


class TestLiveImageBuilder(object):
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

        self.filesystem = mock.Mock()
        kiwi.builder.live.FileSystem = mock.Mock(
            return_value=self.filesystem
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
        kiwi.builder.live.BootLoaderConfig = mock.Mock(
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
            return_value='async'
        )
        self.xml_state.build_type.get_flags = mock.Mock(
            return_value=None
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

        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.result = mock.Mock()
        self.live_image.result = self.result

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

    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.NamedTemporaryFile')
    @patch('kiwi.builder.live.shutil')
    @patch('kiwi.builder.live.Iso.set_media_tag')
    @patch('kiwi.builder.live.FileSystemIsoFs')
    @patch('kiwi.builder.live.SystemSize')
    @patch('kiwi.builder.live.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch_open
    def test_create_overlay_structure(
        self, mock_open, mock_exists, mock_grub_dir, mock_size,
        mock_isofs, mock_tag, mock_shutil, mock_tmpfile, mock_dtemp
    ):
        tempfile = mock.Mock()
        tempfile.name = 'tmpfile'
        mock_tmpfile.return_value = tempfile
        mock_exists.return_value = True
        mock_grub_dir.return_value = 'grub2'
        tmpdir_name = ['temp-squashfs', 'temp_media_dir']

        def side_effect(prefix, dir):
            return tmpdir_name.pop()

        mock_dtemp.side_effect = side_effect

        mock_open.return_value = self.context_manager_mock

        self.live_image.live_type = 'overlay'

        iso_image = mock.Mock()
        iso_image.create_on_file.return_value = 'offset'
        mock_isofs.return_value = iso_image

        rootsize = mock.Mock()
        rootsize.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=8192
        )
        mock_size.return_value = rootsize

        self.setup.export_package_verification.return_value = '.verified'
        self.setup.export_package_list.return_value = '.packages'

        self.live_image.create()

        self.setup.import_cdroot_files.assert_called_once_with('temp_media_dir')

        assert kiwi.builder.live.FileSystem.call_args_list == [
            call(
                custom_args={'mount_options': 'async'},
                device_provider=self.loop, name='ext4',
                root_dir='root_dir/'
            ),
            call(
                device_provider=None, name='squashfs',
                root_dir='temp-squashfs'
            )
        ]

        self.filesystem.create_on_device.assert_called_once_with()
        self.filesystem.sync_data.assert_called_once_with(
            ['image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi']
        )
        self.filesystem.create_on_file.assert_called_once_with('tmpfile')

        assert mock_shutil.copy.call_args_list == [
            call('tmpfile', 'temp-squashfs/LiveOS/rootfs.img'),
            call('tmpfile', 'temp_media_dir/LiveOS/squashfs.img')
        ]

        self.setup.call_edit_boot_config_script.assert_called_once_with(
            boot_part_id=1, filesystem='iso:temp_media_dir',
            working_directory='root_dir'
        )

        assert call(
            'root_dir/etc/dracut.conf.d/02-livecd.conf', 'w'
        ) in mock_open.call_args_list

        assert self.file_mock.write.call_args_list == [
            call('add_dracutmodules+=" kiwi-live pollcdrom "\n'),
            call(
                'omit_dracutmodules+=" '
                'kiwi-dump kiwi-overlay kiwi-repart kiwi-lib multipath "\n'
            ),
            call('hostonly="no"\n'),
            call('dracut_rescue_image="no"\n')
        ]

        assert kiwi.builder.live.BootLoaderConfig.call_args_list[0] == call(
            'isolinux', self.xml_state, 'temp_media_dir'
        )
        assert self.bootloader.setup_live_boot_images.call_args_list[0] == call(
            lookup_path=self.live_image.boot_image.boot_root_directory,
            mbrid=None
        )
        assert self.bootloader.setup_live_image_config.call_args_list[0] == \
            call(mbrid=None)
        assert self.bootloader.write.call_args_list[0] == call()

        assert kiwi.builder.live.BootLoaderConfig.call_args_list[1] == call(
            'grub2', self.xml_state, 'temp_media_dir',
            {'grub_directory_name': 'grub2'}
        )
        assert self.bootloader.setup_live_boot_images.call_args_list[1] == call(
            lookup_path='root_dir', mbrid=self.mbrid
        )
        assert self.bootloader.setup_live_image_config.call_args_list[1] == \
            call(mbrid=self.mbrid)
        assert self.bootloader.write.call_args_list[1] == call()

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
                    'preparer': 'KIWI - http://suse.github.com/kiwi',
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

    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    @patch_open
    @raises(KiwiLiveBootImageError)
    def test_create_no_kernel_found(self, mock_open, mock_shutil, mock_dtemp):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_kernel.return_value = False
        self.live_image.create()

    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    @patch_open
    @raises(KiwiLiveBootImageError)
    def test_create_no_hypervisor_found(
        self, mock_open, mock_shutil, mock_dtemp
    ):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_xen_hypervisor.return_value = False
        self.live_image.create()

    @patch('kiwi.builder.live.mkdtemp')
    @patch('kiwi.builder.live.shutil')
    @patch('os.path.exists')
    @patch_open
    @raises(KiwiLiveBootImageError)
    def test_create_no_initrd_found(
        self, mock_open, mock_exists, mock_shutil, mock_dtemp
    ):
        mock_dtemp.return_value = 'tmpdir'
        mock_exists.return_value = False
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
