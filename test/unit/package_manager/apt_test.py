import logging
from mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
import mock

from kiwi.package_manager.apt import PackageManagerApt

from kiwi.exceptions import (
    KiwiDebootstrapError,
    KiwiRequestError
)


class TestPackageManagerApt:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'
        repository.signing_keys = ['key-file.asc']
        repository.keyring = 'trusted.gpg'
        repository.unauthenticated = 'false'
        repository.components = ['main', 'restricted']

        repository.runtime_config = mock.Mock(
            return_value={
                'apt_get_args': ['-c', 'apt.conf', '-y'],
                'command_env': ['env'],
                'distribution': 'xenial',
                'distribution_path': 'xenial_path'
            }
        )
        self.manager = PackageManagerApt(repository)

    def test_request_package(self):
        self.manager.request_package('name')
        assert self.manager.package_requests == ['name']

    def test_request_collection(self):
        self.manager.request_collection('name')
        with self._caplog.at_level(logging.WARNING):
            assert self.manager.collection_requests == []

    def test_request_product(self):
        self.manager.request_product('name')
        with self._caplog.at_level(logging.WARNING):
            assert self.manager.product_requests == []

    def test_request_package_exclusion(self):
        self.manager.request_package_exclusion('name')
        with self._caplog.at_level(logging.WARNING):
            assert self.manager.exclude_requests == []

    def test_process_install_requests_bootstrap_no_dist(self):
        self.manager.distribution = None
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap()

    @patch('os.path.exists')
    def test_process_install_requests_bootstrap_no_debootstrap_script(
        self, mock_exists
    ):
        mock_exists.return_value = False
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.apt.Path.wipe')
    def test_process_install_requests_bootstrap_failed_debootstrap(
        self, mock_wipe, mock_exists, mock_run
    ):
        self.manager.request_package('apt-get')
        mock_run.side_effect = Exception
        mock_exists.return_value = True
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.apt.DataSync')
    def test_process_install_requests_bootstrap(
        self, mock_sync, mock_exists, mock_run, mock_call
    ):
        self.manager.request_package('apt-get')
        self.manager.request_package('vim')
        data = mock.Mock()
        mock_sync.return_value = data
        mock_exists.return_value = True
        self.manager.process_install_requests_bootstrap()
        mock_sync.assert_called_once_with(
            'root-dir.debootstrap/', 'root-dir'
        )
        data.sync_data.assert_called_once_with(
            options=['-a', '-H', '-X', '-A', '--one-file-system', '--inplace'],
            exclude=['proc', 'sys', 'dev']
        )
        assert mock_run.call_args_list == [
            call(
                [
                    'debootstrap', '--keyring=trusted.gpg',
                    '--variant=minbase', '--components=main,restricted',
                    'xenial', 'root-dir.debootstrap', 'xenial_path'
                ], ['env']
            ),
            call(
                ['rm', '-r', '-f', 'root-dir.debootstrap']
            ),
            call(
                [
                    'chroot', 'root-dir', 'apt-get',
                    '-c', 'apt.conf', '-y', 'update'
                ], ['env']
            )
        ]
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            '-c', 'apt.conf', '-y', 'install', 'vim'],
            ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.apt.DataSync')
    def test_process_install_requests_bootstrap_no_gpg_check(
        self, mock_sync, mock_exists, mock_run, mock_call
    ):
        self.manager.request_package('apt-get')
        self.manager.request_package('vim')
        data = mock.Mock()
        mock_sync.return_value = data
        mock_exists.side_effect = lambda x: True if 'xenial' in x else False
        self.manager.process_install_requests_bootstrap()
        mock_sync.assert_called_once_with(
            'root-dir.debootstrap/', 'root-dir'
        )
        data.sync_data.assert_called_once_with(
            options=['-a', '-H', '-X', '-A', '--one-file-system', '--inplace'],
            exclude=['proc', 'sys', 'dev']
        )
        assert mock_run.call_args_list == [
            call(
                [
                    'debootstrap', '--no-check-gpg',
                    '--variant=minbase', '--components=main,restricted',
                    'xenial', 'root-dir.debootstrap', 'xenial_path'
                ], ['env']
            ),
            call(
                [
                    'chroot', 'root-dir', 'apt-get',
                    '-c', 'apt.conf', '-y', 'update'
                ], ['env']
            )
        ]
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            '-c', 'apt.conf', '-y', 'install', 'vim'],
            ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_install_requests()
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            '-c', 'apt.conf', '-y', 'install', 'vim'],
            ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'apt-get', '-c', 'apt.conf', '-y',
                '--auto-remove', 'remove', 'vim'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        mock_call.assert_called_once_with(
            ['chroot', 'root-dir', 'dpkg', '--force-all', '-r', 'vim'],
            ['env']
        )

    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_package_missing(self, mock_run):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        with raises(KiwiRequestError):
            self.manager.process_delete_requests()

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            '-c', 'apt.conf', '-y', 'upgrade'],
            ['env']
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--no-install-recommends']

    def test_process_plus_recommended(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--no-install-recommends']
        self.manager.process_plus_recommended()
        assert '--no-install-recommends' not in self.manager.custom_args

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', 'Unpacking foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', 'Removing foo')
