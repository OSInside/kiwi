from unittest.mock import (
    patch, Mock
)
from pytest import (
    fixture, raises
)

from kiwi.package_manager.apk import PackageManagerApk

from kiwi.exceptions import KiwiBootStrapPhaseFailed


class TestPackageManagerApk:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        repository = Mock()
        repository.root_dir = '/root-dir'

        repository.runtime_config = Mock(
            return_value={
                'bootstrap_repo': 'https://some',
                'command_env': ['env']
            }
        )
        self.manager = PackageManagerApk(repository)

    def setup_method(self, cls):
        self.setup()

    def test_request_package(self):
        self.manager.request_package('name')
        assert self.manager.package_requests == ['name']

    def test_request_collection(self):
        self.manager.request_collection('name')
        assert self.manager.collection_requests == []
        assert self.manager.package_requests == ['name']

    def test_request_product(self):
        self.manager.request_product('name')
        assert self.manager.product_requests == []

    def test_request_package_exclusion(self):
        self.manager.request_package_exclusion('name')
        assert self.manager.exclude_requests == ['name']

    def test_setup_repository_modules(self):
        self.manager.setup_repository_modules({})

    def test_process_install_requests_bootstrap_raises(self):
        self.manager.bootstrap_repo = None
        with raises(KiwiBootStrapPhaseFailed):
            self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.call')
    def test_process_install_requests_bootstrap_default(self, mock_call):
        self.manager.process_install_requests_bootstrap()
        mock_call.assert_called_once_with(
            [
                'apk', '--root', '/root-dir', '-X', 'https://some',
                '-U', '--allow-untrusted', '--initdb', 'add',
                'alpine-base',
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    def test_process_install_requests_bootstrap(self, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.process_install_requests_bootstrap()
        mock_call.assert_called_once_with(
            [
                'apk', '--root', '/root-dir', '-X', 'https://some',
                '-U', '--allow-untrusted', '--initdb', 'add',
                'vim', 'collection'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.request_package_exclusion('skipme')
        self.manager.process_install_requests()
        mock_run.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'update']
        )
        mock_call.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'add', 'vim', 'collection'],
            ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_run.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'update']
        )
        mock_call.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'del', 'vim'],
            ['env']
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == []

    def test_process_plus_recommended(self):
        self.manager.process_plus_recommended()
        assert self.manager.custom_args == []

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_update(self, mock_run, mock_call):
        self.manager.update()
        mock_run.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'update']
        )
        mock_call.assert_called_once_with(
            ['chroot', '/root-dir', 'apk', 'upgrade'],
            ['env']
        )

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', ' Installing foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', ' Removing foo')
