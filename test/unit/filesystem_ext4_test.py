from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_ext4 import FileSystemExt4


class TestFileSystemExt4(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.ext4 = FileSystemExt4(provider, 'source_dir')
        self.ext4.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem_ext4.Command.run')
    def test_create_on_device(self, mock_command):
        self.ext4.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.ext4', '-L', 'label', '/dev/foo'])
