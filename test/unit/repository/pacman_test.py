
from mock import (
    patch, Mock, call, mock_open
)

import os

from kiwi.repository.pacman import RepositoryPacman


class TestRepositorPacman(object):
    @patch('kiwi.repository.pacman.Temporary.new_file')
    @patch('kiwi.repository.pacman.ConfigParser')
    @patch('kiwi.repository.pacman.Path.create')
    def setup(self, mock_path, mock_config, mock_temp):
        runtime_pacman_config = Mock()
        mock_config.return_value = runtime_pacman_config
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_temp.return_value = tmpfile
        root_bind = Mock()
        root_bind.move_to_root = Mock(
            return_value=['root-moved-arguments']
        )
        root_bind.root_dir = '../data'
        root_bind.shared_location = '/shared-dir'
        with patch('builtins.open', create=True):
            self.repo = RepositoryPacman(root_bind)

            assert runtime_pacman_config.set.call_args_list == [
                call('options', 'Architecture', 'auto'),
                call('options', 'CacheDir', '/shared-dir/pacman/cache'),
                call('options', 'SigLevel', 'Never DatabaseNever'),
                call('options', 'LocalFileSigLevel', 'Never DatabaseNever'),
                call('options', 'Include', '/shared-dir/pacman/repos/*.repo')
            ]

            runtime_pacman_config.reset_mock()

            RepositoryPacman(
                root_bind, custom_args=['check_signatures']
            )

            assert runtime_pacman_config.set.call_args_list == [
                call('options', 'Architecture', 'auto'),
                call('options', 'CacheDir', '/shared-dir/pacman/cache'),
                call('options', 'SigLevel', 'Required DatabaseRequired'),
                call(
                    'options', 'LocalFileSigLevel', 'Required DatabaseRequired'
                ),
                call('options', 'Include', '/shared-dir/pacman/repos/*.repo')
            ]

    def test_runtime_config(self):
        assert self.repo.runtime_config()['pacman_args'] == \
            self.repo.pacman_args
        assert self.repo.runtime_config()['command_env'] == \
            os.environ

    @patch('kiwi.repository.pacman.ConfigParser')
    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    def test_add_local_repo_with_components(
        self, mock_Command_run, mock_exists, mock_config
    ):
        repo_config = Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.repo.add_repo(
                'foo', '/some_uri', components='core extra',
                repo_gpgcheck=False, pkg_gpgcheck=True,
                customization_script='custom_script'
            )
        m_open.assert_called_once_with(
            '/shared-dir/pacman/repos/foo.repo', 'w'
        )

        assert repo_config.add_section.call_args_list == [
            call('core'), call('extra')
        ]
        assert repo_config.set.call_args_list == [
            call('core', 'Server', 'file:///some_uri'),
            call('core', 'SigLevel', 'Required DatabaseNever'),
            call('extra', 'Server', 'file:///some_uri'),
            call('extra', 'SigLevel', 'Required DatabaseNever'),
        ]
        mock_Command_run.assert_called_once_with(
            [
                'bash', '--norc', 'custom_script',
                '/shared-dir/pacman/repos/foo.repo'
            ]
        )

    @patch('kiwi.repository.pacman.ConfigParser')
    @patch('os.path.exists')
    def test_add_repo_with_components(
        self, mock_exists, mock_config
    ):
        repo_config = Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.repo.add_repo(
                'foo', 'some_uri', components='core extra',
                repo_gpgcheck=False, pkg_gpgcheck=True
            )
        m_open.assert_called_once_with(
            '/shared-dir/pacman/repos/foo.repo', 'w'
        )

        assert repo_config.add_section.call_args_list == [
            call('core'), call('extra')
        ]
        assert repo_config.set.call_args_list == [
            call('core', 'Server', 'some_uri'),
            call('core', 'SigLevel', 'Required DatabaseNever'),
            call('extra', 'Server', 'some_uri'),
            call('extra', 'SigLevel', 'Required DatabaseNever'),
        ]

    @patch('kiwi.repository.pacman.ConfigParser')
    @patch('os.path.exists')
    def test_add_repo_without_components(
        self, mock_exists, mock_config
    ):
        repo_config = Mock()
        mock_config.return_value = repo_config
        mock_exists.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.repo.add_repo('foo', 'some_uri', pkg_gpgcheck=False)

        m_open.assert_called_once_with(
            '/shared-dir/pacman/repos/foo.repo', 'w'
        )

        assert repo_config.add_section.call_args_list == [
            call('foo')
        ]
        assert repo_config.set.call_args_list == [
            call('foo', 'Server', 'some_uri'),
            call('foo', 'SigLevel', 'Never DatabaseNever'),
        ]

    @patch('kiwi.repository.pacman.Path.create')
    def test_setup_package_database_configuration(self, mock_path_create):
        self.repo.setup_package_database_configuration()
        mock_path_create.assert_called_once_with(
            '../data/var/lib/pacman'
        )

    @patch('kiwi.repository.pacman.os.path.exists')
    @patch('kiwi.repository.pacman.Command.run')
    def test_import_trusted_keys(self, mock_cmd, mock_exists):
        exists = [True, False]
        mock_exists.side_effect = lambda x: exists.pop()
        signing_keys = ['key-file-a.asc', 'key-file-b_ID']
        self.repo.import_trusted_keys(signing_keys)
        assert mock_cmd.call_args_list == [
            call(['pacman-key', '--add', 'key-file-a.asc']),
            call(['pacman-key', '--recv-keys', 'key-file-b_ID'])
        ]

    @patch('kiwi.repository.pacman.Path')
    def test_delete_repo(self, mock_path):
        self.repo.delete_repo('foo')
        mock_path.wipe.assert_called_once_with(
            '/shared-dir/pacman/repos/foo.repo'
        )

    @patch('kiwi.repository.pacman.Path')
    def test_delete_all_repos(self, mock_path):
        self.repo.delete_all_repos()
        mock_path.wipe.assert_called_once_with('/shared-dir/pacman/repos')
        mock_path.create.assert_called_once_with('/shared-dir/pacman/repos')

    @patch('kiwi.repository.pacman.Path.wipe')
    @patch('kiwi.repository.pacman.os.walk')
    def test_cleanup_unused_repos(self, mock_os_walk, mock_wipe):
        mock_os_walk.return_value = [(
            '/shared-dir/pacman/repos',
            [],
            ['foo.repo', 'bar.repo']
        )]
        self.repo.cleanup_unused_repos()
        mock_os_walk.assert_called_once_with('/shared-dir/pacman/repos')
        assert mock_wipe.call_args_list == [
            call('/shared-dir/pacman/repos/foo.repo'),
            call('/shared-dir/pacman/repos/bar.repo')
        ]

    def test_use_default_location(self):
        self.repo.use_default_location()
        assert self.repo.shared_pacman_dir['cache-dir'] == \
            '/shared-dir/pacman/cache'
        assert self.repo.shared_pacman_dir['repos-dir'] == \
            '../data/etc/pacman.d'

    @patch('kiwi.repository.pacman.Path')
    def test_delete_repo_cache(self, mock_path):
        self.repo.delete_repo_cache('foo')
        mock_path.wipe.assert_called_once_with('/shared-dir/pacman/cache')
