
from mock import patch

import mock

from .test_helper import *

from kiwi.package_manager.base import PackageManagerBase


class TestPackageManagerBase(object):
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'
        self.manager = PackageManagerBase(repository)

    @raises(NotImplementedError)
    def test_request_package(self):
        self.manager.request_package('name')

    @raises(NotImplementedError)
    def test_request_collection(self):
        self.manager.request_collection('name')

    @raises(NotImplementedError)
    def test_request_product(self):
        self.manager.request_product('name')

    @raises(NotImplementedError)
    def test_process_install_requests_bootstrap(self):
        self.manager.process_install_requests_bootstrap()

    @raises(NotImplementedError)
    def test_process_install_requests(self):
        self.manager.process_install_requests()

    @raises(NotImplementedError)
    def test_process_delete_requests(self):
        self.manager.process_delete_requests()

    @raises(NotImplementedError)
    def test_update(self):
        self.manager.update()

    @raises(NotImplementedError)
    def test_process_only_required(self):
        self.manager.process_only_required()

    @raises(NotImplementedError)
    def test_match_package_installed(self):
        self.manager.match_package_installed('package_name', 'log')

    @raises(NotImplementedError)
    def test_match_package_deleted(self):
        self.manager.match_package_deleted('package_name', 'log')

    @raises(NotImplementedError)
    def test_database_consistent(self):
        self.manager.database_consistent()

    @raises(NotImplementedError)
    def test_dump_reload_package_database(self):
        self.manager.dump_reload_package_database()

    def test_cleanup_requests(self):
        self.manager.cleanup_requests()
        assert self.manager.package_requests == []
        assert self.manager.product_requests == []
        assert self.manager.collection_requests == []
