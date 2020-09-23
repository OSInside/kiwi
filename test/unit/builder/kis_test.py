from collections import namedtuple
from mock import (
    patch, Mock, MagicMock, mock_open
)
from pytest import (
    raises, fixture
)
import kiwi

from kiwi.builder.kis import KisBuilder
from kiwi.exceptions import KiwiKisBootImageError


class TestKisBuilder:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.builder.kis.FileSystemBuilder')
    @patch('kiwi.builder.kis.BootImage')
    def setup(self, mock_boot, mock_filesystem):
        self.setup = Mock()
        kiwi.builder.kis.SystemSetup = Mock(
            return_value=self.setup
        )
        self.boot_image_task = MagicMock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd_file_name'
        mock_boot.new.return_value = self.boot_image_task
        self.filesystem = MagicMock()
        self.filesystem.filename = 'myimage.fs'
        self.filesystem.root_uuid = 'some_uuid'
        mock_filesystem.return_value = self.filesystem
        self.xml_state = Mock()
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.get_initrd_system = Mock(
            return_value='dracut'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='some-image'
        )
        self.xml_state.build_type = Mock()
        self.xml_state.build_type.get_kernelcmdline = Mock(
            return_value='console=hvc0'
        )
        kernel_type = namedtuple(
            'kernel', ['filename', 'version']
        )
        xen_type = namedtuple(
            'xen', ['filename', 'name']
        )
        self.kernel = Mock()
        self.kernel.get_kernel = Mock(
            return_value=kernel_type(filename='some-kernel', version='42')
        )
        self.kernel.get_xen_hypervisor = Mock(
            return_value=xen_type(filename='hypervisor', name='xen.gz')
        )
        kiwi.builder.kis.Kernel = Mock(
            return_value=self.kernel
        )
        self.kis = KisBuilder(
            self.xml_state, 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )
        self.kis.image_name = 'myimage'
        self.kis.compressed = True

    @patch('kiwi.builder.kis.Checksum')
    @patch('kiwi.builder.kis.Compress')
    @patch('kiwi.builder.kis.ArchiveTar')
    @patch('os.rename')
    def test_create(
        self, mock_rename, mock_tar, mock_compress, mock_checksum
    ):
        tar = Mock()
        mock_tar.return_value = tar
        compress = Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        checksum = Mock()
        mock_checksum.return_value = checksum
        self.boot_image_task.required = Mock(
            return_value=True
        )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.kis.create()

        m_open.assert_called_once_with(
            'target_dir/some-image.x86_64-1.2.3.append', 'w'
        )
        m_open.return_value.write.assert_called_once_with(
            'root=UUID=some_uuid console=hvc0'
        )

        self.filesystem.create.assert_called_once_with()
        mock_rename.assert_called_once_with(
            'myimage.fs', 'myimage'
        )
        compress.xz.assert_called_once_with(None)
        checksum.md5.assert_called_once_with(
            'target_dir/some-image.x86_64-1.2.3.md5'
        )
        self.boot_image_task.prepare.assert_called_once_with()
        self.setup.export_modprobe_setup.assert_called_once_with(
            'initrd_dir'
        )
        self.boot_image_task.create_initrd.assert_called_once_with()
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )

        tar.create.assert_called_once_with('target_dir')

        self.kis.compressed = False

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.kis.create()

        m_open.return_value.write.assert_called_once_with(
            'root=UUID=some_uuid console=hvc0'
        )

        tar.create_xz_compressed.assert_called_once_with(
            'target_dir', xz_options=['--threads=0']
        )

    @patch('kiwi.builder.kis.Checksum')
    @patch('kiwi.builder.kis.Compress')
    @patch('os.rename')
    def test_create_no_kernel_found(
        self, mock_rename, mock_compress, mock_checksum
    ):
        compress = Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        self.kernel.get_kernel.return_value = False
        with raises(KiwiKisBootImageError):
            self.kis.create()

    @patch('kiwi.builder.kis.Checksum')
    @patch('kiwi.builder.kis.Compress')
    @patch('os.rename')
    def test_create_no_hypervisor_found(
        self, mock_rename, mock_compress, mock_checksum
    ):
        compress = Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        self.kernel.get_xen_hypervisor.return_value = False
        with raises(KiwiKisBootImageError):
            self.kis.create()
