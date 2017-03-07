import mock

from .test_helper import raises

from kiwi.repository.base import RepositoryBase


class TestRepositoryBase(object):
    def setup(self):
        root_bind = mock.Mock()
        self.repo = RepositoryBase(root_bind)
        self.repo.root_dir = 'root-dir'
        self.repo.shared_location = 'shared-dir'

    @raises(NotImplementedError)
    def test_use_default_location(self):
        self.repo.use_default_location()

    @raises(NotImplementedError)
    def test_runtime_config(self):
        self.repo.runtime_config()

    @raises(NotImplementedError)
    def test_add_repo(self):
        self.repo.add_repo(
            'name', 'uri', 'type', 'prio', 'dist', ['components'],
            'user', 'secret', 'credentials-file'
        )

    @raises(NotImplementedError)
    def test_delete_repo(self):
        self.repo.delete_repo('name')

    @raises(NotImplementedError)
    def test_delete_all_repos(self):
        self.repo.delete_all_repos()

    @raises(NotImplementedError)
    def test_cleanup_unused_repos(self):
        self.repo.cleanup_unused_repos()
