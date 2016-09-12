
from mock import patch
from mock import call

import mock
import os

from .test_helper import *

from kiwi.exceptions import (
    KiwiRepoTypeUnknown
)

from kiwi.repository.zypper import RepositoryZypper
from kiwi.system.root_bind import RootBind


class TestRepositoryZypper(object):
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.NamedTemporaryFile')
    @patch_open
    def setup(self, mock_open, mock_temp, mock_command):
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        self.repo = RepositoryZypper(root_bind, ['exclude_docs'])

    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.NamedTemporaryFile')
    @patch_open
    def test_custom_args_init(self, mock_open, mock_temp, mock_command):
        self.repo = RepositoryZypper(mock.MagicMock())
        assert self.repo.custom_args == []

    @raises(KiwiRepoTypeUnknown)
    @patch('kiwi.command.Command.run')
    def test_add_repo_raises(self, mock_command):
        self.repo.add_repo('foo', 'uri', 'xxx')

    def test_use_default_location(self):
        self.repo.use_default_location()
        assert self.repo.zypper_args == [
            '--non-interactive', '--no-gpg-checks'
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

    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.zypper.Path.wipe')
    @patch('os.path.exists')
    def test_add_repo(self, mock_exists, mock_wipe, mock_command):
        mock_exists.return_value = True
        self.repo.add_repo('foo', 'kiwi_iso_mount/uri', 'rpm-md', 42)
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
            call(
                ['zypper'] + self.repo.zypper_args + [
                    '--root', '../data',
                    'modifyrepo', '--priority', '42', 'foo'
                ], self.repo.command_env
            ),
            call([
                'mv', '-f',
                '/shared-dir/packages.moved', '/shared-dir/packages'
            ])
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

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_destructor(self, mock_exists, mock_command):
        mock_exists.return_value = True
        self.repo.__del__()
        mock_command.assert_called_once_with(
            ['mv', '-f', '/shared-dir/packages.moved', '/shared-dir/packages']
        )
