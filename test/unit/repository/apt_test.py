from unittest.mock import (
    patch, call, MagicMock
)
from base64 import b64encode
from pytest import raises
import io
import unittest.mock as mock

from kiwi.repository.apt import RepositoryApt
from kiwi.exceptions import KiwiUriOpenError


class TestRepositoryApt:
    @patch('kiwi.repository.apt.Temporary.unmanaged_file')
    @patch('kiwi.repository.apt.PackageManagerTemplateAptGet')
    @patch('kiwi.repository.apt.Path.create')
    def setup(self, mock_path, mock_template, mock_temp):
        self.apt_conf = mock.Mock()
        mock_template.return_value = self.apt_conf

        template = mock.Mock()
        self.apt_conf.get_host_template.return_value = template

        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = mock.Mock()
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'

        with patch('builtins.open', create=True):
            self.repo = RepositoryApt(
                root_bind, custom_args=['exclude_docs']
            )

            self.exclude_docs = True
            self.apt_conf.get_host_template.assert_called_once_with(
                self.exclude_docs
            )
            template.substitute.assert_called_once_with(
                {
                    'apt_shared_base': '/shared-dir/apt-get',
                    'unauthenticated': 'true'
                }
            )
            repo = RepositoryApt(
                root_bind, custom_args=['check_signatures', '_target_arch%amd64']
            )
            assert repo.custom_args == []
            assert repo.unauthenticated == 'false'

            repo = RepositoryApt(root_bind)
            assert repo.custom_args == []
            assert repo.unauthenticated == 'true'

    @patch('kiwi.repository.apt.Temporary.unmanaged_file')
    @patch('kiwi.repository.apt.PackageManagerTemplateAptGet')
    @patch('kiwi.repository.apt.Path.create')
    def setup_method(self, cls, mock_path, mock_template, mock_temp):
        self.setup()

    def test_use_default_location(self):
        template = mock.Mock()
        template.substitute.return_value = 'template-data'
        self.apt_conf.get_image_template.return_value = template
        with patch('builtins.open', create=True):
            self.repo.use_default_location()
        assert self.repo.shared_apt_get_dir['sources-dir'] == \
            '../data/etc/apt/sources.list.d'
        assert self.repo.shared_apt_get_dir['preferences-dir'] == \
            '../data/etc/apt/preferences.d'
        assert self.repo.shared_apt_get_dir['netrcparts-dir'] == \
            '../data/etc/apt/auth.conf.d'
        self.apt_conf.get_image_template.assert_called_once_with(
            self.exclude_docs
        )
        template.substitute.assert_called_once_with(
            {'apt_shared_base': '../data/etc/apt', 'unauthenticated': 'true'}
        )

    def test_runtime_config(self):
        assert self.repo.runtime_config()['apt_get_args'] == \
            self.repo.apt_get_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    def test_setup_package_database_configuration(self):
        # just pass
        self.repo.setup_package_database_configuration()

    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    def test_add_repo_with_priority(self, mock_Command_run, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', '/srv/my-repo', 'deb', '42', 'xenial', 'a b',
                customization_script='custom_script'
            )
            assert mock_open.call_args_list == [
                call('/shared-dir/apt-get/sources.list.d/foo.sources', 'w'),
                call('/shared-dir/apt-get/preferences.d/foo.pref', 'w')
            ]
            assert file_handle.write.call_args_list == [
                call(
                    'Types: deb\n'
                    'URIs: file:/srv/my-repo\n'
                    'Suites: xenial\n'
                    'Components: a b\n'
                ),
                call('Package: *\n'),
                call('Pin: origin ""\n'),
                call('Pin-Priority: 42\n')
            ]
            assert mock_Command_run.call_args_list == [
                call(
                    [
                        'bash', '--norc', 'custom_script',
                        '/shared-dir/apt-get/sources.list.d/foo.sources'
                    ]
                ),
                call(
                    [
                        'bash', '--norc', 'custom_script',
                        '/shared-dir/apt-get/preferences.d/foo.pref'
                    ]
                )
            ]
        mock_exists.return_value = False
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo',
                'http://download.opensuse.org/repositories/V:/A:/C/Debian_9.0/',
                'deb', '99', 'xenial', 'a b'
            )
            assert file_handle.write.call_args_list == [
                call(
                    'Types: deb\n'
                    'URIs: http://download.opensuse.org/repositories/V:/A:/C/Debian_9.0/\n'
                    'Suites: xenial\n'
                    'Components: a b\n'
                ),
                call('Package: *\n'),
                call('Pin: origin "download.opensuse.org"\n'),
                call('Pin-Priority: 99\n')
            ]

    @patch('os.path.exists')
    def test_add_repo_distribution(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', 'kiwi_iso_mount/uri', 'deb', None, 'xenial', 'a b',
                architectures='amd64,arm64'
            )
            file_handle.write.assert_called_once_with(
                'Types: deb\n'
                'URIs: file:/kiwi_iso_mount/uri\n'
                'Architectures: amd64 arm64\n'
                'Suites: xenial\n'
                'Components: a b\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.sources', 'w'
            )

    @patch('os.path.exists')
    def test_add_repo_private_with_authentication(self, mock_exists):
        mock_exists.return_value = False
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', 'https://example.org/debian', 'deb', None, 'xenial', 'a b',
                user='some-user', secret='some-secret',
                architectures='amd64,arm64'
            )
            assert mock_open.call_args_list == [
                call('/shared-dir/apt-get/sources.list.d/foo.sources', 'w'),
                call('/shared-dir/apt-get/auth.conf.d/foo.conf', 'w')
            ]
            assert file_handle.write.call_args_list == [
                call(
                    'Types: deb\n'
                    'URIs: https://example.org/debian\n'
                    'Architectures: amd64 arm64\n'
                    'Suites: xenial\n'
                    'Components: a b\n'
                ),
                call(
                    'machine https://example.org/debian login '
                    'some-user password some-secret\n'
                )
            ]
            file_handle.reset_mock()
            self.repo.add_repo(
                'foo', 'https://example.org/debian', 'deb', None, 'xenial', 'a b',
                secret='some-token',
                architectures='amd64,arm64'
            )
            assert file_handle.write.call_args_list == [
                call(
                    'Types: deb\n'
                    'URIs: https://example.org/debian\n'
                    'Architectures: amd64 arm64\n'
                    'Suites: xenial\n'
                    'Components: a b\n'
                ),
                call(
                    'machine https://example.org/debian login '
                    'some-token\n'
                )
            ]

    @patch('os.path.exists')
    def test_add_repo_distribution_without_gpgchecks(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', 'kiwi_iso_mount/uri', 'deb', None, 'xenial', 'a b',
                repo_gpgcheck=False, pkg_gpgcheck=False
            )
            file_handle.write.assert_called_once_with(
                'Types: deb\n'
                'URIs: file:/kiwi_iso_mount/uri\n'
                'Suites: xenial\n'
                'Components: a b\n'
                'trusted: yes\n'
                'check-valid-until: no\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.sources', 'w'
            )

    @patch('os.path.exists')
    def test_add_repo_distribution_default_component(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', '/kiwi_iso_mount/uri', 'deb', None, 'xenial'
            )
            file_handle.write.assert_called_once_with(
                'Types: deb\n'
                'URIs: file:/kiwi_iso_mount/uri\n'
                'Suites: xenial\n'
                'Components: main\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.sources', 'w'
            )

    @patch('os.path.exists')
    def test_add_repo_flat(self, mock_exists):
        mock_exists.return_value = False
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', 'http://repo.com', 'deb'
            )
            file_handle.write.assert_called_once_with(
                'Types: deb\n'
                'URIs: http://repo.com\n'
                'Suites: ./\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.sources', 'w'
            )

    @patch('kiwi.repository.apt.glob.glob')
    @patch('kiwi.repository.apt.os.chmod')
    @patch('kiwi.repository.apt.shutil.copy')
    @patch('kiwi.repository.apt.Path.create')
    @patch('kiwi.repository.apt.os.mkdir')
    @patch('kiwi.repository.apt.Temporary.new_dir')
    @patch('kiwi.repository.apt.os.unlink')
    @patch('kiwi.repository.apt.Command.run')
    def test_import_trusted_keys(
        self, mock_run, mock_unlink, mock_Temporary_new_dir, mock_mkdir,
        mock_Path_create, mock_copy, mock_chmod, mock_glob
    ):
        mock_Temporary_new_dir.return_value.__enter__.return_value = \
            '/tmp/keys'
        mock_glob.side_effect = lambda pattern: [
            pattern.replace('*', '0')
        ]
        self.repo.keyring_prefix = 'kiwi-1234-'
        self.repo.import_trusted_keys(['key-file-a.asc', 'key-file-b.asc'])

        # keyrings of a former import are deleted
        assert mock_unlink.call_args_list == [
            call('/etc/apt/keyrings/kiwi-1234-0.gpg'),
            call('../data/etc/apt/keyrings/kiwi-1234-0.gpg')
        ]
        mock_mkdir.assert_called_once_with('/tmp/keys/gnupg', 0o700)
        gpg_args = [
            'gpg', '--homedir', '/tmp/keys/gnupg', '--no-options',
            '--no-default-keyring', '--no-auto-check-trustdb',
            '--trust-model', 'always', '--keyring'
        ]
        assert mock_run.call_args_list == [
            call(gpg_args + [
                '/tmp/keys/keybox.0.gpg',
                '--import', '--ignore-time-conflict', 'key-file-a.asc'
            ]),
            call(gpg_args + [
                '/tmp/keys/keybox.0.gpg',
                '--export', '--yes', '--output', '/tmp/keys/kiwi-1234-0.gpg'
            ]),
            call(gpg_args + [
                '/tmp/keys/keybox.1.gpg',
                '--import', '--ignore-time-conflict', 'key-file-b.asc'
            ]),
            call(gpg_args + [
                '/tmp/keys/keybox.1.gpg',
                '--export', '--yes', '--output', '/tmp/keys/kiwi-1234-1.gpg'
            ])
        ]
        assert mock_Path_create.call_args_list == [
            call('/etc/apt/keyrings'),
            call('../data/etc/apt/keyrings'),
            call('/etc/apt/keyrings'),
            call('../data/etc/apt/keyrings')
        ]
        assert mock_copy.call_args_list == [
            call(
                '/tmp/keys/kiwi-1234-0.gpg',
                '/etc/apt/keyrings/kiwi-1234-0.gpg'
            ),
            call(
                '/tmp/keys/kiwi-1234-0.gpg',
                '../data/etc/apt/keyrings/kiwi-1234-0.gpg'
            ),
            call(
                '/tmp/keys/kiwi-1234-1.gpg',
                '/etc/apt/keyrings/kiwi-1234-1.gpg'
            ),
            call(
                '/tmp/keys/kiwi-1234-1.gpg',
                '../data/etc/apt/keyrings/kiwi-1234-1.gpg'
            )
        ]
        assert mock_chmod.call_args_list == [
            call('/etc/apt/keyrings/kiwi-1234-0.gpg', 0o644),
            call('../data/etc/apt/keyrings/kiwi-1234-0.gpg', 0o644),
            call('/etc/apt/keyrings/kiwi-1234-1.gpg', 0o644),
            call('../data/etc/apt/keyrings/kiwi-1234-1.gpg', 0o644)
        ]
        assert self.repo.keyrings == [
            '/etc/apt/keyrings/kiwi-1234-0.gpg',
            '/etc/apt/keyrings/kiwi-1234-1.gpg'
        ]

        # sources files reference the keyrings via Signed-By
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', 'http://example.com/debian', 'deb', None,
                'trixie', 'main'
            )
            file_handle.write.assert_called_once_with(
                'Types: deb\n'
                'URIs: http://example.com/debian\n'
                'Suites: trixie\n'
                'Components: main\n'
                'Signed-By: /etc/apt/keyrings/kiwi-1234-0.gpg '
                '/etc/apt/keyrings/kiwi-1234-1.gpg\n'
            )

    @patch('kiwi.repository.apt.glob.glob')
    @patch('kiwi.repository.apt.os.chmod')
    @patch('kiwi.repository.apt.shutil.copy')
    @patch('kiwi.repository.apt.Path.create')
    @patch('kiwi.repository.apt.os.mkdir')
    @patch('kiwi.repository.apt.urlopen')
    @patch('kiwi.repository.apt.Temporary.new_dir')
    @patch('kiwi.repository.apt.Command.run')
    def test_import_trusted_keys_remote(
        self, mock_run, mock_Temporary_new_dir, mock_urlopen, mock_mkdir,
        mock_Path_create, mock_copy, mock_chmod, mock_glob
    ):
        mock_glob.return_value = []
        mock_Temporary_new_dir.return_value.__enter__.return_value = \
            '/tmp/keys'
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            b'key-data'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.import_trusted_keys(
                [
                    'key-file-a.asc',
                    'https://user:pass%40word@example.com/key.asc',
                    'ftp://user:secret@example.com/key.asc'
                ]
            )
            assert mock_open.call_args_list == [
                call('/tmp/keys/key.1', 'wb'),
                call('/tmp/keys/key.2', 'wb')
            ]
            assert file_handle.write.call_args_list == [
                call(b'key-data'), call(b'key-data')
            ]
        http_request = mock_urlopen.call_args_list[0][0][0]
        assert http_request.full_url == 'https://example.com/key.asc'
        assert http_request.get_header('Authorization') == \
            'Basic ' + b64encode(b'user:pass@word').decode()
        ftp_request = mock_urlopen.call_args_list[1][0][0]
        assert ftp_request.full_url == \
            'ftp://user:secret@example.com/key.asc'
        assert ftp_request.get_header('Authorization') is None
        imported_keys = [
            command_call[0][0][-1] for command_call in mock_run.call_args_list
            if '--import' in command_call[0][0]
        ]
        assert imported_keys == [
            'key-file-a.asc', '/tmp/keys/key.1', '/tmp/keys/key.2'
        ]

    @patch('kiwi.repository.apt.glob.glob')
    @patch('kiwi.repository.apt.os.mkdir')
    @patch('kiwi.repository.apt.urlopen')
    @patch('kiwi.repository.apt.Temporary.new_dir')
    @patch('kiwi.repository.apt.Command.run')
    def test_import_trusted_keys_remote_download_failed(
        self, mock_run, mock_Temporary_new_dir, mock_urlopen, mock_mkdir,
        mock_glob
    ):
        mock_glob.return_value = []
        mock_Temporary_new_dir.return_value.__enter__.return_value = \
            '/tmp/keys'
        mock_urlopen.side_effect = Exception('404')
        with raises(KiwiUriOpenError) as issue:
            self.repo.import_trusted_keys(
                ['https://user:secret@example.com/key.asc']
            )
        assert 'secret' not in str(issue.value)
        assert not mock_run.called

    @patch('kiwi.repository.apt.glob.glob')
    @patch('kiwi.repository.apt.os.unlink')
    def test_delete_trusted_keys(self, mock_unlink, mock_glob):
        mock_glob.side_effect = lambda pattern: [
            pattern.replace('*', '0')
        ]
        self.repo.keyring_prefix = 'kiwi-1234-'
        self.repo.keyrings = ['/etc/apt/keyrings/kiwi-1234-0.gpg']
        self.repo.delete_trusted_keys()
        assert mock_glob.call_args_list == [
            call('/etc/apt/keyrings/kiwi-1234-*.gpg'),
            call('../data/etc/apt/keyrings/kiwi-1234-*.gpg')
        ]
        assert mock_unlink.call_args_list == [
            call('/etc/apt/keyrings/kiwi-1234-0.gpg'),
            call('../data/etc/apt/keyrings/kiwi-1234-0.gpg')
        ]
        assert self.repo.keyrings == []

    @patch('kiwi.repository.apt.Temporary.unmanaged_file')
    @patch('kiwi.repository.apt.PackageManagerTemplateAptGet')
    @patch('kiwi.repository.apt.Path.create')
    @patch('kiwi.repository.apt.os.path.exists')
    @patch('kiwi.repository.apt.os.unlink')
    def test_post_init_deletes_legacy_keyring(
        self, mock_unlink, mock_exists, mock_Path_create, mock_template,
        mock_temp
    ):
        mock_exists.return_value = True
        root_bind = mock.Mock()
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        with patch('builtins.open', create=True):
            RepositoryApt(root_bind)
        mock_unlink.assert_called_once_with('/shared-dir/apt-get/trusted.gpg')

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo(self, mock_wipe):
        self.repo.delete_repo('foo')
        assert mock_wipe.call_args_list == [
            call('/shared-dir/apt-get/sources.list.d/foo.sources'),
            call('/shared-dir/apt-get/auth.conf.d/foo.conf'),
            call('/shared-dir/apt-get/preferences.d/foo.pref')
        ]

    @patch('kiwi.path.Path.wipe')
    @patch('os.walk')
    def test_cleanup_unused_repos(self, mock_walk, mock_path):
        mock_walk.return_value = [
            ('/foo', ('bar', 'baz'), ('spam', 'eggs'))
        ]
        self.repo.repo_names = ['eggs']
        self.repo.cleanup_unused_repos()
        mock_path.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d/spam'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('kiwi.path.Path.create')
    def test_delete_all_repos(self, mock_create, mock_wipe):
        self.repo.delete_all_repos()
        assert mock_wipe.call_args_list == [
            call('/shared-dir/apt-get/sources.list.d'),
            call('/shared-dir/apt-get/auth.conf.d'),
            call('/shared-dir/apt-get/preferences.d')
        ]
        assert mock_create.call_args_list == [
            call('/shared-dir/apt-get/sources.list.d'),
            call('/shared-dir/apt-get/auth.conf.d'),
            call('/shared-dir/apt-get/preferences.d')
        ]

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo_cache(self, mock_wipe):
        self.repo.delete_repo_cache('foo')
        assert mock_wipe.call_args_list == [
            call('/shared-dir/apt-get/archives'),
            call('/shared-dir/apt-get/pkgcache.bin'),
            call('/shared-dir/apt-get/srcpkgcache.bin')
        ]

    @patch('kiwi.repository.apt.glob.glob')
    @patch('os.path.isfile')
    @patch('os.unlink')
    def test_cleanup(self, mock_os_unlink, mock_os_path_isfile, mock_glob):
        mock_glob.return_value = ['/etc/apt/keyrings/kiwi-1234-0.gpg']
        self.repo.keyring_prefix = 'kiwi-1234-'
        self.repo.cleanup()
        # keyrings in the image root are kept, see delete_trusted_keys
        mock_glob.assert_called_once_with('/etc/apt/keyrings/kiwi-1234-*.gpg')
        assert mock_os_unlink.call_args_list == [
            call('tmpfile'),
            call('/etc/apt/keyrings/kiwi-1234-0.gpg')
        ]
