from pytest import fixture
from unittest.mock import (
    patch, call, mock_open
)
import unittest.mock as mock

from kiwi.repository.dnf5 import RepositoryDnf5


class TestRepositoryDnf5:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.repository.dnf5.Temporary.unmanaged_file')
    @patch('kiwi.repository.dnf5.ConfigParser')
    @patch('kiwi.repository.dnf5.Path.create')
    def setup(self, mock_path, mock_config, mock_temp):
        runtime_dnf_config = mock.MagicMock()
        mock_config.return_value = runtime_dnf_config
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'

        with patch('builtins.open', create=True):
            self.repo = RepositoryDnf5(
                root_bind, [
                    'exclude_docs', '_install_langs%en_US:de_DE',
                    '_target_arch%x86_64'
                ]
            )

        assert runtime_dnf_config.__setitem__.call_args_list == [
            call('main', {
                'system_cachedir': '/shared-dir/dnf/cache',
                'reposdir': '/shared-dir/dnf/repos',
                'varsdir': '/shared-dir/dnf/vars',
                'pluginconfpath': '/shared-dir/dnf/pluginconf',
                'keepcache': '1',
                'debuglevel': '2',
                'best': '1',
                'obsoletes': '1',
                'plugins': '0',
                'gpgcheck': '0'
            })
        ]

    @patch('kiwi.repository.dnf5.Temporary.unmanaged_file')
    @patch('kiwi.repository.dnf5.ConfigParser')
    @patch('kiwi.repository.dnf5.Path.create')
    def setup_method(self, cls, mock_path, mock_config, mock_temp):
        self.setup()

    @patch('kiwi.repository.dnf5.Temporary.unmanaged_file')
    @patch('kiwi.repository.dnf5.Path.create')
    def test_post_init_no_custom_args(self, mock_path, mock_temp):
        with patch('builtins.open', create=True):
            self.repo.post_init()
        assert self.repo.custom_args == []

    @patch('kiwi.repository.dnf5.Temporary.unmanaged_file')
    @patch('kiwi.repository.dnf5.Path.create')
    @patch('os.path.exists')
    def test_post_init_with_custom_args(
        self, mock_exists, mock_path, mock_temp
    ):
        mock_exists.return_value = True
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.repo.post_init(['check_signatures'])
            assert m_open.call_args_list == [
                call(mock_temp.return_value.name, 'w')
            ]
        assert self.repo.custom_args == []
        assert self.repo.gpg_check == '1'

    @patch('kiwi.repository.dnf5.ConfigParser')
    def test_use_default_location(self, mock_config):
        runtime_dnf_config = mock.MagicMock()
        mock_config.return_value = runtime_dnf_config

        with patch('builtins.open', create=True):
            self.repo.use_default_location()

        assert runtime_dnf_config.__setitem__.call_args_list == [
            call('main', {
                'system_cachedir': '../data/var/cache/libdnf5',
                'reposdir': '../data/etc/yum.repos.d',
                'varsdir': '../data/etc/dnf/vars',
                'pluginconfpath': '../data/etc/dnf/libdnf5-plugins',
                'keepcache': '1',
                'debuglevel': '2',
                'best': '1',
                'obsoletes': '1',
                'plugins': '0',
                'gpgcheck': '0'
            })
        ]

    def test_runtime_config(self):
        assert self.repo.runtime_config()['dnf_args'] == \
            self.repo.dnf_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    @patch('kiwi.repository.dnf5.ConfigParser')
    @patch('kiwi.repository.dnf5.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    @patch('os.path.isdir')
    @patch('kiwi.repository.dnf5.Path')
    def test_add_repo(
        self, mock_Path, mock_os_path_isdir, mock_Command_run, mock_exists,
        mock_buildservice, mock_config
    ):
        mock_os_path_isdir.return_value = False
        repo_config = mock.Mock()
        mock_buildservice.return_value = False
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        with patch('builtins.open', create=True) as mock_open:
            self.repo.add_repo(
                'foo', 'kiwi_iso_mount/uri', 'rpm-md', 42,
                customization_script='custom_script'
            )

            repo_config.add_section.assert_called_once_with('foo')
            assert repo_config.set.call_args_list == [
                call('foo', 'name', 'foo'),
                call('foo', 'baseurl', 'file://kiwi_iso_mount/uri'),
                call('foo', 'priority', '42'),
                call('foo', 'repo_gpgcheck', '0'),
                call('foo', 'gpgcheck', '0'),
            ]
            mock_open.assert_called_once_with(
                '/shared-dir/dnf/repos/foo.repo', 'w'
            )
            mock_Command_run.assert_called_once_with(
                [
                    'bash', '--norc', 'custom_script',
                    '/shared-dir/dnf/repos/foo.repo'
                ]
            )
            mock_Path.create.assert_called_once_with('/shared-dir/dnf/repos')

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
                call('bar', 'metalink', 'https://metalink'),
                call('bar', 'repo_gpgcheck', '0'),
                call('bar', 'gpgcheck', '0')
            ]
            mock_open.assert_called_once_with(
                '/shared-dir/dnf/repos/bar.repo', 'w'
            )

    @patch('kiwi.repository.dnf5.ConfigParser')
    @patch('kiwi.repository.dnf5.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    @patch('kiwi.repository.dnf5.Path')
    def test_add_repo_inside_buildservice(
        self, mock_path, mock_exists, mock_buildservice, mock_config
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
                call('foo', 'repo_gpgcheck', '0'),
                call('foo', 'gpgcheck', '0'),
                call('foo', 'module_hotfixes', '1')
            ]
            mock_open.assert_called_once_with(
                '/shared-dir/dnf/repos/foo.repo', 'w'
            )

    @patch('kiwi.repository.dnf5.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.dnf5.Path.create')
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

    @patch('kiwi.repository.dnf5.RpmDataBase')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.repository.dnf5.Path.create')
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

    @patch('kiwi.repository.dnf5.ConfigParser')
    @patch('kiwi.repository.dnf5.Defaults.is_buildservice_worker')
    @patch('os.path.exists')
    @patch('kiwi.repository.dnf5.Path')
    def test_add_repo_with_gpgchecks(
        self, mock_path, mock_exists, mock_buildservice, mock_config
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

    @patch('kiwi.repository.dnf5.RpmDataBase')
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
    @patch('kiwi.repository.dnf5.glob.iglob')
    def test_delete_repo_cache(self, mock_glob, mock_wipe):
        mock_glob.return_value = ['foo_cache']
        self.repo.delete_repo_cache('foo')
        mock_glob.assert_called_once_with(
            '/shared-dir/dnf/cache/foo*'
        )
        mock_wipe.assert_called_once_with(
            'foo_cache'
        )

    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_cleanup(self, mock_os_unlink, mock_os_path_isfile):
        self.repo.cleanup()
        mock_os_unlink.assert_called_once_with('tmpfile')
