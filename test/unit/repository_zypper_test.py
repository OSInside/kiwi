from pytest import raises
from mock import patch
from mock import call

import mock
import os

from .test_helper import patch_open
from kiwi.repository.zypper import RepositoryZypper
from kiwi.exceptions import KiwiCommandError


class TestRepositoryZypper(object):
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.NamedTemporaryFile')
    @patch_open
    def setup(self, mock_open, mock_temp, mock_command):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        self.root_bind = mock.Mock()
        self.root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        self.root_bind.root_dir = '../data'
        self.root_bind.shared_location = '/shared-dir'
        self.repo = RepositoryZypper(
            self.root_bind, ['exclude_docs', '_install_langs%en_US:de_DE']
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.NamedTemporaryFile')
    @patch_open
    def test_custom_args_init_excludedocs(
        self, mock_open, mock_temp, mock_command
    ):
        self.repo = RepositoryZypper(self.root_bind)
        assert self.repo.custom_args == []

    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.NamedTemporaryFile')
    @patch('kiwi.repository.zypper.ConfigParser')
    @patch_open
    def test_custom_args_init_check_signatures(
        self, mock_open, mock_config, mock_temp, mock_command
    ):
        runtime_zypp_config = mock.Mock()
        mock_config.return_value = runtime_zypp_config
        self.repo = RepositoryZypper(self.root_bind, ['check_signatures'])
        assert self.repo.custom_args == []
        assert runtime_zypp_config.set.call_args_list == [
            call(
                'main',
                'credentials.global.dir',
                '../data/shared-dir/zypper/credentials'
            ),
            call('main', 'gpgcheck', '1'),
        ]

    def test_use_default_location(self):
        self.repo.use_default_location()
        assert self.repo.zypper_args == [
            '--non-interactive'
        ]
        assert self.repo.shared_zypper_dir['reposd-dir'] == \
            '../data/etc/zypp/repos.d'
        assert self.repo.command_env == dict(
            os.environ, LANG='C'
        )

    def test_runtime_config(self):
        assert self.repo.runtime_config()['zypper_args'] == \
            self.repo.zypper_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    @patch.object(RepositoryZypper, '_backup_package_cache')
    @patch.object(RepositoryZypper, '_restore_package_cache')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path')
    @patch('kiwi.repository.zypper.Uri')
    @patch('os.path.exists')
    @patch_open
    def test_add_repo_second_attempt_on_failure(
        self, mock_open, mock_exists, mock_uri, mock_path, mock_command,
        mock_restore_package_cache, mock_backup_package_cache
    ):
        mock_command.side_effect = KiwiCommandError('error')
        with raises(KiwiCommandError):
            self.repo.add_repo('foo', 'http://foo/uri', 'rpm-md', 42)
        assert mock_command.call_count == 2

    @patch('kiwi.repository.zypper.ConfigParser')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.wipe')
    @patch('os.path.exists')
    @patch('kiwi.repository.zypper.Uri')
    @patch_open
    def test_add_repo(
        self, mock_open, mock_uri, mock_exists, mock_wipe,
        mock_command, mock_config
    ):
        repo_config = mock.Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True
        self.repo.add_repo('foo', 'kiwi_iso_mount/uri', 'rpm-md', 42)
        mock_wipe.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo'
        )
        uri = mock.Mock()
        uri.is_remote.return_value = True
        mock_uri.return_value = uri
        assert mock_command.call_args_list == [
            call([
                'mv', '-f',
                '/shared-dir/packages', '/shared-dir/packages.moved'
            ]),
            call(
                ['zypper'] + self.repo.zypper_args + [
                    '--root', '../data',
                    'addrepo', '--refresh',
                    '--keep-packages',
                    '--no-check',
                    'kiwi_iso_mount/uri',
                    'foo'
                ], self.repo.command_env
            ),
            call([
                'mv', '-f',
                '/shared-dir/packages.moved', '/shared-dir/packages'
            ])
        ]
        repo_config.read.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo'
        )
        repo_config.set.assert_called_once_with(
            'foo', 'priority', '42'
        )
        mock_open.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo', 'w'
        )
        mock_command.reset_mock()
        uri.is_remote.return_value = False
        self.repo.add_repo('foo', 'http://foo/uri', 'rpm-md', 42)
        assert mock_command.call_args_list == [
            call([
                'mv', '-f',
                '/shared-dir/packages', '/shared-dir/packages.moved'
            ]),
            call(
                ['zypper'] + self.repo.zypper_args + [
                    '--root', '../data',
                    'addrepo', '--refresh',
                    '--no-keep-packages',
                    '--no-check',
                    'http://foo/uri',
                    'foo'
                ], self.repo.command_env
            ),
            call([
                'mv', '-f',
                '/shared-dir/packages.moved', '/shared-dir/packages'
            ])
        ]

    @patch('kiwi.repository.zypper.ConfigParser')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.wipe')
    @patch('os.path.exists')
    @patch('kiwi.repository.zypper.Uri')
    @patch_open
    def test_add_repo_with_gpgchecks(
        self, mock_open, mock_uri, mock_exists, mock_wipe,
        mock_command, mock_config
    ):
        repo_config = mock.Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True
        self.repo.add_repo(
            'foo', 'kiwi_iso_mount/uri', 'rpm-md', 42,
            repo_gpgcheck=False, pkg_gpgcheck=True
        )
        mock_wipe.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo'
        )
        assert mock_command.call_args_list == [
            call([
                'mv', '-f',
                '/shared-dir/packages', '/shared-dir/packages.moved'
            ]),
            call(
                ['zypper'] + self.repo.zypper_args + [
                    '--root', '../data',
                    'addrepo', '--refresh',
                    '--keep-packages',
                    '--no-check',
                    'kiwi_iso_mount/uri',
                    'foo'
                ], self.repo.command_env
            ),
            call([
                'mv', '-f',
                '/shared-dir/packages.moved', '/shared-dir/packages'
            ])
        ]
        repo_config.read.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo'
        )
        assert repo_config.set.call_args_list == [
            call('foo', 'repo_gpgcheck', '0'),
            call('foo', 'pkg_gpgcheck', '1'),
            call('foo', 'priority', '42')
        ]
        mock_open.assert_called_once_with(
            '../data/shared-dir/zypper/repos/foo.repo', 'w'
        )

    @patch('kiwi.repository.zypper.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.create')
    def test_setup_package_database_configuration(
        self, mock_Path_create, mock_Command_run, mock_RpmDataBase
    ):
        rpmdb = mock.Mock()
        rpmdb.has_rpm.return_value = False
        rpmdb.rpmdb_host.expand_query.return_value = '/usr/lib/sysimage/rpm'
        mock_RpmDataBase.return_value = rpmdb
        self.repo.setup_package_database_configuration()
        assert mock_RpmDataBase.call_args_list == [
            call('../data', 'macros.kiwi-image-config'),
            call('../data')
        ]
        rpmdb.set_macro_from_string.assert_called_once_with(
            '_install_langs%en_US:de_DE'
        )
        rpmdb.write_config.assert_called_once_with()
        rpmdb.set_database_to_host_path.assert_called_once_with()
        rpmdb.init_database.assert_called_once_with()
        mock_Path_create.assert_called_once_with('../data/var/lib')
        mock_Command_run.assert_called_once_with(
            [
                'ln', '-s', '../../usr/lib/sysimage/rpm', '../data/var/lib/rpm'
            ], raise_on_error=False
        )

    @patch('kiwi.repository.zypper.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.create')
    def test_setup_package_database_configuration_bootstrapped_system(
        self, mock_Path_create, mock_Command_run, mock_RpmDataBase
    ):
        rpmdb = mock.Mock()
        rpmdb.has_rpm.return_value = True
        rpmdb.rpmdb_host.expand_query.return_value = '/usr/lib/sysimage/rpm'
        mock_RpmDataBase.return_value = rpmdb
        self.repo.setup_package_database_configuration()
        assert mock_RpmDataBase.call_args_list == [
            call('../data', 'macros.kiwi-image-config'),
            call('../data')
        ]
        rpmdb.set_macro_from_string.assert_called_once_with(
            '_install_langs%en_US:de_DE'
        )
        rpmdb.write_config.assert_called_once_with()
        rpmdb.link_database_to_host_path.assert_called_once_with()
        rpmdb.init_database.assert_called_once_with()
        mock_Path_create.assert_called_once_with('../data/var/lib')
        mock_Command_run.assert_called_once_with(
            [
                'ln', '-s', '../../usr/lib/sysimage/rpm', '../data/var/lib/rpm'
            ], raise_on_error=False
        )

    @patch('kiwi.repository.zypper.RpmDataBase')
    def test_import_trusted_keys(self, mock_RpmDataBase):
        rpmdb = mock.Mock()
        mock_RpmDataBase.return_value = rpmdb
        signing_keys = ['key-file-a.asc', 'key-file-b.asc']
        self.repo.import_trusted_keys(signing_keys)
        assert rpmdb.import_signing_key_to_image.call_args_list == [
            call('key-file-a.asc'),
            call('key-file-b.asc')
        ]

    @patch('kiwi.command.Command.run')
    def test_delete_repo(self, mock_command):
        self.repo.delete_repo('foo')
        mock_command.assert_called_once_with(
            ['zypper'] + self.repo.zypper_args + [
                '--root', '../data', 'removerepo', 'foo'
            ], self.repo.command_env
        )

    @patch('kiwi.path.Path.wipe')
    @patch('os.walk')
    def test_cleanup_unused_repos(self, mock_walk, mock_path):
        mock_walk.return_value = [
            ('/foo', ('bar', 'baz'), ('spam', 'eggs'))
        ]
        self.repo.repo_names = ['eggs']
        self.repo.cleanup_unused_repos()
        assert mock_path.call_args_list == [
            call('../data/shared-dir/zypper/solv/@System'),
            call('../data/shared-dir/zypper/repos/spam')
        ]

    @patch('kiwi.command.Command.run')
    def test_delete_all_repos(self, mock_command):
        self.repo.delete_all_repos()
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'rm', '-r', '-f', '../data/shared-dir/zypper/repos'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'mkdir', '-p', '../data/shared-dir/zypper/repos'
            ])

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo_cache(self, mock_wipe):
        self.repo.delete_repo_cache('foo')
        assert mock_wipe.call_args_list == [
            call('../data/shared-dir/packages/foo'),
            call('../data/shared-dir/zypper/solv/foo'),
            call('../data/shared-dir/zypper/raw/foo')
        ]

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_destructor(self, mock_exists, mock_command):
        mock_exists.return_value = True
        self.repo.__del__()
        mock_command.assert_called_once_with(
            ['mv', '-f', '/shared-dir/packages.moved', '/shared-dir/packages']
        )
