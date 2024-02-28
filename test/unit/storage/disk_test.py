import logging
from unittest.mock import (
    patch, mock_open, call, Mock
)
from pytest import (
    fixture, raises
)

import unittest.mock as mock

from kiwi.storage.disk import ptable_entry_type
from kiwi.storage.disk import Disk
from kiwi.exceptions import (
    KiwiCustomPartitionConflictError,
    KiwiCommandError
)


class TestDisk:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch.object(Disk, 'get_discoverable_partition_ids')
    @patch('kiwi.storage.disk.Partitioner.new')
    @patch('kiwi.storage.disk.RuntimeConfig')
    def setup(
        self, mock_RuntimeConfig, mock_partitioner,
        mock_get_discoverable_partition_ids
    ):
        runtime_config = Mock()
        runtime_config.get_mapper_tool.return_value = 'partx'
        mock_RuntimeConfig.return_value = runtime_config
        self.tempfile = mock.Mock()
        self.tempfile.name = 'tempfile'

        self.partitioner = mock.Mock()
        self.partitioner.create = mock.Mock()
        self.partitioner.get_id = mock.Mock(
            return_value=1
        )
        mock_partitioner.return_value = self.partitioner
        self.storage_provider = mock.Mock()
        self.storage_provider.is_loop = mock.Mock(
            return_value=True
        )
        self.storage_provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        self.disk = Disk('gpt', self.storage_provider)

    @patch('kiwi.storage.disk.Partitioner.new')
    @patch('kiwi.storage.disk.RuntimeConfig')
    def setup_method(self, cls, mock_RuntimeConfig, mock_partitioner):
        self.setup()

    @patch('os.path.exists')
    def test_get_device(self, mock_exists):
        mock_exists.return_value = True
        self.disk.partition_map['root'] = '/dev/root-device'
        assert self.disk.get_device()['root'].get_device() == '/dev/root-device'

    def test_is_loop(self):
        self.disk.is_loop()
        self.storage_provider.is_loop.assert_called_once_with()

    def test_create_root_partition(self):
        self.disk.create_root_partition('100', 1)
        assert self.partitioner.create.call_args_list == [
            call('p.lxrootclone1', '100', 't.linux'),
            call('p.lxroot', '100', 't.linux')
        ]

    def test_create_root_which_is_also_boot_partition(self):
        self.disk.create_root_partition('200')
        self.partitioner.create.assert_called_once_with(
            'p.lxroot', '200', 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_BootPart'] == 1

    def test_create_root_which_is_also_read_write_partition(self):
        self.disk.public_partition_id_map['kiwi_ROPart'] = 1
        self.disk.create_root_partition('200')
        self.partitioner.create.assert_called_once_with(
            'p.lxroot', '200', 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_RWPart'] == 1

    def test_create_root_lvm_partition(self):
        self.disk.create_root_lvm_partition('100', 1)
        assert self.partitioner.create.call_args_list == [
            call('p.lxrootclone1', '100', 't.lvm'),
            call('p.lxlvm', '100', 't.lvm')
        ]
        assert self.disk.public_partition_id_map['kiwi_rootPartClone1'] == 1
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1

    def test_create_root_raid_partition(self):
        self.disk.create_root_raid_partition('100', 1)
        assert self.partitioner.create.call_args_list == [
            call('p.lxrootclone1', '100', 't.raid'),
            call('p.lxraid', '100', 't.raid')
        ]
        assert self.disk.public_partition_id_map['kiwi_rootPartClone1'] == 1
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_RaidPart'] == 1

    def test_create_root_readonly_partition(self):
        self.disk.create_root_readonly_partition('100', 1)
        assert self.partitioner.create.call_args_list == [
            call('p.lxrootclone1', '100', 't.linux'),
            call('p.lxreadonly', '100', 't.linux')
        ]
        assert self.disk.public_partition_id_map['kiwi_rootPartClone1'] == 1
        assert self.disk.public_partition_id_map['kiwi_ROPart'] == 1

    def test_create_boot_partition(self):
        self.disk.create_boot_partition('100', 1)
        assert self.partitioner.create.call_args_list == [
            call('p.lxbootclone1', '100', 't.linux'),
            call('p.lxboot', '100', 't.linux')
        ]
        assert self.disk.public_partition_id_map['kiwi_bootPartClone1'] == 1
        assert self.disk.public_partition_id_map['kiwi_BootPart'] == 1

    def test_create_efi_csm_partition(self):
        self.disk.create_efi_csm_partition('100')
        self.partitioner.create.assert_called_once_with(
            'p.legacy', '100', 't.csm'
        )
        assert self.disk.public_partition_id_map['kiwi_BiosGrub'] == 1

    def test_create_efi_partition(self):
        self.disk.create_efi_partition('100')
        self.partitioner.create.assert_called_once_with(
            'p.UEFI', '100', 't.efi'
        )
        assert self.disk.public_partition_id_map['kiwi_EfiPart'] == 1

    def test_create_spare_partition(self):
        self.disk.create_spare_partition('42')
        self.partitioner.create.assert_called_once_with(
            'p.spare', '42', 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_SparePart'] == 1

    def test_create_swap_partition(self):
        self.disk.create_swap_partition('42')
        self.partitioner.create.assert_called_once_with(
            'p.swap', '42', 't.swap'
        )
        assert self.disk.public_partition_id_map['kiwi_SwapPart'] == 1

    @patch('kiwi.storage.disk.Command.run')
    def test_create_prep_partition(self, mock_command):
        self.disk.create_prep_partition('8')
        self.partitioner.create.assert_called_once_with(
            'p.prep', '8', 't.prep'
        )
        assert self.disk.public_partition_id_map['kiwi_PrepPart'] == 1

    @patch('kiwi.storage.disk.Command.run')
    def test_create_custom_partitions(self, mock_command):
        table_entries = {
            'var': ptable_entry_type(
                mbsize='100',
                clone=2,
                partition_name='p.lxvar',
                partition_type='t.linux',
                mountpoint='/var',
                filesystem='ext3'
            )
        }
        self.disk.create_custom_partitions(table_entries)
        assert self.partitioner.create.call_args_list == [
            call('p.lxvarclone1', '100', 't.linux'),
            call('p.lxvarclone2', '100', 't.linux'),
            call('p.lxvar', '100', 't.linux')
        ]
        assert self.disk.public_partition_id_map['kiwi_varPartClone1'] == 1
        assert self.disk.public_partition_id_map['kiwi_varPartClone2'] == 1
        assert self.disk.public_partition_id_map['kiwi_VarPart'] == 1

    def test_create_custom_partitions_reserved_name(self):
        table_entries = {
            'root': ptable_entry_type(
                mbsize='100',
                clone=0,
                partition_name='p.lxroot',
                partition_type='t.linux',
                mountpoint='/',
                filesystem='ext3'
            )
        }
        with raises(KiwiCustomPartitionConflictError):
            self.disk.create_custom_partitions(table_entries)

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_efi_partition_partx(self, mock_command):
        self.disk.create_efi_partition('100')
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/loop0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_efi_partition_kpartx(self, mock_command):
        self.disk.partition_mapper = 'kpartx'
        self.disk.create_efi_partition('100')
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/mapper/loop0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_prep_partition(self, mock_command):
        self.disk.create_prep_partition('8')
        self.disk.map_partitions()
        assert self.disk.partition_map == {'prep': '/dev/loop0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_linux_dev_sda(self, mock_command):
        self.storage_provider.is_loop.return_value = False
        self.storage_provider.get_device = mock.Mock(
            return_value='/dev/sda'
        )
        self.disk.create_efi_partition('100')
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/sda1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_linux_dev_c0d0(self, mock_command):
        self.storage_provider.is_loop.return_value = False
        self.storage_provider.get_device = mock.Mock(
            return_value='/dev/c0d0'
        )
        self.disk.create_efi_partition('100')
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/c0d0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_boot_partition(self, mock_command):
        self.disk.create_boot_partition('100')
        self.disk.create_root_partition('100')
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_root_partition(self, mock_command):
        self.disk.create_root_partition('100')
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_prep_partition(self, mock_command):
        self.disk.create_prep_partition('8')
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_wipe_gpt(self, mock_command):
        self.disk.wipe()
        mock_command.assert_called_once_with(
            ['sgdisk', '--zap-all', '/dev/loop0']
        )

    @patch('kiwi.storage.disk.Command.run')
    @patch('kiwi.storage.disk.Temporary.new_file')
    def test_wipe_dasd(self, mock_temp, mock_command):
        mock_command.side_effect = Exception
        self.disk.table_type = 'dasd'
        mock_temp.return_value = self.tempfile

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk.wipe()

        m_open.return_value.write.assert_called_once_with(
            'y\n\nw\nq\n'
        )
        with self._caplog.at_level(logging.DEBUG):
            mock_command.assert_called_once_with(
                ['bash', '-c', 'cat tempfile | fdasd -f /dev/loop0']
            )

    @patch('kiwi.storage.disk.Command.run')
    def test_map_partitions_loop_partx(self, mock_command):
        self.disk.map_partitions()
        mock_command.assert_called_once_with(
            ['partx', '--add', '/dev/loop0']
        )
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_map_partitions_loop_kpartx(self, mock_command):
        self.disk.partition_mapper = 'kpartx'
        self.disk.map_partitions()
        mock_command.assert_called_once_with(
            ['kpartx', '-s', '-a', '/dev/loop0']
        )
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_map_partitions_other(self, mock_command):
        self.storage_provider.is_loop.return_value = False
        self.disk.map_partitions()
        mock_command.assert_called_once_with(
            ['partprobe', '/dev/loop0']
        )

    @patch.object(Disk, 'get_discoverable_partition_ids')
    @patch('kiwi.storage.disk.Command.run')
    def test_context_manager_exit_partx_loop_cleanup_failed(
        self, mock_command, mock_get_discoverable_partition_ids
    ):
        mock_command.side_effect = Exception
        with Disk('gpt', self.storage_provider) as disk:
            disk.is_mapped = True
            disk.partition_map = {'root': '/dev/loop0p1'}
        with self._caplog.at_level(logging.WARNING):
            mock_command.assert_called_once_with(
                ['partx', '--delete', '/dev/loop0']
            )

    @patch.object(Disk, 'get_discoverable_partition_ids')
    @patch('kiwi.storage.disk.Command.run')
    def test_context_manager_exit_dm_loop_cleanup_failed(
        self, mock_command, mock_get_discoverable_partition_ids
    ):
        mock_command.side_effect = Exception
        with Disk('gpt', self.storage_provider) as disk:
            disk.partition_mapper = 'kpartx'
            disk.is_mapped = True
            disk.partition_map = {'root': '/dev/mapper/loop0p1'}
        with self._caplog.at_level(logging.WARNING):
            mock_command.assert_called_once_with(
                ['dmsetup', 'remove', '/dev/mapper/loop0p1']
            )

    @patch.object(Disk, 'get_discoverable_partition_ids')
    @patch('kiwi.storage.disk.Command.run')
    def test_context_manager_exit_partx(
        self, mock_command, mock_get_discoverable_partition_ids
    ):
        with Disk('gpt', self.storage_provider) as disk:
            disk.is_mapped = True
            disk.partition_map = {'root': '/dev/loop0p1'}
        assert mock_command.call_args_list == [
            call(['partx', '--delete', '/dev/loop0'])
        ]

    @patch.object(Disk, 'get_discoverable_partition_ids')
    @patch('kiwi.storage.disk.Command.run')
    def test_context_manager_exit_kpartx(
        self, mock_command, mock_get_discoverable_partition_ids
    ):
        with Disk('gpt', self.storage_provider) as disk:
            disk.partition_mapper = 'kpartx'
            disk.is_mapped = True
            disk.partition_map = {'root': '/dev/mapper/loop0p1'}
        assert mock_command.call_args_list == [
            call(['dmsetup', 'remove', '/dev/mapper/loop0p1']),
            call(['kpartx', '-d', '/dev/loop0'])
        ]

    def test_get_public_partition_id_map(self):
        assert self.disk.get_public_partition_id_map() == {}

    def test_create_hybrid_mbr(self):
        self.disk.create_hybrid_mbr()
        self.partitioner.set_hybrid_mbr.assert_called_once_with()

    def test_create_mbr(self):
        self.disk.create_mbr()
        self.partitioner.set_mbr.assert_called_once_with()

    def test_set_start_sector(self):
        self.disk.set_start_sector(4096)
        self.partitioner.set_start_sector.assert_called_once_with(4096)

    def test_parse_size(self):
        (size, _) = self.disk._parse_size('100')
        assert size == '100'
        (size, clone_size) = self.disk._parse_size('all_free')
        assert size == 'all_free'
        assert clone_size == 'all_free'
        (size, clone_size) = self.disk._parse_size('clone:100:all_free')
        assert size == '100'
        assert clone_size == 'all_free'

    @patch('kiwi.storage.disk.Command.run')
    def test_get_discoverable_partition_ids(self, mock_Command_run):
        command = Mock()
        with open('../data/systemd-id128.out') as ids:
            command.output = ids.read()
        mock_Command_run.return_value = command
        assert self.disk.get_discoverable_partition_ids()['root'] == \
            '4f68bce3e8cd4db196e7fbcaf984b709'
        mock_Command_run.side_effect = KiwiCommandError('issue')
        assert self.disk.get_discoverable_partition_ids().get('root') == \
            '4f68bce3e8cd4db196e7fbcaf984b709'
