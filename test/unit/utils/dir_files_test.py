from unittest.mock import (
    Mock, patch, call
)

from kiwi.utils.dir_files import DirFiles


class TestDirFiles:
    @patch('kiwi.utils.dir_files.Path')
    def setup(self, mock_Path):
        self.dir_manager = DirFiles('box_dir')
        mock_Path.wipe.assert_called_once_with('box_dir.tmp')

    @patch('kiwi.utils.dir_files.Path')
    def setup_method(self, cls, mock_Path):
        self.setup()

    @patch('kiwi.utils.dir_files.NamedTemporaryFile')
    def test_register(self, mock_NamedTemporaryFile):
        tmpfile = Mock()
        tmpfile.name = 'tmp_a'
        mock_NamedTemporaryFile.return_value = tmpfile
        self.dir_manager.register('/some/path/to/file_a')
        assert self.dir_manager.collection == {
            'file_a': 'tmp_a'
        }

    @patch('kiwi.utils.dir_files.NamedTemporaryFile')
    def test_deregister(self, mock_NamedTemporaryFile):
        tmpfile = Mock()
        tmpfile.name = 'tmp_a'
        mock_NamedTemporaryFile.return_value = tmpfile
        self.dir_manager.register('/some/path/to/file_a')
        assert self.dir_manager.collection == {
            'file_a': 'tmp_a'
        }
        self.dir_manager.deregister('/some/path/to/some/not/present')
        assert self.dir_manager.collection == {
            'file_a': 'tmp_a'
        }
        self.dir_manager.deregister('/some/path/to/file_a')
        assert self.dir_manager.collection == {}

    @patch('kiwi.utils.dir_files.Path')
    @patch('kiwi.utils.dir_files.Command.run')
    def test_commit(self, mock_Command_run, mock_Path):
        self.dir_manager.collection = {
            'file_a': 'tmp_a'
        }
        self.dir_manager.commit()
        mock_Path.create.assert_called_once_with('box_dir.tmp')
        assert mock_Command_run.call_args_list == [
            call(
                ['bash', '-c', 'cp -a box_dir/* box_dir.tmp'],
                raise_on_error=False
            ),
            call(['mv', 'tmp_a', 'box_dir.tmp/file_a']),
            call(['mv', 'box_dir', 'box_dir.wipe']),
            call(['mv', 'box_dir.tmp', 'box_dir']),
            call(['rm', '-rf', 'box_dir.wipe'])
        ]
