import os
from unittest.mock import (
    patch, Mock, call, mock_open
)

from kiwi.utils.rpm import Rpm
from kiwi.defaults import Defaults


class TestRpm:
    def setup(self):
        self.rpm_host = Rpm()
        self.rpm_image = Rpm('root_dir')
        self.macro_file = os.sep.join(
            [
                Defaults.get_custom_rpm_macros_path(),
                Defaults.get_custom_rpm_bootstrap_macro_name()
            ]
        )

    def setup_method(self, cls):
        self.setup()

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

    @patch('kiwi.utils.rpm.Path.create')
    def test_write_config(self, mock_Path_create):
        self.rpm_host.set_config_value('key', 'value')

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.rpm_host.write_config()

        m_open.assert_called_once_with(
            os.sep + self.macro_file, 'w'
        )
        assert m_open.return_value.write.call_args_list == [
            call('%key\tvalue\n')
        ]

        self.rpm_image.set_config_value('foo', 'bar')

        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.rpm_image.write_config()

        m_open.assert_called_once_with(
            os.sep.join(['root_dir', self.macro_file]), 'w'
        )
        assert m_open.return_value.write.call_args_list == [
            call('%foo\tbar\n')
        ]
