from mock import patch
from mock import call

import mock
import os

from .test_helper import raises, patch_open

from kiwi.exceptions import (
    KiwiRepoTypeUnknown
)

from kiwi.repository.zypper import RepositoryZypper


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
        self.repo = RepositoryZypper(self.root_bind, ['exclude_docs'])

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

    @raises(KiwiRepoTypeUnknown)
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Uri')
    def test_add_repo_raises(self, mock_uri, mock_command):
        self.repo.add_repo('foo', 'uri', 'xxx')

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
                    '--type', 'YUM',
                    '--keep-packages',
                    '-C',
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
                    '--type', 'YUM',
                    '--no-keep-packages',
                    '-C',
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
                    '--type', 'YUM',
                    '--keep-packages',
                    '-C',
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

    @patch('kiwi.command.Command.run')
    def test_import_trusted_keys(self, mock_run):
        self.repo.import_trusted_keys(['key-file-a.asc', 'key-file-b.asc'])
        assert mock_run.call_args_list == [
            call([
                'rpm', '--root', '../data', '--import',
                'key-file-a.asc', '--dbpath', '/var/lib/rpm'
            ]),
            call([
                'rpm', '--root', '../data', '--import',
                'key-file-b.asc', '--dbpath', '/var/lib/rpm'
            ])
        ]

    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.wipe')
    @patch('os.path.exists')
    @patch('kiwi.repository.zypper.Uri')
    @patch_open
    def test_add_repo_with_credentials(
        self, mock_open, mock_uri, mock_exists, mock_wipe, mock_command
    ):
        mock_open.return_value = self.context_manager_mock
        exists_results = [False, False, False, True]

        def side_effect(arg):
            return exists_results.pop()

        mock_exists.side_effect = side_effect

        self.repo.add_repo(
            name='foo', uri='http://some/repo',
            user='user', secret='secret', credentials_file='credentials_file'
        )
        mock_wipe.assert_called_once_with(
            '../data/shared-dir/zypper/credentials/credentials_file'
        )
        mock_open.assert_called_once_with(
            '../data/shared-dir/zypper/credentials/credentials_file', 'w'
        )
        assert self.file_mock.write.call_args_list == [
            call('username=user\n'),
            call('password=secret\n')
        ]
        mock_command.assert_called_once_with(
            ['zypper'] + self.repo.zypper_args + [
                '--root', '../data',
                'addrepo', '--refresh',
                '--type', 'YUM',
                '--keep-packages',
                '-C',
                'http://some/repo?credentials=credentials_file',
                'foo'
            ], self.repo.command_env
        )

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
