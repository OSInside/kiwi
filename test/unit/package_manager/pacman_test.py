from mock import patch, call
from pytest import raises
import mock

from kiwi.package_manager.pacman import PackageManagerPacman

from kiwi.exceptions import KiwiRequestError


class TestPackageManagerPacman:
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = '/root-dir'

        repository.runtime_config = mock.Mock(
            return_value={
                'pacman_args': [
                    '--config', '/root-dir/pacman.conf', '-y', '--noconfirm'
                ],
                'command_env': ['env']
            }
        )
        self.manager = PackageManagerPacman(repository)

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

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests_bootstrap(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.process_install_requests_bootstrap()
        mock_run.call_args_list == [
            call(['rm', '-r', '-f', '/root-dir/var/run']),
            call([
                'pacman', '--config', '/root-dir/pacman.conf', '-y',
                '--noconfirm', '--needed', '--root', '/root-dir', '-Sy'
            ])
        ]
        mock_call.assert_called_once_with(
            [
                'pacman', '--config', '/root-dir/pacman.conf',
                '-y', '--noconfirm', '--root', '/root-dir', '-S',
                '--needed', '--overwrite', '/root-dir/var/run',
                'vim', 'collection'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    def test_process_install_requests(self, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.request_package_exclusion('skipme')
        self.manager.process_install_requests()
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'pacman', '--config',
                '/pacman.conf', '-y', '--noconfirm', '-S',
                '--needed', 'vim', 'collection'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'pacman', '--config', '/pacman.conf',
                '-y', '--noconfirm', '-Rdd', 'vim'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_no_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'pacman', '--config', '/pacman.conf',
                '-y', '--noconfirm', '-Rs', 'vim'
            ], ['env']
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    def test_process_delete_requests_package_missing(
        self, mock_call, mock_run
    ):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        with raises(KiwiRequestError):
            self.manager.process_delete_requests()
        mock_run.assert_called_once_with(
            ['chroot', '/root-dir', 'pacman', '-Qi', 'vim']
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == []

    def test_process_plus_recommended(self):
        self.manager.process_plus_recommended()
        assert self.manager.custom_args == []

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'pacman', '--config', '/pacman.conf',
                '-y', '--noconfirm', '-Su'
            ], ['env']
        )

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', ' installing foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', ' removing foo')
