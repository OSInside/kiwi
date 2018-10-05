from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.package_manager.apt import PackageManagerApt
from kiwi.exceptions import (
    KiwiDebootstrapError,
    KiwiRequestError
)


class TestPackageManagerApt(object):
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'
        repository.signing_keys = ['key-file.asc']
        repository.unauthenticated = 'false'

        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        repository.root_bind = root_bind

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

    @patch('kiwi.logger.log.warning')
    def test_request_collection(self, mock_log_warn):
        self.manager.request_collection('name')
        assert self.manager.collection_requests == []
        assert mock_log_warn.called

    @patch('kiwi.logger.log.warning')
    def test_request_product(self, mock_log_warn):
        self.manager.request_product('name')
        assert self.manager.product_requests == []
        assert mock_log_warn.called

    @patch('kiwi.logger.log.warning')
    def test_request_package_exclusion(self, mock_log_warn):
        self.manager.request_package_exclusion('name')
        assert self.manager.exclude_requests == []
        assert mock_log_warn.called

    @raises(KiwiDebootstrapError)
    def test_process_install_requests_bootstrap_no_dist(self):
        self.manager.distribution = None
        self.manager.process_install_requests_bootstrap()

    @patch('os.path.exists')
    @raises(KiwiDebootstrapError)
    def test_process_install_requests_bootstrap_no_debootstrap_script(
        self, mock_exists
    ):
        mock_exists.return_value = False
        self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.apt.Path.wipe')
    @raises(KiwiDebootstrapError)
    def test_process_install_requests_bootstrap_failed_debootstrap(
        self, mock_wipe, mock_exists, mock_run
    ):
        self.manager.request_package('apt-get')
        mock_run.side_effect = Exception
        mock_exists.return_value = True
        self.manager.process_install_requests_bootstrap()

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.apt.DataSync')
    def test_process_install_requests_bootstrap(
        self, mock_sync, mock_exists, mock_run, mock_call, mock_warn
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
            options=['-a', '-H', '-X', '-A']
        )
        assert mock_run.call_args_list == [
            call(command=['mountpoint', '-q', 'root-dir/dev'], raise_on_error=False),
            call([
                'debootstrap', '--no-check-gpg', '--variant=minbase',
                'xenial', 'root-dir.debootstrap', 'xenial_path'],
                ['env']),
            call([
                'chroot', 'root-dir', 'apt-key', 'add', 'key-file.asc'
            ], ['env']),
            call(['rm', '-r', '-f', 'root-dir.debootstrap']),
            call([
                'chroot', 'root-dir', 'apt-get',
                'root-moved-arguments', 'update'
            ], ['env'])
        ]
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            'root-moved-arguments', 'install', 'vim'],
            ['env']
        )
        assert mock_warn.called

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_install_requests()
        self.manager.root_bind.move_to_root(
            self.manager.apt_get_args
        )
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            'root-moved-arguments', 'install', 'vim'],
            ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'apt-get', 'root-moved-arguments',
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
    @raises(KiwiRequestError)
    def test_process_delete_requests_package_missing(self, mock_run):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        self.manager.process_delete_requests()

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        self.manager.root_bind.move_to_root(
            self.manager.apt_get_args
        )
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            'root-moved-arguments', 'upgrade'],
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

    def test_database_consistent(self):
        self.manager.database_consistent()

    def test_dump_reload_package_database(self):
        self.manager.dump_reload_package_database()
