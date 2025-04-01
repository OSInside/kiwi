import io
from unittest.mock import (
    patch, Mock, MagicMock
)
from kiwi.repository.apk import RepositoryApk


class TestRepositoryApk:
    @patch('kiwi.repository.apk.Path.create')
    def setup(self, mock_path_create):
        root_bind = Mock()
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        self.repo = RepositoryApk(root_bind)
        mock_path_create.assert_called_once_with('../data//etc/apk')

    @patch('kiwi.repository.apk.Path.create')
    def setup_method(self, cls, mock_path_create):
        self.setup()

    def test_runtime_config(self):
        assert self.repo.runtime_config()['bootstrap_repo'] == \
            self.repo.bootstrap_repo
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    def test_add_repo(self):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo('some', 'https://some')
            assert self.repo.bootstrap_repo == 'https://some'
            file_handle.write.assert_called_once_with('https://some\n')

    def test_setup_package_database_configuration(self):
        self.repo.setup_package_database_configuration()

    def test_import_trusted_keys(self):
        self.repo.import_trusted_keys([])

    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_delete_repo(self, mock_os_unlink, mock_os_path_isfile):
        mock_os_path_isfile.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo('some_A', 'https://some_A')
            self.repo.add_repo('some_B', 'https://some_B')

            mock_open.reset_mock()

            self.repo.delete_repo('some_A')
            mock_os_unlink.assert_called_once_with('../data//etc/apk/repositories')
            mock_open.assert_called_once_with('../data//etc/apk/repositories', 'a')
            file_handle.write.assert_called_once_with('https://some_B\n')

    @patch('os.unlink')
    @patch('os.path.isfile')
    def test_delete_all_repos(self, mock_os_path_isfile, mock_os_unlink):
        mock_os_path_isfile.return_value = True
        self.repo.delete_all_repos()
        mock_os_unlink.assert_called_once_with(
            '../data//etc/apk/repositories'
        )
        mock_os_path_isfile.assert_called_once_with(
            '../data//etc/apk/repositories'
        )

    def test_cleanup_unused_repos(self):
        self.repo.cleanup_unused_repos()

    def test_use_default_location(self):
        self.repo.use_default_location()

    def test_delete_repo_cache(self):
        self.repo.delete_repo_cache('unused')
