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
        assert self.isofs.custom_args['create_options'] == []
        assert self.isofs.custom_args['mount_options'] == []
        assert self.isofs.custom_args['some_args'] == 'data'

    @patch('kiwi.filesystem.isofs.Command.run')
    @patch('kiwi.filesystem.isofs.Iso.get_iso_creation_tool')
    @patch('kiwi.filesystem.isofs.Iso')
    def test_create_on_file(
        self, mock_iso, mock_get_iso_creation_tool, mock_command
    ):
        iso = mock.Mock()
        iso.header_end_name = 'header_end'
        iso.get_iso_creation_parameters = mock.Mock(
            return_value=['args']
        )
        mock_get_iso_creation_tool.return_value = '/usr/bin/mkisofs'
        mock_iso.return_value = iso
        self.isofs.create_on_file('myimage', None)
        iso.init_iso_creation_parameters.assert_called_once_with([])
        iso.add_efi_loader_parameters.assert_called_once_with()
        iso.create_header_end_block.assert_called_once_with(
            'myimage'
        )
        assert mock_command.call_args_list == [
            call([
                '/usr/bin/mkisofs', 'args', '-o', 'myimage', 'root_dir'
            ]),
            call([
                '/usr/bin/mkisofs', '-hide', 'header_end',
                '-hide-joliet', 'header_end', 'args', '-o', 'myimage',
                'root_dir'
            ])
        ]
        iso.relocate_boot_catalog.assert_called_once_with(
            'myimage'
        )
        iso.fix_boot_catalog.assert_called_once_with(
            'myimage'
        )
