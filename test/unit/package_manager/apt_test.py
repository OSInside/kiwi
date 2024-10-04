import logging
import io
from unittest.mock import (
    patch, call, Mock, MagicMock
)
from pytest import (
    raises, fixture
)

from kiwi.package_manager.apt import PackageManagerApt

import kiwi.defaults as defaults

from kiwi.exceptions import (
    KiwiDebianBootstrapError,
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
        self.env = {'key': 'val'}

        repository.runtime_config = Mock(
            return_value={
                'apt_get_args': ['-c', 'apt.conf', '-y'],
                'command_env': self.env,
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

    @patch('pathlib.Path')
    @patch('kiwi.command.Command.run')
    @patch.object(PackageManagerApt, 'process_install_requests')
    @patch('os.path.isfile')
    def test_process_install_requests_bootstrap_prebuild_root(
        self, mock_os_path_isfile, mock_process_install_requests,
        mock_Command_run, mock_pathlib_Path
    ):
        mock_os_path_isfile.return_value = True
        self.manager.process_install_requests_bootstrap(
            bootstrap_package='bootstrap-package'
        )
        assert mock_Command_run.call_args_list == [
            call(['apt-get', '-c', 'apt.conf', '-y', 'update'], self.env),
            call(
                [
                    'apt-get', '-c', 'apt.conf', '-y',
                    'install', 'bootstrap-package'
                ], self.env
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

    @patch('pathlib.Path')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests_bootstrap_failed(
        self, mock_Command_run, mock_Command_call, mock_pathlib_Path
    ):
        self.manager.request_package('apt')
        mock_Command_call.side_effect = Exception
        with patch('builtins.open', create=True):
            with raises(KiwiDebianBootstrapError):
                self.manager.process_install_requests_bootstrap()

    @patch('pathlib.Path')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.package_manager.apt.Temporary.new_file')
    @patch('kiwi.package_manager.apt.Temporary.new_dir')
    @patch('os.path.exists')
    def test_process_install_requests_bootstrap(
        self, mock_os_path_exists, mock_Temporary_new_dir,
        mock_Temporary_new_file, mock_Command_call, mock_Command_run,
        mock_pathlib_Path
    ):
        mock_os_path_exists.return_value = True
        mock_Temporary_new_dir.return_value.name = 'tempdir'
        mock_Temporary_new_file.return_value.name = 'temporary'
        self.manager.request_package('vim')
        call_result = Mock()
        call_result.process.communicate.return_value = ('stdout', 'stderr')
        mock_Command_call.return_value = call_result
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.__iter__.return_value = ['base-passwd\n', 'usrmerge', 'vim\n']
            self.manager.process_install_requests_bootstrap()
        new_env = self.env | {
            'PATH': '$PATH:/usr/bin:/bin:/usr/sbin:/sbin',
            'DPKG_MAINTSCRIPT_NAME': 'true',
            'DPKG_MAINTSCRIPT_PACKAGE': 'libc6'
        }
        assert mock_Command_run.call_args_list == [
            call(
                ['apt-get', '-c', 'apt.conf', '-y', 'update'], self.env
            ),
            call(
                [
                    'apt-get', '-c', 'apt.conf', '-y', 'install',
                    '-oDebug::pkgDPkgPm=1',
                    '-oDPkg::Pre-Install-Pkgs::=cat >temporary',
                    '?essential',
                    'vim',
                    'apt'
                ], self.env
            ),
            call(
                [
                    'bash', '-c',
                    'dpkg-deb --fsys-tarfile base-passwd | tar -C root-dir -x'
                ], self.env
            ),
            call(
                [
                    'bash', '-c',
                    'dpkg-deb --fsys-tarfile usrmerge | tar -C root-dir -x'
                ], self.env
            ),
            call(
                [
                    'bash', '-c',
                    'dpkg-deb --fsys-tarfile vim | tar -C root-dir -x'
                ], self.env
            ),
            call(
                [
                    'dpkg', '-e', 'base-passwd', 'tempdir/base-passwd'
                ]
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/base-passwd/preinst', 'install'
                ], new_env
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/base-passwd/postinst', 'configure'
                ], new_env
            ),
            call(
                ['dpkg', '-e', 'base-passwd', 'tempdir/base-passwd']
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/base-passwd/preinst', 'install'
                ], new_env
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/base-passwd/postinst', 'configure'
                ], new_env
            ),
            call(
                ['dpkg', '-e', 'vim', 'tempdir/vim']
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/vim/preinst', 'install'
                ], new_env
            ),
            call(
                [
                    'chroot', 'root-dir', 'bash',
                    'tempdir/vim/postinst', 'configure'
                ], new_env
            )
        ]

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_install_requests()
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', 'apt-get',
            '-c', 'apt.conf', '-y', 'install', 'vim'],
            self.env
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
            ], self.env
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
            self.env
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
            self.env
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
