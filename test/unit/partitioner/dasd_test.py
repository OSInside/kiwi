import logging
from pytest import fixture
from unittest.mock import (
    patch, mock_open
)

import unittest.mock as mock

from kiwi.partitioner.dasd import PartitionerDasd


class TestPartitionerDasd:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.partitioner.dasd.Command.run')
    @patch('kiwi.partitioner.dasd.Temporary.new_file')
    def setup(self, mock_temp, mock_command):
        self.tempfile = mock.Mock()
        self.tempfile.name = 'tempfile'

        mock_temp.return_value = self.tempfile

        disk_provider = mock.Mock()
        disk_provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )

        self.partitioner = PartitionerDasd(disk_provider)

    @patch('kiwi.partitioner.dasd.Command.run')
    @patch('kiwi.partitioner.dasd.Temporary.new_file')
    def setup_method(self, cls, mock_temp, mock_command):
        self.setup()

    @patch('kiwi.partitioner.dasd.Command.run')
    @patch('kiwi.partitioner.dasd.Temporary.new_file')
    def test_create(self, mock_temp, mock_command):
        mock_command.side_effect = Exception
        mock_temp.return_value = self.tempfile

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            with self._caplog.at_level(logging.DEBUG):
                self.partitioner.create('name', '100', 't.linux', ['f.active'])

        m_open.return_value.write.assert_called_once_with(
            'n\np\n\n+100M\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdasd -f /dev/loop0']
        )

    @patch('kiwi.partitioner.dasd.Command.run')
    @patch('kiwi.partitioner.dasd.Temporary.new_file')
    def test_create_all_free(self, mock_temp, mock_command):
        mock_temp.return_value = self.tempfile

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.partitioner.create('name', 'all_free', 't.linux')

        m_open.return_value.write.assert_called_once_with(
            'n\np\n\n\nw\nq\n'
        )

    def test_resize_table(self):
        self.partitioner.resize_table()
