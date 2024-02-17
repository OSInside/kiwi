import logging
from unittest.mock import (
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
        self.partitioner = PartitionerMsDos(disk_provider, 4096)
        self.partitioner_extended = PartitionerMsDos(
            disk_provider, extended_layout=True
        )

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.Temporary.new_file')
    def test_create_primary(self, mock_temp, mock_flag, mock_command):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        m_open = mock_open()

        with patch('builtins.open', m_open, create=True):
            self.partitioner._create_primary(
                'name', 100, 't.linux', ['f.active']
            )

        m_open.return_value.write.assert_called_once_with(
            'n\np\n1\n\n+101M\nw\nq\n'
        )
        call = mock_flag.call_args_list[0]
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        call = mock_flag.call_args_list[1]
        assert mock_flag.call_args_list[1] == \
            call(1, 'f.active')
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.Temporary.new_file')
    def test_create_extended(self, mock_temp, mock_flag, mock_command):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        m_open = mock_open()

        with patch('builtins.open', m_open, create=True):
            self.partitioner._create_extended('name')

        m_open.return_value.write.assert_called_once_with(
            'n\ne\n1\n\n\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.Temporary.new_file')
    def test_create_logical(self, mock_temp, mock_flag, mock_command):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        m_open = mock_open()

        with patch('builtins.open', m_open, create=True):
            self.partitioner._create_logical(
                'name', 100, 't.linux', ['f.active']
            )

        m_open.return_value.write.assert_called_once_with(
            'n\n1\n\n+100M\nw\nq\n'
        )
        call = mock_flag.call_args_list[0]
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        call = mock_flag.call_args_list[1]
        assert mock_flag.call_args_list[1] == \
            call(1, 'f.active')
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )

    @patch.object(PartitionerMsDos, '_create_primary')
    @patch.object(PartitionerMsDos, '_create_extended')
    @patch.object(PartitionerMsDos, '_create_logical')
    def test_create(
        self, mock_create_logical, mock_create_extended, mock_create_primary
    ):
        self.partitioner.create('name', 100, 't.linux')
        mock_create_primary.assert_called_once_with(
            'name', 100, 't.linux', []
        )
        mock_create_primary.reset_mock()
        self.partitioner_extended.create('name', 100, 't.linux')
        mock_create_primary.assert_called_once_with(
            'name', 100, 't.linux', []
        )
        self.partitioner_extended.partition_id = 3
        self.partitioner_extended.create('name', 100, 't.linux')
        mock_create_extended.assert_called_once_with('name')
        mock_create_logical.assert_called_once_with(
            'name', 100, 't.linux', []
        )
        mock_create_logical.reset_mock()
        self.partitioner_extended.partition_id = 7
        self.partitioner_extended.create('name', 100, 't.linux')
        mock_create_logical.assert_called_once_with(
            'name', 100, 't.linux', []
        )

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner.msdos.Temporary.new_file')
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

    @patch('kiwi.partitioner.msdos.Command.run')
    @patch('kiwi.partitioner.msdos.Temporary.new_file')
    @patch('kiwi.partitioner.msdos.BlockID')
    def test_set_start_sector(self, mock_BlockID, mock_temp, mock_Command_run):
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        m_open = mock_open()
        mock_BlockID.return_value.get_partition_count.return_value = 4
        with patch('builtins.open', m_open, create=True):
            self.partitioner.set_start_sector(4096)
        assert m_open.return_value.write.call_args_list == [
            call('d\n1\nn\np\n4096\n\nw\nq\n')
        ]
        mock_Command_run.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )
        mock_BlockID.return_value.get_partition_count.return_value = 3
        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.partitioner.set_start_sector(4096)
        assert m_open.return_value.write.call_args_list == [
            call('d\n1\nn\np\n1\n4096\n\nw\nq\n')
        ]
