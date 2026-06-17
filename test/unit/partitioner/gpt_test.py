import logging
from unittest.mock import (
    patch, call, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.partitioner.gpt import PartitionerGpt

from kiwi.exceptions import KiwiPartitionerGptFlagError


class TestPartitionerGpt:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        disk_provider = Mock()
        disk_provider.get_device = Mock(
            return_value='/dev/loop0'
        )
        self.partitioner = PartitionerGpt(disk_provider)

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.PartitionerGpt.set_flag')
    def test_create(self, mock_flag, mock_call_sfdisk):
        self.partitioner.create('name', 100, 't.linux', ['t.csm'])
        mock_call_sfdisk.assert_called_once_with(
            ['size=100MiB, name="name"'], ['--force', '-N', '1']
        )
        call = mock_flag.call_args_list[0]
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        call = mock_flag.call_args_list[1]
        assert mock_flag.call_args_list[1] == \
            call(1, 't.csm')

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.PartitionerGpt.set_flag')
    def test_create_custom_start_sector(self, mock_flag, mock_call_sfdisk):
        disk_provider = Mock()
        disk_provider.get_device = Mock(
            return_value='/dev/loop0'
        )
        partitioner = PartitionerGpt(disk_provider, 4096)
        partitioner.create('name', 100, 't.linux', ['t.csm'])
        partitioner.create('name', 100, 't.linux', ['t.csm'])
        mock_call_sfdisk.assert_has_calls([
            call(
                ['start=4096, size=100MiB, name="name"'],
                ['--force', '-N', '1']
            ),
            call(
                ['size=100MiB, name="name"'],
                ['--force', '-N', '2']
            )
        ])
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        assert mock_flag.call_args_list[1] == \
            call(1, 't.csm')

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.PartitionerGpt.set_flag')
    def test_create_all_free(self, mock_flag, mock_call_sfdisk):
        self.partitioner.create('name', 'all_free', 't.linux')
        mock_call_sfdisk.assert_called_once_with(
            ['size=+, name="name"'], ['--force', '-N', '1']
        )

    def test_set_flag_invalid(self):
        with raises(KiwiPartitionerGptFlagError):
            self.partitioner.set_flag(1, 'foo')

    @patch('kiwi.partitioner.gpt.Command.run')
    def test_set_flag(self, mock_command):
        self.partitioner.set_flag(1, 't.csm')
        mock_command.assert_called_once_with(
            [
                'sfdisk', '--part-type', '/dev/loop0', '1',
                '21686148-6449-6E6F-744E-656564454649'
            ]
        )

    def test_set_flag_ignored(self):
        with self._caplog.at_level(logging.WARNING):
            self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.PartitionerGpt._get_partition_type')
    @patch('kiwi.partitioner.gpt.PartitionerGpt._get_partition_geometry')
    def test_set_hybrid_mbr(
        self, mock_geometry, mock_type, mock_call_sfdisk
    ):
        self.partitioner.partition_id = 5
        self.partitioner.partition_count = 5
        self.partitioner.partition_map = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5
        }
        mock_geometry.side_effect = [('2048', '4096')] * 3
        mock_type.return_value = '0FC63DAF-8483-4772-8E79-3D69D8477DE4'
        self.partitioner.set_hybrid_mbr()
        mock_call_sfdisk.assert_called_once_with(
            [
                '/dev/loop0p1 : start=2048, size=4096, type=83',
                '/dev/loop0p2 : start=2048, size=4096, type=83',
                '/dev/loop0p3 : start=2048, size=4096, type=83'
            ],
            ['--label-nested=mbr']
        )

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.PartitionerGpt._get_partition_type')
    @patch('kiwi.partitioner.gpt.PartitionerGpt._get_partition_geometry')
    def test_set_mbr(self, mock_geometry, mock_type, mock_call_sfdisk):
        self.partitioner.partition_id = 4
        self.partitioner.partition_count = 4
        self.partitioner.partition_map = {
            1: 1,
            2: 2,
            3: 3,
            4: 4
        }
        mock_geometry.side_effect = [
            ('2048', '4096'),
            ('6144', '4096'),
            ('10240', '4096'),
            ('14336', '4096')
        ]
        mock_type.side_effect = [
            '0FC63DAF-8483-4772-8E79-3D69D8477DE4',
            '0657FD6D-A4AB-43C4-84E5-0933C84B4F4F',
            'E6D6D379-F507-44C2-A23C-238F2A3DF928',
            'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
        ]
        self.partitioner.set_mbr()
        mock_call_sfdisk.assert_called_once_with(
            [
                'label: dos',
                '/dev/loop0p1 : start=2048, size=4096, type=83',
                '/dev/loop0p2 : start=6144, size=4096, type=82',
                '/dev/loop0p3 : start=10240, size=4096, type=8e',
                '/dev/loop0p4 : start=14336, size=4096, type=83'
            ]
        )

    @patch('kiwi.partitioner.gpt.PartitionerGpt._call_sfdisk')
    @patch('kiwi.partitioner.gpt.Command.run')
    def test_resize_table(self, mock_command, mock_call_sfdisk):
        command_output = Mock()
        command_output.output = '\n'.join([
            'label: gpt',
            'label-id: ID',
            'device: /dev/loop0',
            'unit: sectors',
            'first-lba: 2048',
            'last-lba: 4096',
            'sector-size: 512',
            '',
            '/dev/loop0p1 : start=2048, size=1024, type=TYPE'
        ])
        mock_command.return_value = command_output
        self.partitioner.resize_table(42)
        mock_command.assert_called_once_with(
            ['sfdisk', '--dump', '/dev/loop0']
        )
        mock_call_sfdisk.assert_called_once_with(
            [
                'label: gpt',
                'label-id: ID',
                'device: /dev/loop0',
                'unit: sectors',
                'first-lba: 2048',
                'last-lba: 4096',
                'table-length: 42',
                'sector-size: 512',
                '',
                '/dev/loop0p1 : start=2048, size=1024, type=TYPE'
            ]
        )

    @patch('kiwi.partitioner.gpt.Command.run')
    def test_set_uuid(self, mock_Command_run):
        self.partitioner.set_uuid(42, 'ID')
        mock_Command_run.assert_called_once_with(
            ['sfdisk', '--part-type', '/dev/loop0', '42', 'ID']
        )
