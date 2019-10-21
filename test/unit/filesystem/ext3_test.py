from mock import patch

import mock

from kiwi.filesystem.ext3 import FileSystemExt3


class TestFileSystemExt3:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.ext3 = FileSystemExt3(provider, 'root_dir')
        self.ext3.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem.ext3.Command.run')
    def test_create_on_device(self, mock_command):
        self.ext3.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.ext3', '-L', 'label', '/dev/foo'])
