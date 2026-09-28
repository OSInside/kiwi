import os
from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from kiwi.boxbuild.defaults import BoxBuildDefaults
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiBoxTargetPathError


class TestBoxBuildDefaults:
    @patch('pathlib.Path.home')
    @patch('os.path.exists')
    def test_get_box_config_file(self, mock_os_path_exists, mock_Path_home):
        mock_os_path_exists.return_value = False
        mock_Path_home.return_value.joinpath.return_value.exists.return_value = \
            False
        assert BoxBuildDefaults.get_box_config_file() == \
            Defaults.project_file('config/kiwi_boxed_plugin.yml')

    @patch('os.path.exists', lambda f: True)
    @patch.dict(os.environ, KIWI_BOXED_PLUGIN_CFG='aarchderwelt.conf')
    def test_get_box_config_file_env(self):
        assert BoxBuildDefaults.get_box_config_file() == 'aarchderwelt.conf'

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.abspath', lambda f: '/highway/to/hell.conf')
    @patch('os.path.exists', lambda f: True)
    def test_get_box_config_file_currdir(self):
        assert BoxBuildDefaults.get_box_config_file() == \
            '/highway/to/hell.conf'

    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.home')
    @patch('os.path.exists')
    def test_get_box_config_file_local_kiwi(
        self, mock_os_path_exists, mock_Path_home
    ):
        mock_os_path_exists.return_value = False
        config_path_home = Mock()
        config_path_home.exists.return_value = True
        config_path_home.as_posix.return_value = \
            '/home/zoidberg/.config/kiwi/kiwi_boxed_plugin.yml'
        mock_Path_home.return_value.joinpath.return_value = config_path_home
        assert BoxBuildDefaults.get_box_config_file() == \
            '/home/zoidberg/.config/kiwi/kiwi_boxed_plugin.yml'
        mock_Path_home.return_value.joinpath.assert_called_once_with(
            '.config/kiwi/kiwi_boxed_plugin.yml'
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.home')
    @patch('os.path.exists', lambda f: f == '/etc/kiwi_boxed_plugin.yml')
    def test_get_box_config_file_etc(self, mock_Path_home):
        mock_Path_home.return_value.joinpath.return_value.exists.return_value = \
            False
        assert BoxBuildDefaults.get_box_config_file() == \
            '/etc/kiwi_boxed_plugin.yml'

    @patch('os.path.isdir')
    def test_get_local_box_cache_dir(self, mock_os_path_isdir):
        mock_os_path_isdir.return_value = True
        with patch.dict(os.environ, {'KIWI_BOXED_CACHE_DIR': '/var/cache'}):
            assert BoxBuildDefaults.get_local_box_cache_dir() == '/var/cache'
        with patch.dict(os.environ, {'HOME': '/home/zoidberg'}, clear=True):
            assert BoxBuildDefaults.get_local_box_cache_dir() == \
                '/home/zoidberg/.kiwi_boxes'

    @patch('pathlib.Path')
    def test_create_build_target_dir(self, mock_Path):
        BoxBuildDefaults.create_build_target_dir('some')
        assert mock_Path.call_args_list == [
            call('some'),
            call('some/result.log'),
        ]
        mock_Path.side_effect = Exception('some error')
        with raises(KiwiBoxTargetPathError):
            BoxBuildDefaults.create_build_target_dir('some')
