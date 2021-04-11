import mock
from pytest import raises

from kiwi.package_manager.base import PackageManagerBase


class TestPackageManagerBase:
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'
        self.manager = PackageManagerBase(repository)

    def test_request_package(self):
        with raises(NotImplementedError):
            self.manager.request_package('name')

    def test_request_collection(self):
        with raises(NotImplementedError):
            self.manager.request_collection('name')

    def test_request_product(self):
        with raises(NotImplementedError):
            self.manager.request_product('name')

    def test_request_package_lock(self):
        with raises(DeprecationWarning):
            self.manager.request_package_lock('name')

    def test_request_package_exclusion(self):
        with raises(NotImplementedError):
            self.manager.request_package_exclusion('name')

    def test_process_install_requests_bootstrap(self):
        with raises(NotImplementedError):
            self.manager.process_install_requests_bootstrap()

    def test_post_process_install_requests_bootstrap(self):
        self.manager.post_process_install_requests_bootstrap()

    def test_process_install_requests(self):
        with raises(NotImplementedError):
            self.manager.process_install_requests()

    def test_process_delete_requests(self):
        with raises(NotImplementedError):
            self.manager.process_delete_requests()

    def test_update(self):
        with raises(NotImplementedError):
            self.manager.update()

    def test_process_only_required(self):
        with raises(NotImplementedError):
            self.manager.process_only_required()

    def test_process_plus_recommended(self):
        with raises(NotImplementedError):
            self.manager.process_plus_recommended()

    def test_match_package_installed(self):
        with raises(NotImplementedError):
            self.manager.match_package_installed('package_name', 'log')

    def test_match_package_deleted(self):
        with raises(NotImplementedError):
            self.manager.match_package_deleted('package_name', 'log')

    def test_database_consistent(self):
        with raises(DeprecationWarning):
            self.manager.database_consistent()

    def test_dump_reload_package_database(self):
        with raises(DeprecationWarning):
            self.manager.dump_reload_package_database()

    def test_has_failed(self):
        assert self.manager.has_failed(0) is False
        assert self.manager.has_failed(1) is True

    def test_cleanup_requests(self):
        self.manager.cleanup_requests()
        assert self.manager.package_requests == []
        assert self.manager.product_requests == []
        assert self.manager.collection_requests == []
        assert self.manager.exclude_requests == []

    def test_clean_leftovers(self):
        self.manager.clean_leftovers()
