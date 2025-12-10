from unittest.mock import (
    patch, Mock
)
from pytest import (
    fixture, raises
)

import unittest.mock as mock

from kiwi.storage.disk import ptable_entry_type
from kiwi.storage.disk import Disk
from kiwi.exceptions import (
    KiwiCustomPartitionConflictError,
)


class TestDiskCustomPartitionControl:
    """Test custom partition control feature for disk partitioning"""

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

        self.partitioner = mock.Mock()
        self.partitioner.create = mock.Mock()
        self.partitioner.set_flag = mock.Mock()
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

    def test_create_custom_partition_with_explicit_partition_number(self):
        """Test creating custom partition passes explicit partition number to partitioner"""
        self.disk.create_custom_partitions(
            {
                'root': ptable_entry_type(
                    mbsize=1024,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext3',
                    label='root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # Verify partitioner.create was called with explicit_partition_id=1
        self.partitioner.create.assert_called_once()
        call_kwargs = self.partitioner.create.call_args[1]
        assert call_kwargs.get('explicit_partition_id') == 1

    def test_create_custom_partition_without_explicit_number_custom_control_false(self):
        """Test backwards compat: no explicit partition number when custom_part_control=False"""
        self.disk.create_custom_partitions(
            {
                'var': ptable_entry_type(
                    mbsize=512,
                    clone=0,
                    partition_name='p.lxvar',
                    partition_type='t.linux',
                    mountpoint='/var',
                    filesystem='ext3',
                    label='var',
                    partition_number=None,
                    boot_flag=False
                )
            },
            custom_part_control=False
        )
        # Verify explicit_partition_id not passed (None or not in kwargs)
        self.partitioner.create.assert_called_once()
        call_kwargs = self.partitioner.create.call_args[1]
        assert call_kwargs.get('explicit_partition_id') is None

    def test_create_custom_partition_set_boot_flag(self):
        """Test boot_flag=True calls partitioner.set_flag with f.active"""
        self.disk.create_custom_partitions(
            {
                'boot': ptable_entry_type(
                    mbsize=512,
                    clone=0,
                    partition_name='p.lxboot',
                    partition_type='t.linux',
                    mountpoint='/boot',
                    filesystem='ext3',
                    label='boot',
                    partition_number=128,
                    boot_flag=True
                )
            },
            custom_part_control=True
        )
        # Verify set_flag was called with boot flag (f.active)
        set_flag_calls = [
            c for c in self.partitioner.set_flag.call_args_list
            if len(c[0]) >= 2 and c[0][1] == 'f.active'
        ]
        assert len(set_flag_calls) > 0

    def test_create_custom_partition_no_boot_flag_when_false(self):
        """Test boot_flag=False does not set boot flag"""
        self.partitioner.set_flag.reset_mock()
        self.disk.create_custom_partitions(
            {
                'root': ptable_entry_type(
                    mbsize=5000,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext3',
                    label='root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # Only type flag (t.linux) should be set, not f.active
        set_flag_calls = [
            c for c in self.partitioner.set_flag.call_args_list
            if len(c[0]) >= 2 and c[0][1] == 'f.active'
        ]
        assert len(set_flag_calls) == 0

    def test_create_custom_partition_reserved_names_allowed_with_custom_control(self):
        """Test custom_part_control=True allows reserved partition names (root, boot, efi)"""
        # Should not raise when using reserved name with custom_part_control=True
        self.disk.create_custom_partitions(
            {
                'root': ptable_entry_type(
                    mbsize=5000,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext3',
                    label='root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        self.partitioner.create.assert_called_once()

    def test_create_custom_partition_reserved_names_blocked_without_custom_control(self):
        """Test custom_part_control=False blocks reserved partition names"""
        with raises(KiwiCustomPartitionConflictError):
            self.disk.create_custom_partitions(
                {
                    'root': ptable_entry_type(
                        mbsize=5000,
                        clone=0,
                        partition_name='p.lxroot',
                        partition_type='t.linux',
                        mountpoint='/',
                        filesystem='ext3',
                        label='root',
                        partition_number=None,
                        boot_flag=False
                    )
                },
                custom_part_control=False
            )

    def test_create_custom_partition_all_reserved_names_blocked(self):
        """Test all reserved names are blocked when custom_part_control=False"""
        reserved_names = ['root', 'boot', 'efi', 'efi_csm', 'prep', 'swap', 'readonly', 'spare']
        for name in reserved_names:
            with raises(KiwiCustomPartitionConflictError):
                self.disk.create_custom_partitions(
                    {
                        name: ptable_entry_type(
                            mbsize=512,
                            clone=0,
                            partition_name=f'p.lx{name}',
                            partition_type='t.linux',
                            mountpoint=f'/{name}',
                            filesystem='ext3',
                            label=name,
                            partition_number=None,
                            boot_flag=False
                        )
                    },
                    custom_part_control=False
                )

    def test_create_custom_partition_with_partition_type_efi(self):
        """Test EFI partition type is passed to partitioner correctly"""
        self.disk.create_custom_partitions(
            {
                'efi': ptable_entry_type(
                    mbsize=100,
                    clone=0,
                    partition_name='p.UEFI',
                    partition_type='t.efi',
                    mountpoint='',
                    filesystem='vfat',
                    label='efi',
                    partition_number=127,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # Verify t.efi type is passed
        call_args = self.partitioner.create.call_args[0]
        assert call_args[2] == 't.efi'

    def test_create_custom_partition_multiple_partitions_in_order(self):
        """Test multiple partitions are created in the order provided"""
        partitions = {
            'efi': ptable_entry_type(
                mbsize=100,
                clone=0,
                partition_name='p.UEFI',
                partition_type='t.efi',
                mountpoint='',
                filesystem='vfat',
                label='efi',
                partition_number=127,
                boot_flag=False
            ),
            'boot': ptable_entry_type(
                mbsize=512,
                clone=0,
                partition_name='p.lxboot',
                partition_type='t.linux',
                mountpoint='/boot',
                filesystem='ext3',
                label='boot',
                partition_number=128,
                boot_flag=True
            ),
            'root': ptable_entry_type(
                mbsize=5000,
                clone=0,
                partition_name='p.lxroot',
                partition_type='t.linux',
                mountpoint='/',
                filesystem='ext3',
                label='root',
                partition_number=1,
                boot_flag=False
            )
        }
        self.disk.create_custom_partitions(
            partitions,
            custom_part_control=True
        )
        # Verify all three partitions were created
        assert self.partitioner.create.call_count == 3

    def test_create_custom_partition_lvm_with_explicit_number(self):
        """Test LVM partition with explicit partition number"""
        self.disk.create_custom_partitions(
            {
                'lvm_pv': ptable_entry_type(
                    mbsize=8000,
                    clone=0,
                    partition_name='p.lxlvm',
                    partition_type='t.lvm',
                    mountpoint='',
                    filesystem='',
                    label='lvm_pv',
                    partition_number=10,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        call_args = self.partitioner.create.call_args[0]
        assert call_args[2] == 't.lvm'
        call_kwargs = self.partitioner.create.call_args[1]
        assert call_kwargs.get('explicit_partition_id') == 10

    def test_create_custom_partition_raid_with_explicit_number(self):
        """Test RAID partition with explicit partition number"""
        self.disk.create_custom_partitions(
            {
                'raid_md': ptable_entry_type(
                    mbsize=3000,
                    clone=0,
                    partition_name='p.lxraid',
                    partition_type='t.raid',
                    mountpoint='',
                    filesystem='',
                    label='raid_md',
                    partition_number=20,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        call_args = self.partitioner.create.call_args[0]
        assert call_args[2] == 't.raid'
        call_kwargs = self.partitioner.create.call_args[1]
        assert call_kwargs.get('explicit_partition_id') == 20

    def test_ptable_entry_type_includes_partition_number_field(self):
        """Test ptable_entry_type has partition_number field"""
        entry = ptable_entry_type(
            mbsize=512,
            clone=0,
            partition_name='p.test',
            partition_type='t.linux',
            mountpoint='/test',
            filesystem='ext3',
            label='test',
            partition_number=5,
            boot_flag=True
        )
        assert entry.partition_number == 5
        assert entry.boot_flag is True

    def test_ptable_entry_type_partition_number_can_be_none(self):
        """Test ptable_entry_type partition_number can be None"""
        entry = ptable_entry_type(
            mbsize=512,
            clone=0,
            partition_name='p.test',
            partition_type='t.linux',
            mountpoint='/test',
            filesystem='ext3',
            label='test',
            partition_number=None,
            boot_flag=False
        )
        assert entry.partition_number is None

    def test_create_custom_partition_with_all_free_size(self):
        """Test all_free size is passed correctly to partitioner"""
        self.disk.create_custom_partitions(
            {
                'root': ptable_entry_type(
                    mbsize='all_free',
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext3',
                    label='root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        call_args = self.partitioner.create.call_args[0]
        assert call_args[1] == 'all_free'

    def test_create_custom_partition_sequential_numbering_without_custom_control(self):
        """Test sequential numbering when custom_part_control=False"""
        # Without custom_part_control, partition numbers should auto-increment
        # and explicit_partition_id should be None
        self.disk.create_custom_partitions(
            {
                'var': ptable_entry_type(
                    mbsize=1000,
                    clone=0,
                    partition_name='p.lxvar',
                    partition_type='t.linux',
                    mountpoint='/var',
                    filesystem='ext3',
                    label='var',
                    partition_number=None,
                    boot_flag=False
                ),
                'tmp': ptable_entry_type(
                    mbsize=500,
                    clone=0,
                    partition_name='p.lxtmp',
                    partition_type='t.linux',
                    mountpoint='/tmp',
                    filesystem='ext3',
                    label='tmp',
                    partition_number=None,
                    boot_flag=False
                )
            },
            custom_part_control=False
        )
        # Both should have explicit_partition_id=None
        calls = self.partitioner.create.call_args_list
        for call_obj in calls:
            assert call_obj[1].get('explicit_partition_id') is None

    def test_canonical_alias_efi_partition_by_type(self):
        """Test EFI partition creates 'efi' alias based on t.efi type"""
        self.disk.create_custom_partitions(
            {
                'custom_efi': ptable_entry_type(
                    mbsize=100,
                    clone=0,
                    partition_name='p.UEFI',
                    partition_type='t.efi',
                    mountpoint='/boot/efi',
                    filesystem='vfat',
                    label='EFI',
                    partition_number=127,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # Verify 'efi' alias is created in partition_map
        assert 'efi' in self.disk.partition_map
        assert 'custom_efi' in self.disk.partition_map
        # Both should point to the same device
        assert self.disk.partition_map['efi'] == self.disk.partition_map['custom_efi']

    def test_canonical_alias_boot_partition_by_flag(self):
        """Test boot partition creates 'boot' alias based on boot_flag=True"""
        self.disk.create_custom_partitions(
            {
                'custom_boot': ptable_entry_type(
                    mbsize=512,
                    clone=0,
                    partition_name='p.lxboot',
                    partition_type='t.linux',
                    mountpoint='/boot',
                    filesystem='ext4',
                    label='Boot',
                    partition_number=128,
                    boot_flag=True
                )
            },
            custom_part_control=True
        )
        # Verify 'boot' alias is created in partition_map
        assert 'boot' in self.disk.partition_map
        assert 'custom_boot' in self.disk.partition_map
        assert self.disk.partition_map['boot'] == self.disk.partition_map['custom_boot']

    def test_canonical_alias_root_partition_by_label(self):
        """Test root partition creates 'root' alias based on label containing 'root'"""
        self.disk.create_custom_partitions(
            {
                'custom_root': ptable_entry_type(
                    mbsize=10000,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext4',
                    label='Root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # Verify 'root' alias is created in partition_map
        assert 'root' in self.disk.partition_map
        assert 'custom_root' in self.disk.partition_map
        assert self.disk.partition_map['root'] == self.disk.partition_map['custom_root']

    def test_canonical_alias_not_created_for_existing_canonical_name(self):
        """Test no alias created when partition already uses canonical name"""
        self.disk.create_custom_partitions(
            {
                'root': ptable_entry_type(
                    mbsize=10000,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext4',
                    label='Root',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # 'root' should be in partition_map only once (the original name)
        assert 'root' in self.disk.partition_map

    def test_canonical_alias_not_created_without_custom_part_control(self):
        """Test aliases are NOT created when custom_part_control=False"""
        self.disk.create_custom_partitions(
            {
                'custom_efi': ptable_entry_type(
                    mbsize=100,
                    clone=0,
                    partition_name='p.UEFI',
                    partition_type='t.efi',
                    mountpoint='/boot/efi',
                    filesystem='vfat',
                    label='EFI',
                    partition_number=None,
                    boot_flag=False
                )
            },
            custom_part_control=False
        )
        # 'efi' alias should NOT be created when custom_part_control=False
        assert 'efi' not in self.disk.partition_map
        assert 'custom_efi' in self.disk.partition_map

    def test_canonical_alias_multiple_partitions(self):
        """Test canonical aliases are created for multiple partitions"""
        # get_id is called multiple times per partition (for _add_to_map and _add_to_public_id_map)
        self.partitioner.get_id.side_effect = [1, 1, 2, 2, 3, 3]
        self.disk.create_custom_partitions(
            {
                'my_efi': ptable_entry_type(
                    mbsize=100,
                    clone=0,
                    partition_name='p.UEFI',
                    partition_type='t.efi',
                    mountpoint='/boot/efi',
                    filesystem='vfat',
                    label='EFI',
                    partition_number=127,
                    boot_flag=False
                ),
                'my_boot': ptable_entry_type(
                    mbsize=512,
                    clone=0,
                    partition_name='p.lxboot',
                    partition_type='t.linux',
                    mountpoint='/boot',
                    filesystem='ext4',
                    label='Boot',
                    partition_number=128,
                    boot_flag=True
                ),
                'my_root': ptable_entry_type(
                    mbsize=10000,
                    clone=0,
                    partition_name='p.lxroot',
                    partition_type='t.linux',
                    mountpoint='/',
                    filesystem='ext4',
                    label='MyRoot',
                    partition_number=1,
                    boot_flag=False
                )
            },
            custom_part_control=True
        )
        # All canonical aliases should be created
        assert 'efi' in self.disk.partition_map
        assert 'boot' in self.disk.partition_map
        assert 'root' in self.disk.partition_map
        # Original names should also exist
        assert 'my_efi' in self.disk.partition_map
        assert 'my_boot' in self.disk.partition_map
        assert 'my_root' in self.disk.partition_map
