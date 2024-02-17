import unittest.mock as mock
from pytest import raises

from kiwi.repository.base import RepositoryBase


class TestRepositoryBase:
    def setup(self):
        root_bind = mock.Mock()
        self.repo = RepositoryBase(root_bind)
        self.repo.root_dir = 'root-dir'
        self.repo.shared_location = 'shared-dir'

    def setup_method(self, cls):
        self.setup()

    def test_use_default_location(self):
        with raises(NotImplementedError):
            self.repo.use_default_location()

    def test_runtime_config(self):
        with raises(NotImplementedError):
            self.repo.runtime_config()

    def test_add_repo(self):
        with raises(NotImplementedError):
            self.repo.add_repo(
                'name', 'uri', 'type', 'prio', 'dist', ['components'], 'user',
                'secret', 'credentials-file', False, False, False, False
            )

    def test_setup_package_database_configuration(self):
        with raises(NotImplementedError):
            self.repo.setup_package_database_configuration()

    def test_import_trusted_keys(self):
        with raises(NotImplementedError):
            self.repo.import_trusted_keys(['key-file.asc'])

    def test_delete_repo(self):
        with raises(NotImplementedError):
            self.repo.delete_repo('name')

    def test_delete_all_repos(self):
        with raises(NotImplementedError):
            self.repo.delete_all_repos()

    def test_cleanup_unused_repos(self):
        with raises(NotImplementedError):
            self.repo.cleanup_unused_repos()

    def test_delete_repo_cache(self):
        with raises(NotImplementedError):
            self.repo.delete_repo_cache('foo')
