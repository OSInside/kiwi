from mock import patch, call
from pytest import raises

import os

from kiwi.path import Path
from kiwi.exceptions import KiwiFileAccessError


class TestPath(object):
    def test_sort_by_hierarchy(self):
        ordered = Path.sort_by_hierarchy(
            ['usr', 'usr/bin', 'etc', 'usr/lib']
        )
        assert ordered == ['usr', 'etc', 'usr/bin', 'usr/lib']

    @patch('kiwi.command.Command.run')
    def test_create(self, mock_command):
        Path.create('foo')
        mock_command.assert_called_once_with(
            ['mkdir', '-p', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_wipe(self, mock_command):
        Path.wipe('foo')
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_remove(self, mock_command):
        Path.remove('foo')
        mock_command.assert_called_once_with(
            ['rmdir', 'foo']
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_remove_hierarchy(self, mock_log_warn, mock_command):
        Path.remove_hierarchy('/my_root/tmp/foo/bar')
        assert mock_command.call_args_list == [
            call(['rmdir', '--ignore-fail-on-non-empty', '/my_root/tmp/foo/bar']),
            call(['rmdir', '--ignore-fail-on-non-empty', '/my_root/tmp/foo'])
        ]
        mock_log_warn.assert_called_once_with(
            'remove_hierarchy: path /my_root/tmp is protected'
        )

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

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.debug')
    def test_which_not_found_log(
        self, mock_log, mock_exists, mock_env, mock_access
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = False
        assert Path.which('file') is None
        mock_log.assert_called_once_with(
            '"file": in paths "%s" exists: "False" mode match: not checked' %
            mock_env.return_value
        )

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.debug')
    def test_which_not_found_for_mode_log(
        self, mock_log, mock_exists, mock_env, mock_access
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = True
        mock_access.return_value = False
        assert Path.which('file', access_mode=os.X_OK) is None
        mock_log.assert_called_once_with(
            '"file": in paths "%s" exists: "True" mode match: "False"' %
            mock_env.return_value
        )

    def test_access_invalid_mode(self):
        with raises(ValueError) as val_err_exc:
            Path.access("/some/non-existent-file/", 128)

        assert "0x80" in str(val_err_exc)

    def test_access_with_non_existent_file(self):
        non_existent = "/some/file/that/should/not/exist"
        with raises(KiwiFileAccessError) as kfae_exc:
            Path.access(non_existent, os.F_OK)

        assert non_existent in str(kfae_exc)

    @patch('os.stat')
    @patch('os.access')
    def test_access_with_args(self, mock_access, mock_stat):
        mock_access.return_value = True

        fname = "arbitrary"
        mode = os.R_OK
        assert Path.access(fname, mode, effective_ids=True)

        mock_stat.assert_called_once_with(fname)
        mock_access.assert_called_once_with(fname, mode, effective_ids=True)
