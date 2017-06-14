from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiRequestedTypeError

from kiwi.builder import ImageBuilder


class TestImageBuilder(object):
    @patch('kiwi.builder.FileSystemBuilder')
    def test_filesystem_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='ext4'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.builder.DiskBuilder')
    def test_disk_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='vmx'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.LiveImageBuilder')
    def test_live_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='iso'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.PxeBuilder')
    def test_pxe_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.ArchiveBuilder')
    def test_archive_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.ContainerBuilder')
    def test_container_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='docker'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @raises(KiwiRequestedTypeError)
    def test_unsupported_build_type(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='bogus'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
