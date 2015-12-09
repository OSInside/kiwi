from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_isofs import FileSystemIsoFs


class TestFileSystemIsoFs(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.isofs = FileSystemIsoFs(mock.Mock(), 'source_dir')

    def test_post_init(self):
        self.isofs.post_init(['args'])
        assert self.isofs.custom_args == ['args']

    @patch('kiwi.filesystem_isofs.Command.run')
    @patch('kiwi.filesystem_isofs.Iso')
    def test_create_on_file(self, mock_iso, mock_command):
        iso = mock.Mock()
        iso.get_iso_creation_parameters = mock.Mock(
            return_value=['args']
        )
        mock_iso.return_value = iso
        self.isofs.create_on_file('myimage', None)
        iso.init_iso_creation_parameters.assert_called_once_with(None)
        iso.add_efi_loader_parameters.assert_called_once_with()
        mock_command.assert_called_once_with(
            ['genisoimage', 'args', '-o', 'myimage', 'source_dir']
        )
