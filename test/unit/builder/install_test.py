from unittest.mock import (
    MagicMock, patch, call, mock_open, ANY, Mock
)
from pytest import raises
import unittest.mock as mock
import kiwi.builder.install

from collections import namedtuple

from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2
from kiwi.defaults import Defaults
from kiwi.builder.install import InstallImageBuilder
from kiwi.exceptions import KiwiInstallBootImageError


class TestInstallImageBuilder:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
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
        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        kiwi.builder.install.SystemIdentifier = mock.Mock(
            return_value=self.mbrid
        )
        kiwi.builder.install.Path = mock.Mock()

        create_boot_loader_config_mock = mock.Mock(return_value=MagicMock())
        create_boot_loader_config_mock.return_value.__enter__.return_value = mock.Mock()
        kiwi.builder.install.create_boot_loader_config = create_boot_loader_config_mock

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
        self.xml_state.get_installmedia_initrd_modules = mock.Mock(
            return_value=['module1', 'module2']
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

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.builder.install.BootImage')
    def test_init_dracut_based(self, mock_boot_image):
        InstallImageBuilder(
            self.xml_state, 'root_dir', 'target_dir', None
        )
        mock_boot_image.new.assert_called_once_with(
            ANY, 'target_dir', 'root_dir'
        )

    def test_setup_ix86(self):
        Defaults.set_platform_name('i686')
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

    @patch('kiwi.builder.install.FileSystemIsoFs')
    @patch('kiwi.builder.install.FileSystemSquashFs')
    @patch('kiwi.builder.install.DeviceProvider')
    @patch('kiwi.builder.install.create_boot_loader_config')
    @patch('kiwi.builder.install.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.install.shutil.copy')
    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Defaults.get_grub_boot_directory_name')
    def test_create_install_iso(
        self, mock_grub_dir, mock_command, mock_Temporary, mock_copy,
        mock_setup_media_loader_directory, mock_create_boot_loader_config,
        mock_DeviceProvider, mock_FileSystemSquashFs, mock_FileSystemIsoFs
    ):
        temp_squashfs = Mock()
        temp_squashfs.new_dir.return_value.name = 'temp-squashfs'

        temp_media_dir = Mock()
        temp_media_dir.new_dir.return_value.name = 'temp_media_dir'

        temp_esp_file = Mock()
        temp_esp_file.new_file.return_value.name = 'temp_esp'

        tmp_names = [temp_esp_file, temp_squashfs, temp_media_dir]

        iso_image = mock_FileSystemIsoFs.return_value.__enter__.return_value
        iso_image.create_on_file.return_value = 42

        def side_effect(prefix, path):
            return tmp_names.pop()

        bootloader_config = mock.MagicMock(spec=BootLoaderConfigGrub2)
        mock_create_boot_loader_config.return_value.__enter__.return_value = bootloader_config
        mock_Temporary.side_effect = side_effect

        self.firmware.bios_mode.return_value = False

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.install_image.create_install_iso()

        self.setup.import_cdroot_files.assert_called_once_with('temp_media_dir')

        self.checksum.md5.assert_called_once_with(
            'temp-squashfs/result-image.md5'
        )
        mock_copy.assert_called_once_with(
            'root_dir/boot/initrd-kernel_version',
            'temp_media_dir/initrd.system_image'
        )
        assert m_open.call_args_list == [
            call('temp_media_dir/config.isoclient', 'w'),
            call('initrd_dir/config.vmxsystem', 'w')
        ]
        assert m_open.return_value.write.call_args_list == [
            call('IMAGE="result-image.raw"\n'),
            call('IMAGE="result-image.raw"\n')
        ]
        kiwi.builder.install.FileSystemSquashFs.assert_called_once_with(
            custom_args={'compression': mock.ANY},
            device_provider=mock_DeviceProvider.return_value,
            root_dir='temp-squashfs'
        )
        squashed_image = mock_FileSystemSquashFs \
            .return_value.__enter__.return_value
        squashed_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.raw.squashfs'
        )
        mock_create_boot_loader_config.assert_called_once_with(
            name='grub2', xml_state=self.xml_state, root_dir='root_dir',
            boot_dir='temp_media_dir', custom_args={
                'grub_directory_name': mock_grub_dir.return_value,
                'grub_load_command': 'configfile'
            }
        )
        bootloader_config.setup_install_boot_images.assert_called_once_with(
            lookup_path='initrd_dir', mbrid=self.mbrid
        )
        mock_setup_media_loader_directory.assert_called_once_with(
            'initrd_dir', 'temp_media_dir',
            bootloader_config.get_boot_theme.return_value
        )
        bootloader_config.write_meta_data.assert_called_once_with()
        bootloader_config.setup_install_image_config.assert_called_once_with(
            mbrid=self.mbrid
        )
        bootloader_config.write.assert_called_once_with()
        bootloader_config._create_embedded_fat_efi_image.assert_called_once_with(
            'temp_esp'
        )
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid, 'initrd_kiwi_install', install_initrd=True
        )
        self.boot_image_task.cleanup.assert_called_once_with()
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
        iso_image.create_on_file.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.install.iso'
        )

        tmp_names = [temp_esp_file, temp_squashfs, temp_media_dir]
        self.install_image.initrd_system = 'dracut'

        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.install_image.create_install_iso()

        self.boot_image_task.include_module.assert_any_call('kiwi-dump')
        self.boot_image_task.include_module.assert_any_call('kiwi-dump-reboot')
        assert self.boot_image_task.omit_module.call_args_list == [
            call('multipath'), call('module1'), call('module2')
        ]
        self.boot_image_task.set_static_modules.assert_called_once_with(
            ['module1', 'module2']
        )

        self.boot_image_task.include_file.assert_called_once_with(
            '/config.bootoptions'
        )
        assert m_open.call_args_list == [
            call('temp_media_dir/config.isoclient', 'w'),
        ]
        assert m_open.return_value.write.call_args_list == [
            call('IMAGE="result-image.raw"\n')
        ]

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.install.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    def test_create_install_iso_no_kernel_found(
        self, mock_command, mock_Temporary, mock_setup_media_loader_directory,
        mock_create_boot_loader_config
    ):
        self.firmware.bios_mode.return_value = False
        self.kernel.get_kernel.return_value = False
        with patch('builtins.open'):
            with raises(KiwiInstallBootImageError):
                self.install_image.create_install_iso()

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.install.IsoToolsBase.setup_media_loader_directory')
    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    def test_create_install_iso_no_hypervisor_found(
        self, mock_command, mock_Temporary, mock_setup_media_loader_directory,
        mock_create_boot_loader_config
    ):
        self.firmware.bios_mode.return_value = False
        self.kernel.get_xen_hypervisor.return_value = False
        with patch('builtins.open'):
            with raises(KiwiInstallBootImageError):
                self.install_image.create_install_iso()

    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    def test_create_install_pxe_no_kernel_found(
        self, mock_compress, mock_md5, mock_command, mock_Temporary
    ):
        self.firmware.bios_mode.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        self.kernel.get_kernel.return_value = False
        with patch('builtins.open'):
            with raises(KiwiInstallBootImageError):
                self.install_image.create_install_pxe_archive()

    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    @patch('kiwi.builder.install.os.symlink')
    def test_create_install_pxe_no_hypervisor_found(
        self, mock_symlink, mock_compress, mock_md5, mock_command,
        mock_Temporary
    ):
        self.firmware.bios_mode.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        self.kernel.get_xen_hypervisor.return_value = False
        with patch('builtins.open'):
            with raises(KiwiInstallBootImageError):
                self.install_image.create_install_pxe_archive()

    @patch('kiwi.builder.install.Temporary')
    @patch('kiwi.builder.install.Command.run')
    @patch('kiwi.builder.install.ArchiveTar')
    @patch('kiwi.builder.install.Checksum')
    @patch('kiwi.builder.install.Compress')
    @patch('kiwi.builder.install.shutil.copy')
    @patch('kiwi.builder.install.os.symlink')
    @patch('kiwi.builder.install.os.chmod')
    def test_create_install_pxe_archive(
        self, mock_chmod, mock_symlink, mock_copy, mock_compress,
        mock_md5, mock_archive, mock_command, mock_Temporary
    ):
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'

        archive = mock.Mock()
        mock_archive.return_value = archive

        checksum = mock.Mock()
        mock_md5.return_value = checksum

        compress = mock.Mock()
        src = 'target_dir/result-image.x86_64-1.2.3.raw'
        compress.xz.return_value = src
        mock_compress.return_value = compress

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.install_image.create_install_pxe_archive()

        mock_compress.assert_called_once_with(
            keep_source_on_compress=True, source_filename=src
        )
        compress.xz.assert_called_once_with(None)
        assert mock_command.call_args_list[0] == call(
            ['mv', src, 'tmpdir/result-image.x86_64-1.2.3.xz']
        )
        mock_md5.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.raw'
        )
        checksum.md5.assert_called_once_with(
            'tmpdir/result-image.x86_64-1.2.3.md5'
        )
        assert m_open.call_args_list == [
            call('initrd_dir/config.vmxsystem', 'w'),
            call('tmpdir/result-image.x86_64-1.2.3.append', 'w')
        ]
        assert m_open.return_value.write.call_args_list == [
            call('IMAGE="result-image.raw"\n'),
            call('pxe=1 custom_kernel_options\n')
        ]
        self.kernel.copy_kernel.assert_called_once_with(
            'tmpdir', 'pxeboot.result-image.x86_64-1.2.3.kernel'
        )
        mock_symlink.assert_called_once_with(
            'pxeboot.result-image.x86_64-1.2.3.kernel',
            'tmpdir/result-image.x86_64-1.2.3.kernel'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'tmpdir', '/pxeboot.result-image.x86_64-1.2.3.xen.gz'
        )
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid, 'initrd_kiwi_install', install_initrd=True
        )
        self.boot_image_task.cleanup.assert_called_once_with()
        assert mock_command.call_args_list[1] == call(
            [
                'mv', 'initrd',
                'tmpdir/pxeboot.result-image.x86_64-1.2.3.initrd'
            ]
        )
        mock_chmod.assert_called_once_with(
            'tmpdir/pxeboot.result-image.x86_64-1.2.3.initrd', 420
        )
        mock_archive.assert_called_once_with(
            'target_dir/result-image.x86_64-1.2.3.install.tar'
        )
        archive.create.assert_called_once_with('tmpdir')

        mock_chmod.reset_mock()
        mock_copy.reset_mock()
        self.install_image.initrd_system = 'dracut'
        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.install_image.create_install_pxe_archive()

        assert mock_copy.call_args_list == [
            call(
                'root_dir/boot/initrd-kernel_version',
                'tmpdir/result-image.x86_64-1.2.3.initrd'
            ),
            call(
                'root_dir/config.bootoptions',
                'tmpdir/result-image.x86_64-1.2.3.config.bootoptions'
            )
        ]
        assert mock_chmod.call_args_list == [
            call('tmpdir/result-image.x86_64-1.2.3.initrd', 420),
            call('tmpdir/pxeboot.result-image.x86_64-1.2.3.initrd', 420)
        ]
        assert m_open.call_args_list == [
            call('tmpdir/result-image.x86_64-1.2.3.append', 'w'),
        ]
        assert m_open.return_value.write.call_args_list == [
            call(
                ' '.join([
                    'rd.kiwi.install.pxe',
                    'rd.kiwi.install.image=http://example.com/image.xz',
                    'custom_kernel_options\n'
                ])
            )
        ]

        self.boot_image_task.include_module.assert_any_call('kiwi-dump')
        self.boot_image_task.include_module.assert_any_call('kiwi-dump-reboot')
        assert self.boot_image_task.omit_module.call_args_list == [
            call('multipath'), call('module1'), call('module2')
        ]
        self.boot_image_task.set_static_modules.assert_called_once_with(
            ['module1', 'module2']
        )
