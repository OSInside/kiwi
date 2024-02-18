import logging
from unittest.mock import (
    patch, call, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.package_manager.apt import PackageManagerApt

import kiwi.defaults as defaults

from kiwi.exceptions import (
    KiwiDebootstrapError,
    KiwiRequestError,
    KiwiFileNotFound
)


class TestPackageManagerApt:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        repository = Mock()
        repository.root_dir = 'root-dir'
        repository.signing_keys = ['key-file.asc']
        repository.keyring = 'trusted.gpg'
        repository.unauthenticated = 'false'
        repository.components = ['main', 'restricted']

        repository.runtime_config = Mock(
            return_value={
                'apt_get_args': ['-c', 'apt.conf', '-y'],
                'command_env': ['env'],
                'distribution': 'xenial',
                'distribution_path': 'xenial_path'
            }
        )
        self.manager = PackageManagerApt(repository)

    def setup_method(self, cls):
        self.setup()

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

    def test_setup_repository_modules(self):
        self.manager.setup_repository_modules({})

    @patch('kiwi.command.Command.run')
    @patch.object(PackageManagerApt, 'process_install_requests')
    @patch('os.path.isfile')
    def test_process_install_requests_bootstrap_prebuild_root(
        self, mock_os_path_isfile, mock_process_install_requests,
        mock_Command_run
    ):
        mock_os_path_isfile.return_value = True
        self.manager.process_install_requests_bootstrap(
            bootstrap_package='bootstrap-package'
        )
        assert mock_Command_run.call_args_list == [
            call(['apt-get', '-c', 'apt.conf', '-y', 'update'], ['env']),
            call(
                [
                    'apt-get', '-c', 'apt.conf', '-y',
                    'install', 'bootstrap-package'
                ], ['env']
            ),
            call(
                [
                    'tar', '-C', 'root-dir', '-xf',
                    '/var/lib/bootstrap/bootstrap-package.{0}.tar.xz'.format(
                        defaults.PLATFORM_MACHINE
                    )
                ]
            )
        ]
        mock_process_install_requests.assert_called_once_with()
        mock_os_path_isfile.return_value = False
        with raises(KiwiFileNotFound):
            self.manager.process_install_requests_bootstrap(
                bootstrap_package='bootstrap-package'
            )

    def test_process_install_requests_bootstrap_debootstrap_no_dist(self):
        self.manager.distribution = None
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap()

    @patch('os.path.exists')
    def test_process_install_requests_bootstrap_debootstrap_no_script(
        self, mock_exists
    ):
        mock_exists.return_value = False
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.call')
    @patch('kiwi.package_manager.apt.os.path.exists')
    @patch('kiwi.package_manager.apt.Path.wipe')
    def test_process_install_requests_bootstrap_debootstrap_failed(
        self, mock_wipe, mock_exists, mock_call
    ):
        self.manager.request_package('apt')
        mock_call.side_effect = Exception
        mock_exists.return_value = True
        mock_root_bind = Mock()
        with raises(KiwiDebootstrapError):
            self.manager.process_install_requests_bootstrap(mock_root_bind)

    @patch('kiwi.package_manager.apt.os.path.exists')
    def test_get_error_details(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = 'log-data'
            assert self.manager.get_error_details() == \
                file_handle.read.return_value
        mock_open.assert_called_once_with(
            'root-dir/debootstrap/debootstrap.log'
        )

    @patch('kiwi.package_manager.apt.os.path.exists')
    def test_get_error_details_no_log_file(self, mock_exists):
        mock_exists.return_value = False
        assert self.manager.get_error_details() == \
            "logfile 'root-dir/debootstrap/debootstrap.log' does not exist"

    @patch('kiwi.package_manager.apt.os.path.exists')
    def test_get_error_details_logfile_is_empty(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = ''
            assert self.manager.get_error_details() == \
                'logfile is empty'

    @patch('kiwi.command.Command.call')
    @patch('kiwi.package_manager.apt.Path.wipe')
    @patch('kiwi.package_manager.apt.os.path.exists')
    def test_process_install_requests_bootstrap_debootstrap(
        self, mock_exists, mock_wipe, mock_call
    ):
        self.manager.request_package('apt')
        self.manager.request_package('vim')
        call_result = Mock()
        call_result.process.communicate.return_value = ('stdout', 'stderr')
        mock_call.return_value = call_result
        mock_root_bind = Mock()
        mock_exists.return_value = True
        self.manager.process_install_requests_bootstrap(mock_root_bind)
        mock_call.assert_called_once_with(
            [
                'debootstrap', '--keyring=trusted.gpg',
                '--variant=minbase', '--include=vim',
                '--components=main,restricted', 'xenial',
                'root-dir', 'xenial_path'
            ], ['env']
        )
        assert mock_wipe.call_args_list == [
            call('root-dir/dev/fd'),
            call('root-dir/dev/pts')
        ]
        mock_root_bind.umount_kernel_file_systems.assert_called_once_with()

    def test_post_process_install_requests_bootstrap(self):
        mock_root_bind = Mock()
        self.manager.post_process_install_requests_bootstrap(mock_root_bind)
        mock_root_bind.mount_kernel_file_systems.assert_called_once_with(False)

    @patch('kiwi.command.Command.call')
    @patch('kiwi.package_manager.apt.Path.wipe')
    @patch('kiwi.package_manager.apt.os.path.exists')
    def test_process_install_requests_bootstrap_debootstrap_no_gpg_check(
        self, mock_exists, mock_wipe, mock_call
    ):
        self.manager.request_package('apt')
        self.manager.request_package('vim')
        call_result = Mock()
        call_result.process.communicate.return_value = ('stdout', 'stderr')
        mock_root_bind = Mock()
        mock_call.return_value = call_result
        mock_exists.side_effect = lambda x: True if 'xenial' in x else False
        self.manager.process_install_requests_bootstrap(mock_root_bind)
        mock_call.assert_called_once_with(
            [
                'debootstrap', '--no-check-gpg',
                '--variant=minbase', '--include=vim',
                '--components=main,restricted', 'xenial',
                'root-dir', 'xenial_path'
            ], ['env']
        )
        assert mock_wipe.call_args_list == [
            call('root-dir/dev/fd'),
            call('root-dir/dev/pts')
        ]
        mock_root_bind.umount_kernel_file_systems.assert_called_once_with()

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
    @patch('kiwi.package_manager.apt.Path.wipe')
    @patch('glob.iglob')
    def test_process_delete_requests_force(
        self, mock_iglob, mock_Path_wipe, mock_run, mock_call
    ):
        mock_iglob.return_value = ['glob-result']
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        assert mock_run.call_args_list == [
            call(
                [
                    'chroot', 'root-dir', 'dpkg', '-l', 'vim'
                ]
            ),
            call(
                [
                    'cp', 'root-dir/usr/sbin/ldconfig',
                    'root-dir/usr/sbin/ldconfig.orig'
                ]
            ),
            call(
                [
                    'cp', 'root-dir/usr/bin/true',
                    'root-dir/usr/sbin/ldconfig'
                ]
            )
        ]
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'dpkg',
                '--remove', '--force-remove-reinstreq',
                '--force-remove-essential', '--force-depends', 'vim'
            ],
            ['env']
        )
        mock_iglob.call_args_list == [
            call('root-dir/var/lib/dpkg/info/vim*.pre*'),
            call('root-dir/var/lib/dpkg/info/vim*.post*')
        ]
        mock_Path_wipe.call_args_list == [
            call('glob-result'), call('glob-result')
        ]

    @patch('kiwi.command.Command.run')
    def test_post_process_delete_requests(self, mock_run):
        self.manager.post_process_delete_requests()
        assert mock_run.call_args_list == [
            call(
                [
                    'mv', 'root-dir/usr/sbin/ldconfig.orig',
                    'root-dir/usr/sbin/ldconfig'
                ]
            )
        ]

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
