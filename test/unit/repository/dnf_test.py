from pytest import fixture
from mock import (
    patch, call, mock_open
)
import mock

from kiwi.repository.dnf import RepositoryDnf


class TestRepositoryDnf:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch('kiwi.repository.dnf.ConfigParser')
    @patch('kiwi.repository.dnf.Path.create')
    def setup(self, mock_path, mock_config, mock_temp):
        runtime_dnf_config = mock.Mock()
        mock_config.return_value = runtime_dnf_config
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'

        with patch('builtins.open', create=True):
            self.repo = RepositoryDnf(
                root_bind, ['exclude_docs', '_install_langs%en_US:de_DE']
            )

        assert runtime_dnf_config.set.call_args_list == [
            call('main', 'cachedir', '/shared-dir/dnf/cache'),
            call('main', 'reposdir', '/shared-dir/dnf/repos'),
            call('main', 'varsdir', '/shared-dir/dnf/vars'),
            call('main', 'pluginconfpath', '/shared-dir/dnf/pluginconf'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'best', '1'),
            call('main', 'obsoletes', '1'),
            call('main', 'plugins', '1'),
            call('main', 'gpgcheck', '0'),
            call('main', 'tsflags', 'nodocs'),
            call('main', 'enabled', '1')
        ]

    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch('kiwi.repository.dnf.Path.create')
    def test_post_init_no_custom_args(self, mock_path, mock_temp):
        with patch('builtins.open', create=True):
            self.repo.post_init()
        assert self.repo.custom_args == []

    @patch('kiwi.repository.dnf.NamedTemporaryFile')
    @patch('kiwi.repository.dnf.Path.create')
    @patch('os.path.exists')
    def test_post_init_with_custom_args(
        self, mock_exists, mock_path, mock_temp
    ):
        mock_exists.return_value = True
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.repo.post_init(['check_signatures'])
            assert m_open.call_args_list == [
                call(mock_temp.return_value.name, 'w'),
                call('/shared-dir/dnf/pluginconf/priorities.conf', 'w')
            ]
        assert self.repo.custom_args == []
        assert self.repo.gpg_check == '1'

    @patch('kiwi.repository.dnf.ConfigParser')
    def test_use_default_location(self, mock_config):
        runtime_dnf_config = mock.Mock()
        mock_config.return_value = runtime_dnf_config

        with patch('builtins.open', create=True):
            self.repo.use_default_location()

        assert runtime_dnf_config.set.call_args_list == [
            call('main', 'cachedir', '../data/var/cache/dnf'),
            call('main', 'reposdir', '../data/etc/yum.repos.d'),
            call('main', 'varsdir', '../data/etc/dnf/vars'),
            call('main', 'pluginconfpath', '../data/etc/dnf/plugins'),
            call('main', 'keepcache', '1'),
            call('main', 'debuglevel', '2'),
            call('main', 'best', '1'),
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
    @patch('kiwi.repository.dnf.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    def test_add_repo(self, mock_exists, mock_buildservice, mock_config):
        repo_config = mock.Mock()
        mock_buildservice.return_value = False
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        with patch('builtins.open', create=True) as mock_open:
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

        repo_config.add_section.reset_mock()
        repo_config.set.reset_mock()
        mock_exists.return_value = False
        with patch('builtins.open', create=True) as mock_open:
            self.repo.add_repo(
                'bar', 'https://metalink', 'rpm-md', sourcetype='metalink'
            )

            repo_config.add_section.assert_called_once_with('bar')
            assert repo_config.set.call_args_list == [
                call('bar', 'name', 'bar'),
                call('bar', 'metalink', 'https://metalink')
            ]
            mock_open.assert_called_once_with(
                '/shared-dir/dnf/repos/bar.repo', 'w'
            )

    @patch('kiwi.repository.dnf.ConfigParser')
    @patch('kiwi.repository.dnf.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    def test_add_repo_inside_buildservice(
        self, mock_exists, mock_buildservice, mock_config
    ):
        repo_config = mock.Mock()
        mock_buildservice.return_value = True
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        with patch('builtins.open', create=True) as mock_open:
            self.repo.add_repo('foo', 'kiwi_iso_mount/uri', 'rpm-md', 42)

            repo_config.add_section.assert_called_once_with('foo')
            assert repo_config.set.call_args_list == [
                call('foo', 'name', 'foo'),
                call('foo', 'baseurl', 'file://kiwi_iso_mount/uri'),
                call('foo', 'priority', '42'),
                call('foo', 'module_hotfixes', '1')
            ]
            mock_open.assert_called_once_with(
                '/shared-dir/dnf/repos/foo.repo', 'w'
            )

    @patch('kiwi.repository.dnf.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.dnf.Path.create')
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
        mock_Path_create.assert_called_once_with('../data/var/lib')
        mock_Command_run.assert_called_once_with(
            [
                'ln', '-s', '--no-target-directory',
                '../../usr/lib/sysimage/rpm', '../data/var/lib/rpm'
            ], raise_on_error=False
        )

    @patch('kiwi.repository.dnf.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.dnf.Path.create')
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
        mock_Path_create.assert_called_once_with('../data/var/lib')
        mock_Command_run.assert_called_once_with(
            [
                'ln', '-s', '--no-target-directory',
                '../../usr/lib/sysimage/rpm', '../data/var/lib/rpm'
            ], raise_on_error=False
        )

    @patch('kiwi.repository.dnf.ConfigParser')
    @patch('kiwi.repository.dnf.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    def test_add_repo_with_gpgchecks(
        self, mock_exists, mock_buildservice, mock_config
    ):
        repo_config = mock.Mock()
        mock_buildservice.return_value = False
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        with patch('builtins.open', create=True) as mock_open:
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

    @patch('kiwi.repository.dnf.RpmDataBase')
    def test_import_trusted_keys(self, mock_RpmDataBase):
        rpmdb = mock.Mock()
        mock_RpmDataBase.return_value = rpmdb
        signing_keys = ['key-file-a.asc', 'key-file-b.asc']
        self.repo.import_trusted_keys(signing_keys)
        assert rpmdb.import_signing_key_to_image.call_args_list == [
            call('key-file-a.asc'),
            call('key-file-b.asc')
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
