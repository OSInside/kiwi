from mock import patch
from mock import call

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiIsoToolError

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

    @raises(KiwiIsoToolError)
    @patch('kiwi.filesystem.isofs.Command.run')
    @patch('kiwi.filesystem.isofs.Iso')
    @patch('kiwi.filesystem.isofs.Path.which')
    def test_create_on_file_no_tool_found(
        self, mock_which, mock_iso, mock_command
    ):
        mock_which.return_value = None
        self.isofs.create_on_file('myimage', None)

    @patch('kiwi.filesystem.isofs.Command.run')
    @patch('kiwi.filesystem.isofs.Iso')
    @patch('kiwi.filesystem.isofs.Path.which')
    def test_create_on_file_mkisofs(
        self, mock_which, mock_iso, mock_command
    ):
        iso = mock.Mock()
        iso.header_end_name = 'header_end'
        iso.get_iso_creation_parameters = mock.Mock(
            return_value=['args']
        )
        mock_iso.return_value = iso
        path_return_values = [
            '/usr/bin/mkisofs', '/usr/bin/mkisofs'
        ]

        def side_effect(arg):
            return path_return_values.pop()

        mock_which.side_effect = side_effect
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

    @patch('kiwi.filesystem.isofs.Command.run')
    @patch('kiwi.filesystem.isofs.Iso')
    @patch('kiwi.filesystem.isofs.Path.which')
    def test_create_on_file_genisoimage(
        self, mock_which, mock_iso, mock_command
    ):
        iso = mock.Mock()
        iso.header_end_name = 'header_end'
        iso.get_iso_creation_parameters = mock.Mock(
            return_value=['args']
        )
        mock_iso.return_value = iso
        path_return_values = [
            '/usr/bin/genisoimage', None, '/usr/bin/genisoimage', None
        ]

        def side_effect(arg):
            return path_return_values.pop()

        mock_which.side_effect = side_effect
        self.isofs.create_on_file('myimage', None)
        iso.init_iso_creation_parameters.assert_called_once_with([])
        iso.add_efi_loader_parameters.assert_called_once_with()
        iso.create_header_end_block.assert_called_once_with(
            'myimage'
        )
        assert mock_command.call_args_list == [
            call([
                '/usr/bin/genisoimage', 'args', '-o', 'myimage', 'root_dir'
            ]),
            call([
                '/usr/bin/genisoimage', '-hide', 'header_end',
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
