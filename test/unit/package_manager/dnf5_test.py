from unittest.mock import (
    patch, call
)
from pytest import raises
import unittest.mock as mock

from kiwi.package_manager.dnf5 import PackageManagerDnf5

from kiwi.exceptions import KiwiRequestError


class TestPackageManagerDnf5:
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = '/root-dir'

        repository.runtime_config = mock.Mock(
            return_value={
                'dnf_args': ['--config', '/root-dir/dnf.conf', '-y'],
                'command_env': ['env']
            }
        )
        self.manager = PackageManagerDnf5(repository)

    def setup_method(self, cls):
        self.setup()

    def test_request_package(self):
        self.manager.request_package('name')
        assert self.manager.package_requests == ['name']

    def test_request_collection(self):
        self.manager.request_collection('name')
        assert self.manager.collection_requests == ['@name']

    def test_request_product(self):
        self.manager.request_product('name')
        assert self.manager.product_requests == []

    def test_request_package_exclusion(self):
        self.manager.request_package_exclusion('name')
        assert self.manager.exclude_requests == ['name']

    @patch('kiwi.command.Command.run')
    def test_setup_repository_modules(self, mock_run):
        self.manager.setup_repository_modules(
            {
                'disable': ['mod_c'],
                'enable': ['mod_a:stream', 'mod_b']
            }
        )
        dnf_call_args = [
            'dnf5', '--config', '/root-dir/dnf.conf',
            '-y', '--installroot', '/root-dir', '--releasever=0'
        ]
        assert mock_run.call_args_list == [
            call(
                dnf_call_args + [
                    'module', 'disable', 'mod_c'
                ], ['env']
            ),
            call(
                dnf_call_args + [
                    'module', 'reset', 'mod_a'
                ], ['env']
            ),
            call(
                dnf_call_args + [
                    'module', 'enable', 'mod_a:stream'
                ], ['env']
            ),
            call(
                dnf_call_args + [
                    'module', 'reset', 'mod_b'
                ], ['env']
            ),
            call(
                dnf_call_args + [
                    'module', 'enable', 'mod_b'
                ], ['env']
            )
        ]

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests_bootstrap(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.request_collection('collection')
        self.manager.request_package_exclusion('skipme')
        self.manager.process_install_requests_bootstrap()
        mock_run.assert_called_once_with(
            [
                'dnf5', '--config', '/root-dir/dnf.conf', '-y',
                '--releasever=0', 'makecache'
            ]
        )
        mock_call.assert_called_once_with(
            [
                'dnf5', '--config', '/root-dir/dnf.conf', '-y',
                '--installroot', '/root-dir', '--releasever=0',
                '--exclude=skipme',
                'install', 'vim', '@collection'
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
                'chroot', '/root-dir', 'dnf5', '--config', '/dnf.conf', '-y',
                '--releasever=0', '--exclude=skipme',
                'install', 'vim', '@collection'
            ], ['env']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'rpm', '-e',
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
                'chroot', '/root-dir', 'dnf5',
                '--config', '/dnf.conf', '-y',
                '--releasever=0', '--setopt=clean_requirements_on_remove=true',
                'remove', 'vim'
            ],
            ['env']
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    def test_process_delete_requests_package_missing(
        self, mock_call, mock_run
    ):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        with raises(KiwiRequestError):
            self.manager.process_delete_requests(force=True)
        mock_run.assert_called_once_with(
            ['chroot', '/root-dir', 'rpm', '-q', 'vim']
        )

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        mock_call.assert_called_once_with(
            [
                'chroot', '/root-dir', 'dnf5',
                '--config', '/dnf.conf', '-y',
                '--releasever=0', 'upgrade'
            ], ['env']
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--setopt=install_weak_deps=False']

    def test_process_plus_recommended(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--setopt=install_weak_deps=False']
        self.manager.process_plus_recommended()
        assert \
            '--setopt=install_weak_deps=False' not in self.manager.custom_args

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', 'Installing  : foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', 'Removing: foo')

    @patch('kiwi.package_manager.dnf5.RpmDataBase')
    def test_post_process_install_requests_bootstrap(self, mock_RpmDataBase):
        rpmdb = mock.Mock()
        rpmdb.has_rpm.return_value = True
        mock_RpmDataBase.return_value = rpmdb
        self.manager.post_process_install_requests_bootstrap()
        rpmdb.rebuild_database.assert_called_once_with()
        rpmdb.set_database_to_image_path.assert_called_once_with()

    @patch('kiwi.package_manager.dnf5.Rpm')
    def test_clean_leftovers(self, mock_rpm):
        mock_rpm.return_value = mock.Mock()
        self.manager.clean_leftovers()
        mock_rpm.assert_called_once_with(
            '/root-dir', 'macros.kiwi-image-config'
        )
        mock_rpm.return_value.wipe_config.assert_called_once_with()
