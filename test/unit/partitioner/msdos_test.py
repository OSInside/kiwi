import logging
from mock import (
    patch, call, mock_open, Mock
)
from pytest import (
    raises, fixture
)
from collections import namedtuple

from kiwi.partitioner.msdos import PartitionerMsDos

from kiwi.exceptions import KiwiPartitionerMsDosFlagError


class TestPartitionerMsDos:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        disk_provider = Mock()
        disk_provider.get_device = Mock(
            return_value='/dev/loop0'
        )
        self.partitioner = PartitionerMsDos(disk_provider)

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.NamedTemporaryFile')
    def test_create(self, mock_temp, mock_flag, mock_command):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.partitioner.create('name', 100, 't.linux', ['f.active'])

        m_open.return_value.write.assert_called_once_with(
            'n\np\n1\n\n+100M\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )
        call = mock_flag.call_args_list[0]
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        call = mock_flag.call_args_list[1]
        assert mock_flag.call_args_list[1] == \
            call(1, 'f.active')

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.NamedTemporaryFile')
    def test_create_custom_start_sector(
        self, mock_temp, mock_flag, mock_command
    ):
        disk_provider = Mock()
        disk_provider.get_device = Mock(
            return_value='/dev/loop0'
        )
        partitioner = PartitionerMsDos(disk_provider, 4096)
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            partitioner.create('name', 100, 't.linux', ['f.active'])
            partitioner.create('name', 100, 't.linux', ['f.active'])

        mock_command.assert_has_calls([
            call(['bash', '-c', 'cat tempfile | fdisk /dev/loop0']),
            call(['bash', '-c', 'cat tempfile | fdisk /dev/loop0'])
        ])
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        assert mock_flag.call_args_list[1] == \
            call(1, 'f.active')

        m_open.return_value.write.assert_has_calls([
            call('n\np\n1\n4096\n+100M\nw\nq\n'),
            call('n\np\n2\n\n+100M\nw\nq\n')
        ])

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.NamedTemporaryFile')
    def test_create_all_free(
        self, mock_temp, mock_flag, mock_command
    ):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.partitioner.create('name', 'all_free', 't.linux')

        m_open.return_value.write.assert_called_once_with(
            'n\np\n1\n\n\nw\nq\n'
        )

    def test_set_flag_invalid(self):
        with raises(KiwiPartitionerMsDosFlagError):
            self.partitioner.set_flag(1, 'foo')

    @patch('kiwi.partitioner.msdos.Command.run')
    def test_set_flag(self, mock_command):
        self.partitioner.set_flag(1, 't.linux')
        mock_command.assert_called_once_with(
            ['sfdisk', '-c', '/dev/loop0', '1', '83']
        )

    @patch('kiwi.partitioner.msdos.Command.run')
    def test_set_active(self, mock_command):
        self.partitioner.set_flag(1, 'f.active')
        mock_command.assert_called_once_with(
            ['parted', '/dev/loop0', 'set', '1', 'boot', 'on']
        )

    def test_set_flag_ignored(self):
        with self._caplog.at_level(logging.WARNING):
            self.partitioner.set_flag(1, 't.csm')

    def test_resize_table(self):
        self.partitioner.resize_table()
