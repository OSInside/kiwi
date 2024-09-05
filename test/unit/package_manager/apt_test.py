import logging
import io
from textwrap import dedent
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

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests_bootstrap_failed(
        self, mock_Command_run, mock_Command_call
    ):
        self.manager.request_package('apt')
        mock_Command_call.side_effect = Exception
        with patch('builtins.open', create=True):
            with raises(KiwiDebianBootstrapError):
                self.manager.process_install_requests_bootstrap()

    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.package_manager.apt.Temporary.new_file')
    def test_process_install_requests_bootstrap(
        self, mock_Temporary_new_file, mock_Command_call, mock_Command_run
    ):
        mock_Temporary_new_file.return_value.name = 'temporary'
        self.manager.request_package('vim')
        call_result = Mock()
        call_result.process.communicate.return_value = ('stdout', 'stderr')
        mock_Command_call.return_value = call_result
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.manager.process_install_requests_bootstrap()
            script = dedent('''\n
                set -e
                while read -r deb;do
                    echo "Unpacking $deb"
                    dpkg-deb --fsys-tarfile $deb | tar -C {0} -x
                done < {1}
                export PATH=/usr/bin:/bin:/usr/sbin:/sbin
                while read -r deb;do
                    pushd "$(dirname "$deb")" >/dev/null || exit 1
                    if [[ "$(basename "$deb")" == base-passwd* ]];then
                        echo "Running pre/post package scripts for $(basename "$deb")"
                        dpkg -e "$deb" "{0}/DEBIAN"
                        test -e {0}/DEBIAN/preinst && chroot {0} bash -c "/DEBIAN/preinst install"
                        test -e {0}/DEBIAN/postinst && chroot {0} bash -c "/DEBIAN/postinst"
                        rm -rf {0}/DEBIAN
                    fi
                    popd >/dev/null || exit 1
                done < {1}
                chroot {0} touch /var/lib/dpkg/status.kiwi
            ''')
            file_handle.write.assert_called_once_with(
                script.format('root-dir', 'temporary')
            )
        assert mock_Command_run.call_args_list == [
            call(
                ['apt-get', '-c', 'apt.conf', '-y', 'update'], ['env']
            ),
            call(
                [
                    'apt-get', '-c', 'apt.conf', '-y', 'install',
                    '-oDebug::pkgDPkgPm=1',
                    '-oDPkg::Pre-Install-Pkgs::=cat >temporary',
                    '?essential',
                    '?exact-name(usr-is-merged)',
                    'base-passwd',
                    'vim',
                    'apt'
                ], ['env']
            ),
            call(
                ['bash', 'temporary'], ['env']
            )
        ]

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_install_requests(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_install_requests()
        mock_call.assert_called_once_with([
            'chroot', 'root-dir', '/bin/bash', '-c',
            'apt-get -c apt.conf -y install vim && /bin/rm /var/lib/dpkg/status.kiwi'],
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
