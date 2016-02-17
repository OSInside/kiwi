from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_xfs import FileSystemXfs


class TestFileSystemXfs(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.xfs = FileSystemXfs(provider, 'root_dir')
        self.xfs.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem_xfs.Command.run')
    def test_create_on_device(self, mock_command):
        self.xfs.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.xfs', '-f', '-L', 'label', '/dev/foo'])
