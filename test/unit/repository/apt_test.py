from mock import (
    patch, call, MagicMock
)
import io
import mock

from kiwi.repository.apt import RepositoryApt


class TestRepositoryApt:
    @patch('kiwi.repository.apt.NamedTemporaryFile')
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
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'

        with patch('builtins.open', create=True):
            self.repo = RepositoryApt(root_bind, ['exclude_docs'])

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

    @patch('kiwi.repository.apt.NamedTemporaryFile')
    @patch('kiwi.repository.apt.Path.create')
    def test_post_init_no_custom_args(self, mock_path, mock_temp):
        self.repo.post_init()
        assert self.repo.custom_args == []

    @patch('kiwi.repository.apt.NamedTemporaryFile')
    @patch('kiwi.repository.apt.Path.create')
    def test_post_init_with_custom_args(self, mock_path, mock_temp):
        self.repo.post_init(['check_signatures'])
        assert self.repo.custom_args == []
        assert self.repo.unauthenticated == 'false'

    def test_use_default_location(self):
        template = mock.Mock()
        template.substitute.return_value = 'template-data'
        self.apt_conf.get_image_template.return_value = template
        self.repo.use_default_location()
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
    def test_add_repo_with_priority(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.repo.add_repo(
                'foo', '/srv/my-repo', 'deb', '42', 'xenial', 'a b'
            )
            assert mock_open.call_args_list == [
                call('/shared-dir/apt-get/sources.list.d/foo.list', 'w'),
                call('/shared-dir/apt-get/preferences.d/foo.pref', 'w')
            ]
            assert file_handle.write.call_args_list == [
                call('deb file:/srv/my-repo xenial a b\n'),
                call('Package: *\n'),
                call('Pin: origin ""\n'),
                call('Pin-Priority: 42\n')
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
                    'deb http://download.opensuse.org/repositories/'
                    'V:/A:/C/Debian_9.0/ xenial a b\n'
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
                'foo', 'kiwi_iso_mount/uri', 'deb', None, 'xenial', 'a b'
            )
            file_handle.write.assert_called_once_with(
                'deb file:/kiwi_iso_mount/uri xenial a b\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
            )

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
                'deb [trusted=yes check-valid-until=no] file:/kiwi_iso_mount/uri xenial a b\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
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
                'deb file:/kiwi_iso_mount/uri xenial main\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
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
                'deb http://repo.com ./\n'
            )
            mock_open.assert_called_once_with(
                '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
            )

    def test_import_trusted_keys(self):
        self.repo.import_trusted_keys(['key-file-a.asc', 'key-file-b.asc'])
        assert self.repo.signing_keys == ['key-file-a.asc', 'key-file-b.asc']

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo(self, mock_wipe):
        self.repo.delete_repo('foo')
        mock_wipe.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d/foo.list'
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
            '/shared-dir/apt-get/sources.list.d/spam'
        )

    @patch('kiwi.path.Path.wipe')
    @patch('kiwi.path.Path.create')
    def test_delete_all_repos(self, mock_create, mock_wipe):
        self.repo.delete_all_repos()
        mock_wipe.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d'
        )
        mock_create.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d'
        )

    @patch('kiwi.path.Path.wipe')
    def test_delete_repo_cache(self, mock_wipe):
        self.repo.delete_repo_cache('foo')
        assert mock_wipe.call_args_list == [
            call('/shared-dir/apt-get/archives'),
            call('/shared-dir/apt-get/pkgcache.bin'),
            call('/shared-dir/apt-get/srcpkgcache.bin')
        ]
