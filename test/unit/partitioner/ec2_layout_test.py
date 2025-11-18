#!/usr/bin/env python3

"""
Test to verify EC2 layout partition numbering logic
"""

import unittest
from unittest.mock import Mock

from kiwi.partitioner.base import PartitionerBase


class MockDeviceProvider:
    def get_device(self):
        return '/dev/loop0'


class MockPartitioner(PartitionerBase):
    def __init__(self):
        super().__init__(MockDeviceProvider())
        self.created_partitions = []
    
    def create(self, name, mbsize, type_name, flags=None):
        is_root = name in ['p.lxroot', 'p.lxlvm', 'p.lxraid']
        partition_id = self.get_next_id(is_root)
        self.created_partitions.append((name, partition_id))
        return partition_id


class TestEC2Layout(unittest.TestCase):

    def test_normal_layout(self):
        """Test normal partition layout without EC2 mode"""
        partitioner = TestPartitioner()
        
        # Create partitions in typical order
        partitioner.create('p.UEFI', 100, 't.efi')
        partitioner.create('p.lxboot', 500, 't.linux')
        partitioner.create('p.lxroot', 'all_free', 't.linux')
        
        expected = [('p.UEFI', 1), ('p.lxboot', 2), ('p.lxroot', 3)]
        self.assertEqual(partitioner.created_partitions, expected)

    def test_ec2_layout_basic(self):
        """Test EC2 layout with root partition getting ID 1"""
        partitioner = TestPartitioner()
        partitioner.set_ec2_layout(True)
        
        # Create partitions in EC2 order (root created last but should get ID 1)
        partitioner.create('p.UEFI', 100, 't.efi')
        partitioner.create('p.lxboot', 500, 't.linux')
        partitioner.create('p.lxroot', 'all_free', 't.linux')
        
        expected = [('p.UEFI', 2), ('p.lxboot', 3), ('p.lxroot', 1)]
        self.assertEqual(partitioner.created_partitions, expected)

    def test_ec2_layout_complex(self):
        """Test EC2 layout with multiple partitions"""
        partitioner = TestPartitioner()
        partitioner.set_ec2_layout(True)
        
        # Create partitions: EFI, boot, swap, root
        partitioner.create('p.UEFI', 100, 't.efi')
        partitioner.create('p.lxboot', 500, 't.linux')
        partitioner.create('p.swap', 1024, 't.swap')
        partitioner.create('p.lxroot', 'all_free', 't.linux')
        
        expected = [('p.UEFI', 2), ('p.lxboot', 3), ('p.swap', 4), ('p.lxroot', 1)]
        self.assertEqual(partitioner.created_partitions, expected)

    def test_ec2_layout_lvm_root(self):
        """Test EC2 layout with LVM root partition"""
        partitioner = TestPartitioner()
        partitioner.set_ec2_layout(True)
        
        partitioner.create('p.UEFI', 100, 't.efi')
        partitioner.create('p.lxlvm', 'all_free', 't.lvm')  # LVM root should get ID 1
        
        expected = [('p.UEFI', 2), ('p.lxlvm', 1)]
        self.assertEqual(partitioner.created_partitions, expected)

    def test_ec2_layout_raid_root(self):
        """Test EC2 layout with RAID root partition"""
        partitioner = TestPartitioner()
        partitioner.set_ec2_layout(True)
        
        partitioner.create('p.UEFI', 100, 't.efi')
        partitioner.create('p.lxraid', 'all_free', 't.raid')  # RAID root should get ID 1
        
        expected = [('p.UEFI', 2), ('p.lxraid', 1)]
        self.assertEqual(partitioner.created_partitions, expected)

    def test_reserved_ids_tracking(self):
        """Test that reserved IDs are properly tracked"""
        partitioner = TestPartitioner()
        partitioner.set_ec2_layout(True)
        
        # Verify that ID 1 is reserved
        self.assertIn(1, partitioner.reserved_ids)
        
        # Create non-root partition - should skip ID 1
        partitioner.create('p.UEFI', 100, 't.efi')
        self.assertEqual(partitioner.created_partitions[0][1], 2)


if __name__ == '__main__':
    unittest.main()
