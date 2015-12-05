from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.pxe_builder import PxeBuilder


class TestPxeBuilder(object):
    @patch('kiwi.pxe_builder.FileSystemBuilder')
    @patch('kiwi.pxe_builder.BootImageTask')
    def setup(self, mock_boot, mock_filesystem):
        self.boot_image_task = mock.MagicMock()
        mock_boot.return_value = self.boot_image_task
        self.filesystem = mock.MagicMock()
        self.filesystem.filename = 'myimage'
        mock_filesystem.return_value = self.filesystem
        self.xml_state = mock.MagicMock()
        self.pxe = PxeBuilder(
            self.xml_state, 'target_dir', 'source_dir'
        )

    @raises(KiwiPxeBootImageError)
    def test_create_no_boot_attribute_configured(self):
        self.boot_image_task.required = mock.Mock(
            return_value=False
        )
        self.pxe.create()

    @patch('kiwi.pxe_builder.Checksum')
    @patch('kiwi.pxe_builder.Compress')
    def test_create(self, mock_compress, mock_checksum):
        compress = mock.Mock()
        mock_compress.return_value = compress
        checksum = mock.Mock()
        mock_checksum.return_value = checksum
        self.boot_image_task.required = mock.Mock(
            return_value=True
        )
        self.pxe.create()
        self.filesystem.create.assert_called_once_with()
        compress.xz.assert_called_once_with()
        checksum.md5.assert_called_once_with('myimage.md5')
        self.boot_image_task.prepare.assert_called_once_with()
        self.boot_image_task.extract_kernel_files.assert_called_once_with()
        self.boot_image_task.create_initrd.assert_called_once_with()
