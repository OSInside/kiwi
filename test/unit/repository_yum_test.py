
from mock import patch
from mock import call

import mock

from .test_helper import *

from kiwi.repository.yum import RepositoryYum
from kiwi.system.root_bind import RootBind


class TestRepositoryYum(object):
    @patch('kiwi.repository.yum.NamedTemporaryFile')
    @patch_open
    @patch('kiwi.repository.yum.ConfigParser')
    @patch('kiwi.repository.yum.Path.create')
    def setup(self, mock_path, mock_config, mock_open, mock_temp):
        runtime_yum_config = mock.Mock()
        mock_config.return_value = runtime_yum_config
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        self.repo = RepositoryYum(root_bind)

        assert runtime_yum_config.set.call_args_list == [
            call('main', 'cachedir', '/shared-dir/yum/cache'),
            call('main', 'reposdir', '/shared-dir/yum/repos'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'pkgpolicy', 'newest'),
            call('main', 'tolerant', '0'),
            call('main', 'exactarch', '1'),
            call('main', 'obsoletes', '1'),
            call('main', 'plugins', '1'),
            call('main', 'metadata_expire', '1800'),
            call('main', 'group_command', 'compat')
        ]

    @patch_open
    @patch('kiwi.repository.yum.ConfigParser')
    def test_use_default_location(self, mock_config, mock_open):
        runtime_yum_config = mock.Mock()
        mock_config.return_value = runtime_yum_config

        self.repo.use_default_location()

        assert runtime_yum_config.set.call_args_list == [
            call('main', 'cachedir', '../data/var/cache/yum'),
            call('main', 'reposdir', '../data/etc/yum/repos.d'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'pkgpolicy', 'newest'),
            call('main', 'tolerant', '0'),
            call('main', 'exactarch', '1'),
            call('main', 'obsoletes', '1'),
            call('main', 'plugins', '1'),
            call('main', 'metadata_expire', '1800'),
            call('main', 'group_command', 'compat')
        ]

    def test_runtime_config(self):
        assert self.repo.runtime_config()['yum_args'] == \
            self.repo.yum_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    @patch('kiwi.repository.yum.ConfigParser')
    @patch('os.path.exists')
    @patch_open
    def test_add_repo(self, mock_open, mock_exists, mock_config):
        repo_config = mock.Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        self.repo.add_repo('foo', 'kiwi_iso_mount/uri', 'rpm-md', 42)

        repo_config.add_section.assert_called_once_with('foo')
        assert repo_config.set.call_args_list == [
            call('foo', 'name', 'foo'),
            call('foo', 'baseurl', 'file://kiwi_iso_mount/uri'),
            call('foo', 'priority', '42')
        ]
        mock_open.assert_called_once_with(
            '/shared-dir/yum/repos/foo.repo', 'w'
        )

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo(self, mock_wipe):
        self.repo.delete_repo('foo')
        mock_wipe.assert_called_once_with(
            '/shared-dir/yum/repos/foo.repo'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('os.walk')
    def test_cleanup_unused_repos(self, mock_walk, mock_path):
        mock_walk.return_value = [
            ('/foo', ('bar', 'baz'), ('spam', 'eggs'))
        ]
        self.repo.repo_names = ['eggs']
        self.repo.cleanup_unused_repos()
        mock_path.assert_called_once_with(
            '/shared-dir/yum/repos/spam'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('kiwi.path.Path.create')
    def test_delete_all_repos(self, mock_create, mock_wipe):
        self.repo.delete_all_repos()
        mock_wipe.assert_called_once_with(
            '/shared-dir/yum/repos'
        )
        mock_create.assert_called_once_with(
            '/shared-dir/yum/repos'
        )
