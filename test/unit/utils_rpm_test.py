import io
import os
from .test_helper import patch_open
from mock import (
    patch, Mock, MagicMock, call
)

from kiwi.utils.rpm import Rpm
from kiwi.defaults import Defaults


class TestRpm(object):
    def setup(self):
        self.rpm_host = Rpm()
        self.rpm_image = Rpm('root_dir')
        self.macro_file = os.sep.join(
            [
                Defaults.get_custom_rpm_macros_path(),
                Defaults.get_custom_rpm_bootstrap_macro_name()
            ]
        )

    @patch('kiwi.utils.rpm.Command.run')
    def test_expand_query(self, mock_Command_run):
        self.rpm_host.expand_query('foo')
        mock_Command_run.assert_called_once_with(
            ['rpm', '-E', 'foo']
        )
        mock_Command_run.reset_mock()
        self.rpm_image.expand_query('foo')
        mock_Command_run.assert_called_once_with(
            ['chroot', 'root_dir', 'rpm', '-E', 'foo']
        )

    @patch('kiwi.utils.rpm.Command.run')
    def test_get_query(self, mock_Command_run):
        rpmdb_call = Mock()
        rpmdb_call.output = '%_dbpath  %{_usr}/lib/sysimage/rpm'
        mock_Command_run.return_value = rpmdb_call
        assert self.rpm_host.get_query('_dbpath') == \
            '%{_usr}/lib/sysimage/rpm'
        mock_Command_run.assert_called_once_with(
            ['rpmdb', '--showrc']
        )
        mock_Command_run.reset_mock()
        assert self.rpm_image.get_query('_dbpath') == \
            '%{_usr}/lib/sysimage/rpm'
        mock_Command_run.assert_called_once_with(
            ['chroot', 'root_dir', 'rpmdb', '--showrc']
        )

    def test_set_config_value(self):
        self.rpm_host.set_config_value('key', 'value')
        assert self.rpm_host.custom_config[0] == '%key\tvalue'

    @patch('kiwi.utils.rpm.Path.wipe')
    def test_wipe_config(self, mock_Path_wipe):
        self.rpm_host.wipe_config()
        mock_Path_wipe.assert_called_once_with(
            os.sep + self.macro_file
        )
        mock_Path_wipe.reset_mock()
        self.rpm_image.wipe_config()
        mock_Path_wipe.assert_called_once_with(
            os.sep.join(['root_dir', self.macro_file])
        )

    @patch_open
    @patch('kiwi.utils.rpm.Path.create')
    def test_write_config(self, mock_Path_create, mock_open):
        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value
        self.rpm_host.set_config_value('key', 'value')
        self.rpm_host.write_config()
        mock_open.assert_called_once_with(
            os.sep + self.macro_file, 'w'
        )
        assert file_handle.write.call_args_list == [
            call('%key\tvalue\n')
        ]
        mock_open.reset_mock()
        file_handle.write.reset_mock()
        self.rpm_image.set_config_value('foo', 'bar')
        self.rpm_image.write_config()
        mock_open.assert_called_once_with(
            os.sep.join(['root_dir', self.macro_file]), 'w'
        )
        assert file_handle.write.call_args_list == [
            call('%foo\tbar\n')
        ]
