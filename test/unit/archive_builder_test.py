from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.archive_builder import ArchiveBuilder


class TestArchiveBuilder(object):
    def setup(self):
        self.xml_state = mock.Mock()
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
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
        xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        archive = ArchiveBuilder(
            xml_state, 'target_dir', 'root_dir'
        )
        archive.create()

    @patch('kiwi.archive_builder.ArchiveTar')
    @patch('kiwi.archive_builder.Checksum')
    def test_create(self, mock_checksum, mock_tar):
        checksum = mock.Mock()
        mock_checksum.return_value = checksum
        archive = mock.Mock()
        mock_tar.return_value = archive
        self.archive.create()
        mock_tar.assert_called_once_with(
            'target_dir/myimage.tar'
        )
        archive.create_xz_compressed.assert_called_once_with(
            'root_dir'
        )
        mock_checksum.assert_called_once_with(
            'target_dir/myimage.tar.xz'
        )
        checksum.md5.assert_called_once_with(
            'target_dir/myimage.md5'
        )
