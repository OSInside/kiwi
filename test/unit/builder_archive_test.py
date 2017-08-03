from mock import patch

import mock
import kiwi

from .test_helper import raises

from kiwi.exceptions import KiwiArchiveSetupError
from kiwi.builder.archive import ArchiveBuilder


class TestArchiveBuilder(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.xml_state = mock.Mock()
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        self.setup = mock.Mock()
        kiwi.builder.archive.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        self.archive = ArchiveBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )

    @raises(KiwiArchiveSetupError)
    def test_create_unknown_archive_type(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='bogus'
        )
        xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        archive = ArchiveBuilder(
            xml_state, 'target_dir', 'root_dir'
        )
        archive.create()

    @patch('kiwi.builder.archive.ArchiveTar')
    @patch('kiwi.builder.archive.Checksum')
    @patch('platform.machine')
    def test_create(self, mock_machine, mock_checksum, mock_tar):
        mock_machine.return_value = 'x86_64'
        checksum = mock.Mock()
        mock_checksum.return_value = checksum
        archive = mock.Mock()
        mock_tar.return_value = archive
        self.archive.create()
        mock_tar.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.tar'
        )
        archive.create_xz_compressed.assert_called_once_with(
            'root_dir', exclude=[
                'image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi'
            ], xz_options=None
        )
        mock_checksum.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.tar.xz'
        )
        checksum.md5.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.md5'
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )
