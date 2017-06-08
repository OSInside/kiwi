
from mock import patch
from mock import call

from .test_helper import patch_open

import mock

from kiwi.repository.dnf import RepositoryDnf


class TestRepositoryDnf(object):
    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch_open
    @patch('kiwi.repository.dnf.ConfigParser')
    @patch('kiwi.repository.dnf.Path.create')
    @patch('kiwi.logger.log.warning')
    def setup(self, mock_warn, mock_path, mock_config, mock_open, mock_temp):
        runtime_dnf_config = mock.Mock()
        mock_config.return_value = runtime_dnf_config
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        self.repo = RepositoryDnf(root_bind, ['exclude_docs'])

        assert runtime_dnf_config.set.call_args_list == [
            call('main', 'cachedir', '/shared-dir/dnf/cache'),
            call('main', 'reposdir', '/shared-dir/dnf/repos'),
            call('main', 'pluginconfpath', '/shared-dir/dnf/pluginconf'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'pkgpolicy', 'newest'),
            call('main', 'tolerant', '0'),
            call('main', 'exactarch', '1'),
            call('main', 'obsoletes', '1'),
            call('main', 'plugins', '1'),
            call('main', 'gpgcheck', '0'),
            call('main', 'tsflags', 'nodocs'),
            call('main', 'enabled', '1')
        ]

    @patch_open
    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch('kiwi.repository.dnf.Path.create')
    def test_post_init_no_custom_args(self, mock_path, mock_temp, mock_open):
        self.repo.post_init()
        assert self.repo.custom_args == []

    @patch_open
    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch('kiwi.repository.dnf.Path.create')
    def test_post_init_with_custom_args(self, mock_path, mock_temp, mock_open):
        self.repo.post_init(['check_signatures'])
        assert self.repo.custom_args == []
        assert self.repo.gpg_check == '1'

    @patch_open
    @patch('kiwi.repository.dnf.ConfigParser')
    def test_use_default_location(self, mock_config, mock_open):
        runtime_dnf_config = mock.Mock()
        mock_config.return_value = runtime_dnf_config

        self.repo.use_default_location()

        assert runtime_dnf_config.set.call_args_list == [
            call('main', 'cachedir', '../data/var/cache/dnf'),
            call('main', 'reposdir', '../data/etc/yum.repos.d'),
            call('main', 'pluginconfpath', '../data/etc/dnf/plugins'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'pkgpolicy', 'newest'),
            call('main', 'tolerant', '0'),
            call('main', 'exactarch', '1'),
            call('main', 'obsoletes', '1'),
            call('main', 'plugins', '1'),
            call('main', 'gpgcheck', '0'),
            call('main', 'tsflags', 'nodocs'),
            call('main', 'enabled', '1')
        ]

    def test_runtime_config(self):
        assert self.repo.runtime_config()['dnf_args'] == \
            self.repo.dnf_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    @patch('kiwi.repository.dnf.ConfigParser')
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
            '/shared-dir/dnf/repos/foo.repo', 'w'
        )

    @patch('kiwi.repository.dnf.ConfigParser')
    @patch('os.path.exists')
    @patch_open
    def test_add_repo_with_gpgchecks(
        self, mock_open, mock_exists, mock_config
    ):
        repo_config = mock.Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        self.repo.add_repo(
            'foo', 'kiwi_iso_mount/uri', 'rpm-md', 42,
            repo_gpgcheck=False, pkg_gpgcheck=True
        )

        repo_config.add_section.assert_called_once_with('foo')
        assert repo_config.set.call_args_list == [
            call('foo', 'name', 'foo'),
            call('foo', 'baseurl', 'file://kiwi_iso_mount/uri'),
            call('foo', 'priority', '42'),
            call('foo', 'repo_gpgcheck', '0'),
            call('foo', 'gpgcheck', '1')
        ]
        mock_open.assert_called_once_with(
            '/shared-dir/dnf/repos/foo.repo', 'w'
        )

    @patch('kiwi.command.Command.run')
    def test_import_trusted_keys(self, mock_run):
        self.repo.import_trusted_keys(['key-file-a.asc', 'key-file-b.asc'])
        assert mock_run.call_args_list == [
            call(['rpm', '--root', '../data', '--import', 'key-file-a.asc']),
            call(['rpm', '--root', '../data', '--import', 'key-file-b.asc'])
        ]

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo(self, mock_wipe):
        self.repo.delete_repo('foo')
        mock_wipe.assert_called_once_with(
            '/shared-dir/dnf/repos/foo.repo'
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
            '/shared-dir/dnf/repos/spam'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('kiwi.path.Path.create')
    def test_delete_all_repos(self, mock_create, mock_wipe):
        self.repo.delete_all_repos()
        mock_wipe.assert_called_once_with(
            '/shared-dir/dnf/repos'
        )
        mock_create.assert_called_once_with(
            '/shared-dir/dnf/repos'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('kiwi.repository.dnf.glob.iglob')
    def test_delete_repo_cache(self, mock_glob, mock_wipe):
        mock_glob.return_value = ['foo_cache']
        self.repo.delete_repo_cache('foo')
        mock_glob.assert_called_once_with(
            '/shared-dir/dnf/cache/foo*'
        )
        mock_wipe.assert_called_once_with(
            'foo_cache'
        )
