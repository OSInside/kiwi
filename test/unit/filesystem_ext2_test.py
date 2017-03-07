from mock import patch

import mock

from kiwi.filesystem.ext2 import FileSystemExt2


class TestFileSystemExt2(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.ext2 = FileSystemExt2(provider, 'root_dir')
        self.ext2.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem.ext2.Command.run')
    def test_create_on_device(self, mock_command):
        self.ext2.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.ext2', '-L', 'label', '/dev/foo'])
