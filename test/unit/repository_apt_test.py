
from mock import patch
from mock import call

import mock

from .test_helper import *

from kiwi.repository.apt import RepositoryApt
from kiwi.system.root_bind import RootBind


class TestRepositoryApt(object):
    @patch('kiwi.repository.apt.NamedTemporaryFile')
    @patch_open
    @patch('kiwi.repository.apt.PackageManagerTemplateAptGet')
    @patch('kiwi.repository.apt.Path.create')
    def setup(self, mock_path, mock_template, mock_open, mock_temp):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

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

        self.repo = RepositoryApt(root_bind, ['exclude_docs'])

        self.exclude_docs = True
        self.apt_conf.get_host_template.assert_called_once_with(
            self.exclude_docs
        )
        template.substitute.assert_called_once_with(
            {'apt_shared_base': '/shared-dir/apt-get'}
        )

    @patch_open
    @patch('kiwi.repository.apt.NamedTemporaryFile')
    @patch('kiwi.repository.apt.Path.create')
    def test_post_init_no_custom_args(self, mock_open, mock_path, mock_temp):
        self.repo.post_init()
        assert self.repo.custom_args == []

    @patch_open
    def test_use_default_location(self, mock_open):
        template = mock.Mock()
        self.apt_conf.get_image_template.return_value = template
        self.repo.use_default_location()
        self.apt_conf.get_image_template.assert_called_once_with(
            self.exclude_docs
        )
        template.substitute.assert_called_once_with()

    def test_runtime_config(self):
        assert self.repo.runtime_config()['apt_get_args'] == \
            self.repo.apt_get_args
        assert self.repo.runtime_config()['command_env'] == \
            self.repo.command_env

    @patch('os.path.exists')
    @patch_open
    def test_add_repo_distribution(self, mock_open, mock_exists):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True
        self.repo.add_repo(
            'foo', 'kiwi_iso_mount/uri', 'deb', None, 'xenial', 'a b'
        )
        self.file_mock.write.assert_called_once_with(
            'deb file:/kiwi_iso_mount/uri xenial a b\n'
        )
        mock_open.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
        )

    @patch('os.path.exists')
    @patch_open
    def test_add_repo_distribution_default_component(
        self, mock_open, mock_exists
    ):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = True
        self.repo.add_repo(
            'foo', 'kiwi_iso_mount/uri', 'deb', None, 'xenial'
        )
        self.file_mock.write.assert_called_once_with(
            'deb file:/kiwi_iso_mount/uri xenial main\n'
        )
        mock_open.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
        )

    @patch('os.path.exists')
    @patch_open
    def test_add_repo_flat(self, mock_open, mock_exists):
        mock_open.return_value = self.context_manager_mock
        mock_exists.return_value = False
        self.repo.add_repo(
            'foo', 'http://repo.com', 'deb'
        )
        self.file_mock.write.assert_called_once_with(
            'deb http://repo.com ./\n'
        )
        mock_open.assert_called_once_with(
            '/shared-dir/apt-get/sources.list.d/foo.list', 'w'
        )

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
