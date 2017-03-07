from mock import patch

import mock

from kiwi.filesystem.fat32 import FileSystemFat32


class TestFileSystemFat32(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.fat32 = FileSystemFat32(provider, 'root_dir')
        self.fat32.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem.fat32.Command.run')
    def test_create_on_device(self, mock_command):
        self.fat32.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkdosfs', '-F32', '-I', '-n', 'label', '/dev/foo'])
