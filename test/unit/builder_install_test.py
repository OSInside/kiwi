from mock import patch
from mock import call

import mock
import kiwi

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiInstallBootImageError

from kiwi.builder.install import InstallImageBuilder


class TestInstallImageBuilder(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
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
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='result-image'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.build_type.get_kernelcmdline = mock.Mock(
            return_value='custom_kernel_options'
        )
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        self.install_image = InstallImageBuilder(
            self.xml_state, 'target_dir', self.boot_image_task
        )
        self.install_image.machine = mock.Mock()
        self.install_image.machine.get_domain = mock.Mock(
            return_value='dom0'
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
        install_image = InstallImageBuilder(
            xml_state, 'target_dir', mock.Mock()
        )
        assert install_image.arch == 'ix86'

    @patch('kiwi.builder.install.mkdtemp')
    @patch_open
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Iso.create_hybrid')
    def test_create_install_iso(
        self, mock_hybrid, mock_command, mock_open, mock_dtemp
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

        self.checksum.md5.assert_called_once_with(
            'temp-squashfs/result-image.md5'
        )
        assert mock_open.call_args_list == [
            call('initrd_dir/config.vmxsystem', 'w'),
            call('temp_media_dir/config.isoclient', 'w')
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
            call(lookup_path='initrd_dir', mbrid=self.mbrid)
        ]
        assert self.bootloader.setup_install_boot_images.call_args_list == [
            call(lookup_path='initrd_dir', mbrid=None),
            call(lookup_path='initrd_dir', mbrid=self.mbrid)
        ]
        assert self.bootloader.setup_install_image_config.call_args_list == [
            call(mbrid=None),
            call(mbrid=self.mbrid)
        ]
        assert self.bootloader.write.call_args_list == [
            call(), call()
        ]
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid
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
        mock_hybrid.assert_called_once_with(
            42, self.mbrid, 'target_dir/result-image.x86_64-1.2.3.install.iso'
        )

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
    @raises(KiwiInstallBootImageError)
    def test_create_install_pxe_no_hypervisor_found(
        self, mock_compress, mock_md5, mock_command, mock_open, mock_dtemp
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
    def test_create_install_pxe_archive(
        self, mock_compress, mock_md5, mock_archive,
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
        compress.xz.assert_called_once_with()
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
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'tmpdir', '/pxeboot.xen.gz'
        )
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid
        )
        assert mock_command.call_args_list[1] == call(
            ['mv', 'initrd', 'tmpdir/pxeboot.initrd.xz']
        )
        mock_archive.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.install.tar'
        )
        archive.create_xz_compressed.assert_called_once_with(
            'tmpdir'
        )

    @patch('kiwi.builder.install.Path.wipe')
    def test_destructor(self, mock_wipe):
        self.install_image.pxe_dir = 'pxe-dir'
        self.install_image.media_dir = 'media-dir'
        self.install_image.squashed_contents = 'squashed-dir'
        self.install_image.__del__()
        assert mock_wipe.call_args_list == [
            call('media-dir'), call('pxe-dir'), call('squashed-dir')
        ]
        self.install_image.pxe_dir = None
        self.install_image.media_dir = None
        self.install_image.squashed_contents = None
