from mock import patch
from mock import call

import mock

from kiwi.filesystem.isofs import FileSystemIsoFs


class TestFileSystemIsoFs(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.isofs = FileSystemIsoFs(mock.Mock(), 'root_dir')

    def test_post_init(self):
        self.isofs.post_init({'some_args': 'data'})
        assert self.isofs.custom_args['meta_data'] == {}
        assert self.isofs.custom_args['mount_options'] == []
        assert self.isofs.custom_args['some_args'] == 'data'

    @patch('kiwi.filesystem.isofs.IsoTools')
    @patch('kiwi.filesystem.isofs.Iso')
    def test_create_on_file(self, mock_iso, mock_cdrtools):
        iso_tool = mock.Mock()
        iso_tool.has_iso_hybrid_capability = mock.Mock(
            return_value=False
        )
        iso_tool.get_tool_name = mock.Mock(
            return_value='/usr/bin/mkisofs'
        )
        iso = mock.Mock()
        iso.header_end_name = 'header_end'
        mock_cdrtools.return_value = iso_tool
        mock_iso.return_value = iso
        self.isofs.create_on_file('myimage', None)

        iso.setup_isolinux_boot_path.assert_called_once_with()
        iso.create_header_end_marker.assert_called_once_with()

        iso_tool.init_iso_creation_parameters.assert_called_once_with({})
        iso_tool.add_efi_loader_parameters.assert_called_once_with()

        iso.create_header_end_block.assert_called_once_with('myimage')

        assert iso_tool.create_iso.call_args_list == [
            call('myimage'), call('myimage', hidden_files=['header_end'])
        ]

        iso.relocate_boot_catalog.assert_called_once_with(
            'myimage'
        )
        iso.fix_boot_catalog.assert_called_once_with(
            'myimage'
        )
        iso.create_hybrid.assert_called_once_with(
            iso.create_header_end_block.return_value,
            '0xffffffff', 'myimage', False
        )
