import logging
from mock import patch, call
from pytest import (
    raises, fixture
)

import os

from kiwi.path import Path
from kiwi.exceptions import KiwiFileAccessError


class TestPath:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_sort_by_hierarchy(self):
        ordered = Path.sort_by_hierarchy(
            ['usr', 'usr/bin', 'etc', 'usr/lib']
        )
        assert ordered == ['usr', 'etc', 'usr/bin', 'usr/lib']

    @patch('kiwi.command.os.path.exists')
    @patch('kiwi.command.Command.run')
    def test_create(self, mock_command, mock_exists):
        mock_exists.return_value = False
        Path.create('foo')
        mock_command.assert_called_once_with(
            ['mkdir', '-p', 'foo']
        )
        mock_exists.return_value = True
        mock_command.reset_mock()
        Path.create('foo')
        assert not mock_command.called

    @patch('kiwi.command.os.path.exists')
    @patch('kiwi.command.Command.run')
    def test_wipe(self, mock_command, mock_exists):
        mock_exists.return_value = True
        Path.wipe('foo')
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'foo']
        )
        mock_exists.return_value = False
        mock_command.reset_mock()
        Path.wipe('foo')
        assert not mock_command.called

    @patch('kiwi.command.Command.run')
    def test_remove(self, mock_command):
        Path.remove('foo')
        mock_command.assert_called_once_with(
            ['rmdir', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_remove_hierarchy(self, mock_command):
        Path.remove_hierarchy('/my_root', '/tmp/foo/bar')
        with self._caplog.at_level(logging.WARNING):
            assert mock_command.call_args_list == [
                call(
                    [
                        'rmdir', '--ignore-fail-on-non-empty',
                        '/my_root/tmp/foo/bar'
                    ]
                ),
                call(
                    [
                        'rmdir', '--ignore-fail-on-non-empty',
                        '/my_root/tmp/foo'
                    ]
                )
            ]
            assert 'remove_hierarchy: path /my_root/tmp is protected' in \
                self._caplog.text
        mock_command.reset_mock()
        Path.remove_hierarchy('/home/kiwi/my_root', 'foo')
        mock_command.assert_called_once_with(
            ['rmdir', '--ignore-fail-on-non-empty', '/home/kiwi/my_root/foo']
        )

    def test_move_to_root(self):
        assert [
            '/usr/bin', '/sbin'
        ] == Path.move_to_root('/root_dir', ['/root_dir/usr/bin', '/sbin'])

    def test_rebase_to_root(self):
        assert [
            '/root_dir/usr/bin', '/root_dir/sbin'
        ] == Path.rebase_to_root('/root_dir', ['usr/bin', '/sbin'])

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which(self, mock_exists, mock_env, mock_access):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = True
        assert Path.which('some-file') == '/usr/local/bin/some-file'
        mock_exists.return_value = False
        assert Path.which('some-file') is None
        mock_env.return_value = None
        mock_exists.return_value = True
        assert Path.which('some-file', ['alternative']) == \
            'alternative/some-file'
        mock_access.return_value = False
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        assert Path.which('some-file', access_mode=os.X_OK) is None
        mock_access.return_value = True
        assert Path.which('some-file', access_mode=os.X_OK) == \
            '/usr/local/bin/some-file'
        assert Path.which('some-file', custom_env={'PATH': 'custom_path'}) == \
            'custom_path/some-file'
        assert Path.which(
            'some-file',
            custom_env={'PATH': 'custom_path'},
            root_dir='/root_dir'
        ) == '/root_dir/custom_path/some-file'

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which_not_found_log(
        self, mock_exists, mock_env, mock_access
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = False
        with self._caplog.at_level(logging.DEBUG):
            assert Path.which('file') is None
            print(self._caplog.text)
            assert (
                '"file": in paths "{0}" exists: "False" mode match: '
                'not checked'
            ).format(mock_env.return_value) in self._caplog.text

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which_not_found_for_mode_log(
        self, mock_exists, mock_env, mock_access
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = True
        mock_access.return_value = False
        with self._caplog.at_level(logging.DEBUG):
            assert Path.which('file', access_mode=os.X_OK) is None
            assert (
                '"file": in paths "{0}" exists: "True" mode match: '
                '"False"'
            ).format(mock_env.return_value) in self._caplog.text

    def test_access_invalid_mode(self):
        with raises(ValueError) as issue:
            Path.access("/some/non-existent-file/", 128)
        assert '0x80' in format(issue.value)

    def test_access_with_non_existent_file(self):
        non_existent = "/some/file/that/should/not/exist"
        with raises(KiwiFileAccessError) as issue:
            Path.access(non_existent, os.F_OK)
        assert non_existent in issue.value.message

    @patch('os.stat')
    @patch('os.access')
    def test_access_with_args(self, mock_access, mock_stat):
        mock_access.return_value = True

        fname = "arbitrary"
        mode = os.R_OK
        assert Path.access(fname, mode, effective_ids=True)

        mock_stat.assert_called_once_with(fname)
        mock_access.assert_called_once_with(fname, mode, effective_ids=True)
