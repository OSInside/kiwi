from mock import patch

import mock

from .test_helper import raises

from kiwi.package_manager.dnf import PackageManagerDnf
from kiwi.exceptions import KiwiRequestError


class TestPackageManagerDnf(object):
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'

        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        repository.root_bind = root_bind

        repository.runtime_config = mock.Mock(
            return_value={
                'dnf_args': ['-c', 'dnf.conf', '-y'],
                'command_env': ['env']
            }
        )
        self.manager = PackageManagerDnf(repository)

    def test_request_package(self):
        self.manager.request_package('name')
        assert self.manager.package_requests == ['name']

    def test_request_collection(self):
        self.manager.request_collection('name')
        assert self.manager.collection_requests == ['"name"']

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
        mock_run.assert_called_once_with(
            ['dnf', '-c', 'dnf.conf', '-y', 'makecache']
        )
        mock_call.assert_called_once_with(
            [
                'bash', '-c',
                'dnf -c dnf.conf -y --installroot root-dir install vim && ' +
                'dnf -c dnf.conf -y --installroot root-dir group install ' +
                '"collection"'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.request_package_exclusion('skipme')
        self.manager.process_install_requests()
        self.manager.root_bind.move_to_root(
            self.manager.dnf_args
        )
        mock_run.assert_called_once_with(
            ['chroot', 'root-dir', 'rpm', '--rebuilddb']
        )
        mock_call.assert_called_once_with(
            [
                'bash', '-c',
                'chroot root-dir dnf root-moved-arguments --exclude=skipme install vim && ' +
                'chroot root-dir dnf root-moved-arguments --exclude=skipme group install ' +
                '"collection"'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'rpm', '-e',
                '--nodeps', '--allmatches', '--noscripts', 'vim'
            ],
            [
                'env'
            ]
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_no_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'dnf',
                'root-moved-arguments', 'autoremove', 'vim'
            ],
            ['env']
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    @raises(KiwiRequestError)
    def test_process_delete_requests_package_missing(
        self, mock_call, mock_run
    ):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_run.assert_called_once_with(
            ['chroot', 'root-dir', 'rpm', '-q', 'vim']
        )

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        self.manager.root_bind.move_to_root(
            self.manager.dnf_args
        )
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'dnf',
                'root-moved-arguments', 'upgrade'
            ], ['env']
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--setopt=install_weak_deps=False']

    def test_process_plus_recommended(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--setopt=install_weak_deps=False']
        self.manager.process_plus_recommended()
        assert '--setopt=install_weak_deps=False' not in self.manager.custom_args

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', 'Installing  : foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', 'Removing: foo')

    @patch('kiwi.command.Command.run')
    def test_database_consistent(self, mock_command):
        assert self.manager.database_consistent() is True
        mock_command.assert_called_once_with(
            ['chroot', 'root-dir', 'rpmdb', '--initdb']
        )

    @patch('kiwi.command.Command.run')
    def test_database_not_consistent(self, mock_command):
        mock_command.side_effect = Exception
        assert self.manager.database_consistent() is False

    def test_dump_reload_package_database(self):
        self.manager.dump_reload_package_database()
