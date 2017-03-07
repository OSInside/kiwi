from mock import patch
from mock import call
import mock

from kiwi.filesystem.clicfs import FileSystemClicFs


class TestFileSystemClicFs(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.clicfs = FileSystemClicFs(mock.Mock(), 'root_dir')

    @patch('kiwi.filesystem.clicfs.Command.run')
    @patch('kiwi.filesystem.clicfs.mkdtemp')
    @patch('kiwi.filesystem.clicfs.LoopDevice')
    @patch('kiwi.filesystem.clicfs.FileSystemExt4')
    @patch('kiwi.filesystem.clicfs.SystemSize')
    @patch('kiwi.filesystem.clicfs.Path.wipe')
    def test_create_on_file(
        self, mock_wipe, mock_size, mock_ext4, mock_loop,
        mock_dtemp, mock_command
    ):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        size.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        filesystem = mock.Mock()
        mock_ext4.return_value = filesystem
        loop_provider = mock.Mock()
        mock_loop.return_value = loop_provider
        mock_dtemp.return_value = 'tmpdir'

        self.clicfs.create_on_file('myimage', 'label')

        size.accumulate_mbyte_file_sizes.assert_called_once_with()
        size.customize.assert_called_once_with(42, 'ext4')
        mock_loop.assert_called_once_with(
            'tmpdir/fsdata.ext4', 42
        )
        loop_provider.create.assert_called_once_with()
        mock_ext4.assert_called_once_with(
            loop_provider, 'root_dir'
        )
        filesystem.create_on_device.assert_called_once_with()
        assert mock_command.call_args_list == [
            call(
                ['resize2fs', '-f', loop_provider.get_device(), '-M']
            ),
            call(
                ['mkclicfs', 'tmpdir/fsdata.ext4', 'myimage']
            )
        ]

    @patch('kiwi.filesystem.clicfs.Path.wipe')
    def test_destructor(self, mock_wipe):
        self.clicfs.container_dir = 'tmpdir'
        self.clicfs.__del__()
        mock_wipe.assert_called_once_with('tmpdir')
