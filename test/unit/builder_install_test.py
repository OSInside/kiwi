from mock import patch
from mock import call

import mock
import kiwi

from collections import namedtuple

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiInstallBootImageError

from kiwi.builder.install import InstallImageBuilder


class TestInstallImageBuilder(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
        mock_machine.return_value = 'x86_64'
        self.setup = mock.Mock()
        kiwi.builder.install.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        self.firmware = mock.Mock()
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        kiwi.builder.install.FirmWare = mock.Mock(
            return_value=self.firmware
        )
        self.bootloader = mock.Mock()
        kiwi.builder.install.BootLoaderConfig = mock.Mock(
            return_value=self.bootloader
        )
        self.squashed_image = mock.Mock()
        kiwi.builder.install.FileSystemSquashFs = mock.Mock(
            return_value=self.squashed_image
        )
        self.iso_image = mock.Mock()
        self.iso_image.create_on_file.return_value = 42
        kiwi.builder.install.FileSystemIsoFs = mock.Mock(
            return_value=self.iso_image
        )
        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        kiwi.builder.install.SystemIdentifier = mock.Mock(
            return_value=self.mbrid
        )
        kiwi.builder.install.Path = mock.Mock()
        self.checksum = mock.Mock()
        kiwi.builder.install.Checksum = mock.Mock(
            return_value=self.checksum
        )
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock()
        self.kernel.get_xen_hypervisor = mock.Mock()
        self.kernel.copy_kernel = mock.Mock()
        self.kernel.copy_xen_hypervisor = mock.Mock()
        kiwi.builder.install.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.xml_state = mock.Mock()
        self.xml_state.get_initrd_system = mock.Mock(
            return_value='kiwi'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='result-image'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.build_type.get_kernelcmdline = mock.Mock(
            return_value='custom_kernel_options'
        )
        self.xml_state.get_oemconfig_oem_multipath_scan = mock.Mock(
            return_value=False
        )
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        self.boot_image_task.get_boot_names = mock.Mock(
            return_value=boot_names_type(
                kernel_name='kernel_name',
                initrd_name='initrd-kernel_version'
            )
        )

        self.install_image = InstallImageBuilder(
            self.xml_state, 'root_dir', 'target_dir', self.boot_image_task
        )

    @patch('platform.machine')
    def test_setup_ix86(self, mock_machine):
        mock_machine.return_value = 'i686'
        xml_state = mock.Mock()
        xml_state.xml_data.get_name = mock.Mock(
            return_value='result-image'
        )
        xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        xml_state.build_type.get_kernelcmdline = mock.Mock(
            return_value='custom_kernel_options'
        )
        xml_state.get_build_type_oemconfig_section = mock.Mock(
            return_value=None
        )
        install_image = InstallImageBuilder(
            xml_state, 'root_dir', 'target_dir', mock.Mock()
        )
        assert install_image.arch == 'ix86'

    @patch('kiwi.builder.install.shutil.copy')
    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Defaults.get_grub_boot_directory_name')
    def test_create_install_iso(
        self, mock_grub_dir, mock_command, mock_open,
        mock_dtemp, mock_copy
    ):
        tmpdir_name = ['temp-squashfs', 'temp_media_dir']

        def side_effect(prefix, dir):
            return tmpdir_name.pop()

        mock_dtemp.side_effect = side_effect
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.install_image.create_install_iso()

        self.setup.import_cdroot_files.assert_called_once_with('temp_media_dir')

        self.checksum.md5.assert_called_once_with(
            'temp-squashfs/result-image.md5'
        )
        mock_copy.assert_called_once_with(
            'root_dir/boot/initrd-kernel_version',
            'temp_media_dir/initrd.system_image'
        )
        assert mock_open.call_args_list == [
            call('temp_media_dir/config.isoclient', 'w'),
            call('initrd_dir/config.vmxsystem', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('IMAGE="result-image.raw"\n'),
            call('IMAGE="result-image.raw"\n')
        ]
        self.squashed_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.raw.squashfs'
        )
        assert self.bootloader.setup_install_boot_images.call_args_list == [
            call(lookup_path='initrd_dir', mbrid=None),
            call(lookup_path='root_dir', mbrid=self.mbrid)
        ]
        assert self.bootloader.setup_install_image_config.call_args_list == [
            call(mbrid=None),
            call(mbrid=self.mbrid)
        ]
        assert self.bootloader.write.call_args_list == [
            call(), call()
        ]
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid, 'initrd_kiwi_install'
        )
        self.kernel.copy_kernel.assert_called_once_with(
            'temp_media_dir/boot/x86_64/loader', '/linux'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'temp_media_dir/boot/x86_64/loader', '/xen.gz'
        )
        assert mock_command.call_args_list == [
            call([
                'cp', '-l',
                'target_dir/result-image.x86_64-1.2.3.raw',
                'temp-squashfs/result-image.raw'
            ]),
            call([
                'mv', 'target_dir/result-image.raw.squashfs', 'temp_media_dir'
            ]),
            call([
                'mv', 'initrd', 'temp_media_dir/boot/x86_64/loader/initrd'
            ])
        ]
        self.iso_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.install.iso'
        )

        tmpdir_name = ['temp-squashfs', 'temp_media_dir']
        file_mock.write.reset_mock()
        mock_open.reset_mock()
        self.install_image.initrd_system = 'dracut'

        self.install_image.create_install_iso()

        self.boot_image_task.include_file.assert_called_once_with(
            '/config.bootoptions'
        )
        assert mock_open.call_args_list == [
            call('temp_media_dir/config.isoclient', 'w'),
            call('root_dir/etc/dracut.conf.d/02-kiwi.conf', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('IMAGE="result-image.raw"\n'),
            call('hostonly="no"\n'),
            call('dracut_rescue_image="no"\n'),
            call('add_dracutmodules+=" kiwi-lib kiwi-dump "\n'),
            call('omit_dracutmodules+=" kiwi-overlay kiwi-live kiwi-repart multipath "\n')
        ]

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @raises(KiwiInstallBootImageError)
    def test_create_install_iso_no_kernel_found(
        self, mock_command, mock_open, mock_dtemp
    ):
        self.kernel.get_kernel.return_value = False
        self.install_image.create_install_iso()

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @raises(KiwiInstallBootImageError)
    def test_create_install_iso_no_hypervisor_found(
        self, mock_command, mock_open, mock_dtemp
    ):
        self.kernel.get_xen_hypervisor.return_value = False
        self.install_image.create_install_iso()

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    @raises(KiwiInstallBootImageError)
    def test_create_install_pxe_no_kernel_found(
        self, mock_compress, mock_md5, mock_command, mock_open, mock_dtemp
    ):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_kernel.return_value = False
        self.install_image.create_install_pxe_archive()

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    @patch('kiwi.builder.install.os.symlink')
    @raises(KiwiInstallBootImageError)
    def test_create_install_pxe_no_hypervisor_found(
        self, mock_symlink, mock_compress, mock_md5, mock_command,
        mock_open, mock_dtemp
    ):
        mock_dtemp.return_value = 'tmpdir'
        self.kernel.get_xen_hypervisor.return_value = False
        self.install_image.create_install_pxe_archive()

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.ArchiveTar')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    @patch('kiwi.builder.install.shutil.copy')
    @patch('kiwi.builder.install.os.symlink')
    @patch('kiwi.builder.install.os.chmod')
    def test_create_install_pxe_archive(
        self, mock_chmod, mock_symlink, mock_copy,
        mock_compress, mock_md5, mock_archive,
        mock_command, mock_open, mock_dtemp
    ):
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        mock_dtemp.return_value = 'tmpdir'

        archive = mock.Mock()
        mock_archive.return_value = archive

        checksum = mock.Mock()
        mock_md5.return_value = checksum

        compress = mock.Mock()
        mock_compress.return_value = compress

        self.install_image.create_install_pxe_archive()

        mock_compress.assert_called_once_with(
            keep_source_on_compress=True,
            source_filename='target_dir/result-image.x86_64-1.2.3.raw'
        )
        compress.xz.assert_called_once_with(None)
        assert mock_command.call_args_list[0] == call(
            ['mv', compress.compressed_filename, 'tmpdir/result-image.xz']
        )
        mock_md5.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.raw'
        )
        checksum.md5.assert_called_once_with(
            'tmpdir/result-image.md5'
        )
        assert mock_open.call_args_list == [
            call('initrd_dir/config.vmxsystem', 'w'),
            call('tmpdir/result-image.append', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('IMAGE="result-image.raw"\n'),
            call('pxe=1 custom_kernel_options\n')
        ]
        self.kernel.copy_kernel.assert_called_once_with(
            'tmpdir', '/pxeboot.kernel'
        )
        mock_symlink.assert_called_once_with(
            'pxeboot.kernel', 'tmpdir/result-image.kernel'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'tmpdir', '/pxeboot.xen.gz'
        )
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid, 'initrd_kiwi_install'
        )
        assert mock_command.call_args_list[1] == call(
            ['mv', 'initrd', 'tmpdir/pxeboot.initrd.xz']
        )
        mock_chmod.assert_called_once_with(
            'tmpdir/pxeboot.initrd.xz', 420
        )
        mock_archive.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.install.tar'
        )
        archive.create_xz_compressed.assert_called_once_with(
            'tmpdir', xz_options=None
        )

        file_mock.write.reset_mock()
        mock_chmod.reset_mock()
        mock_open.reset_mock()
        self.install_image.initrd_system = 'dracut'

        self.install_image.create_install_pxe_archive()

        self.boot_image_task.include_file.assert_called_once_with(
            '/config.bootoptions'
        )
        mock_copy.assert_called_once_with(
            'root_dir/boot/initrd-kernel_version', 'tmpdir/result-image.initrd'
        )
        assert mock_chmod.call_args_list == [
            call('tmpdir/result-image.initrd', 420),
            call('tmpdir/pxeboot.initrd.xz', 420)
        ]
        assert mock_open.call_args_list == [
            call('tmpdir/result-image.append', 'w'),
            call('root_dir/etc/dracut.conf.d/02-kiwi.conf', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call(
                ' '.join([
                    'rd.kiwi.install.pxe',
                    'rd.kiwi.install.image=http://example.com/image.xz',
                    'custom_kernel_options\n'
                ])
            ),
            call('hostonly="no"\n'),
            call('dracut_rescue_image="no"\n'),
            call('add_dracutmodules+=" kiwi-lib kiwi-dump "\n'),
            call('omit_dracutmodules+=" kiwi-overlay kiwi-live kiwi-repart multipath "\n')
        ]

    @patch('kiwi.builder.install.Path.wipe')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_destructor(self, mock_remove, mock_exists, mock_wipe):
        mock_exists.return_value = True
        self.install_image.initrd_system = 'dracut'
        self.install_image.pxe_dir = 'pxe-dir'
        self.install_image.media_dir = 'media-dir'
        self.install_image.squashed_contents = 'squashed-dir'
        self.install_image.__del__()
        mock_remove.assert_called_once_with(
            'root_dir/etc/dracut.conf.d/02-kiwi.conf'
        )
        assert mock_wipe.call_args_list == [
            call('media-dir'), call('pxe-dir'), call('squashed-dir')
        ]
        self.install_image.pxe_dir = None
        self.install_image.media_dir = None
        self.install_image.squashed_contents = None
