from mock import patch

import mock

import kiwi

from .test_helper import raises

from collections import namedtuple

from kiwi.exceptions import KiwiPxeBootImageError
from kiwi.builder.pxe import PxeBuilder


class TestPxeBuilder(object):
    @patch('kiwi.builder.pxe.FileSystemBuilder')
    @patch('kiwi.builder.pxe.BootImage')
    def setup(self, mock_boot, mock_filesystem):
        self.setup = mock.Mock()
        kiwi.builder.pxe.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        self.boot_image_task = mock.MagicMock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd_file_name'
        mock_boot.return_value = self.boot_image_task
        self.filesystem = mock.MagicMock()
        self.filesystem.filename = 'myimage.fs'
        mock_filesystem.return_value = self.filesystem
        self.xml_state = mock.Mock()
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='some-image'
        )
        kernel_type = namedtuple(
            'kernel', ['filename', 'version']
        )
        xen_type = namedtuple(
            'xen', ['filename', 'name']
        )
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock(
            return_value=kernel_type(filename='some-kernel', version='42')
        )
        self.kernel.get_xen_hypervisor = mock.Mock(
            return_value=xen_type(filename='hypervisor', name='xen.gz')
        )
        kiwi.builder.pxe.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.pxe = PxeBuilder(
            self.xml_state, 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )
        self.pxe.image_name = 'myimage'

    @patch('kiwi.builder.pxe.Checksum')
    @patch('kiwi.builder.pxe.Compress')
    @patch('kiwi.logger.log.warning')
    @patch('kiwi.builder.pxe.Command.run')
    @patch('os.rename')
    def test_create(
        self, mock_rename, mock_command, mock_log_warn,
        mock_compress, mock_checksum
    ):
        compress = mock.Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        checksum = mock.Mock()
        mock_checksum.return_value = checksum
        self.boot_image_task.required = mock.Mock(
            return_value=True
        )
        self.pxe.create()
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
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                'tar -C target_dir -c --to-stdout ' +
                'myimage-42.kernel ' +
                'initrd_file_name ' +
                'compressed-file-name ' +
                'some-image.x86_64-1.2.3.md5 ' +
                '| xz -f --threads=0 > ' +
                'target_dir/some-image.x86_64-1.2.3.tar.xz'
            ]
        )
        # warning for not implemented pxedeploy handling
        assert mock_log_warn.called

    @patch('kiwi.builder.pxe.Checksum')
    @patch('kiwi.builder.pxe.Compress')
    @patch('os.rename')
    @raises(KiwiPxeBootImageError)
    def test_create_no_kernel_found(
        self, mock_rename, mock_compress, mock_checksum
    ):
        compress = mock.Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        self.kernel.get_kernel.return_value = False
        self.pxe.create()

    @patch('kiwi.builder.pxe.Checksum')
    @patch('kiwi.builder.pxe.Compress')
    @patch('os.rename')
    @raises(KiwiPxeBootImageError)
    def test_create_no_hypervisor_found(
        self, mock_rename, mock_compress, mock_checksum
    ):
        compress = mock.Mock()
        mock_compress.return_value = compress
        compress.compressed_filename = 'compressed-file-name'
        self.kernel.get_xen_hypervisor.return_value = False
        self.pxe.create()
