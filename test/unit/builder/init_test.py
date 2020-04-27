from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.builder import ImageBuilder
from kiwi.exceptions import KiwiRequestedTypeError


class TestImageBuilder:
    @patch('kiwi.builder.FileSystemBuilder')
    def test_filesystem_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='ext4'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.builder.DiskBuilder')
    def test_disk_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='vmx'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.LiveImageBuilder')
    def test_live_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='iso'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.KisBuilder')
    def test_kis_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='kis'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )
        mock_builder.reset_mock()
        xml_state.get_build_type_name = Mock(
            return_value='pxe'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.ArchiveBuilder')
    def test_archive_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='tbz'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    @patch('kiwi.builder.ContainerBuilder')
    def test_container_builder(self, mock_builder):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='docker'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir', None
        )

    def test_unsupported_build_type(self):
        xml_state = Mock()
        xml_state.get_build_type_name = Mock(
            return_value='bogus'
        )
        with raises(KiwiRequestedTypeError):
            ImageBuilder(xml_state, 'target_dir', 'root_dir')
