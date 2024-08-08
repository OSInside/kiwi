import logging
from unittest.mock import patch
from pytest import (
    fixture, raises
)
import unittest.mock as mock

import kiwi

from kiwi.storage.setup import DiskSetup
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.defaults import Defaults
from kiwi.storage.disk import ptable_entry_type
from kiwi.exceptions import (
    KiwiVolumeTooSmallError,
    KiwiPartitionTooSmallError
)


class TestDiskSetup:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.size = mock.Mock()
        self.size.customize = mock.Mock(
            return_value=42
        )
        self.size.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=42
        )
        kiwi.storage.setup.SystemSize = mock.Mock(
            return_value=self.size
        )

        description = XMLDescription(
            '../data/example_disk_size_config.xml'
        )
        self.setup = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_volume_config.xml'
        )
        self.setup_volumes = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_oem_volume_config.xml'
        )
        self.setup_oem_volumes = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_volume_too_small_config.xml'
        )
        self.setup_volume_too_small = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_partition_too_small_config.xml'
        )
        self.setup_partition_too_small = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_empty_vol_config.xml'
        )
        self.setup_empty_volumes = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_vol_root_config.xml'
        )
        self.setup_root_volume = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        description = XMLDescription(
            '../data/example_disk_size_partitions_config.xml'
        )
        self.setup_partitions = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        Defaults.set_platform_name('ppc64')
        description = XMLDescription(
            '../data/example_ppc_disk_size_config.xml'
        )
        self.setup_ppc = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        Defaults.set_platform_name('arm64')
        description = XMLDescription(
            '../data/example_arm_disk_size_config.xml'
        )
        self.setup_arm = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

    def setup_method(self, cls):
        self.setup()

    def test_need_boot_partition_on_request(self):
        self._init_bootpart_check()
        self.setup.bootpart_requested = True
        assert self.setup.need_boot_partition() is True
        self.setup.bootpart_requested = False
        assert self.setup.need_boot_partition() is False

    def test_need_boot_partition_mdraid(self):
        self._init_bootpart_check()
        self.setup.mdraid = True
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_lvm(self):
        self._init_bootpart_check()
        self.setup.volume_manager = 'lvm'
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_overlay(self):
        self._init_bootpart_check()
        self.setup.root_filesystem_is_overlay = True
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_btrfs(self):
        self._init_bootpart_check()
        self.setup.volume_manager = 'btrfs'
        assert self.setup.need_boot_partition() is False

    def test_need_boot_partition_xfs(self):
        self._init_bootpart_check()
        self.setup.filesystem = 'xfs'
        assert self.setup.need_boot_partition() is False

    def test_boot_partition_size(self):
        self.setup.bootpart_requested = True
        assert self.setup.boot_partition_size() == \
            Defaults.get_default_boot_mbytes()
        self.setup.bootpart_mbytes = 42
        assert self.setup.boot_partition_size() == 42

    def test_get_disksize_mbytes(self):
        self.setup.configured_size = mock.Mock()
        self.setup.configured_size.additive = False
        self.setup.configured_size.mbytes = 1024
        assert self.setup.get_disksize_mbytes() == \
            self.setup.configured_size.mbytes

    def test_get_disksize_mbytes_with_ppc_prep_partition(self):
        assert self.setup_ppc.get_disksize_mbytes() == \
            Defaults.get_default_prep_mbytes() + \
            self.size.accumulate_mbyte_file_sizes.return_value

    def test_get_disksize_mbytes_with_spare_partition(self):
        configured_spare_part_size = 42
        assert self.setup_arm.get_disksize_mbytes() == \
            configured_spare_part_size + \
            Defaults.get_default_efi_boot_mbytes() + \
            self.size.accumulate_mbyte_file_sizes.return_value

    def test_get_disksize_mbytes_configured_additive(self):
        self.setup.configured_size = mock.Mock()
        self.setup.configured_size.additive = True
        self.setup.configured_size.mbytes = 42
        root_size = self.size.accumulate_mbyte_file_sizes.return_value
        assert self.setup.get_disksize_mbytes() == \
            Defaults.get_default_legacy_bios_mbytes() + \
            Defaults.get_default_efi_boot_mbytes() + \
            Defaults.get_swapsize_mbytes() + \
            root_size + 42 + \
            200 * 1.7

    def test_get_disksize_mbytes_configured(self):
        self.setup.configured_size = mock.Mock()
        self.setup.configured_size.additive = False
        self.setup.configured_size.mbytes = 42
        with self._caplog.at_level(logging.WARNING):
            assert self.setup.get_disksize_mbytes() == \
                self.setup.configured_size.mbytes

    def test_get_disksize_mbytes_empty_volumes(self):
        assert self.setup_empty_volumes.get_disksize_mbytes() == \
            Defaults.get_lvm_overhead_mbytes() + \
            Defaults.get_default_legacy_bios_mbytes() + \
            Defaults.get_default_efi_boot_mbytes() + \
            Defaults.get_default_boot_mbytes() + \
            self.size.accumulate_mbyte_file_sizes.return_value

    @patch('os.path.exists')
    def test_get_disksize_mbytes_volume_too_small(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        with raises(KiwiVolumeTooSmallError):
            self.setup_volume_too_small.get_disksize_mbytes()

    @patch('os.path.exists')
    def test_get_disksize_mbytes_partition_too_small(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        with raises(KiwiPartitionTooSmallError):
            self.setup_partition_too_small.get_disksize_mbytes()

    @patch('os.path.exists')
    def test_get_disksize_mbytes_volumes(self, mock_exists):
        mock_exists.side_effect = lambda path: path != 'root_dir/newfolder'
        assert self.setup_volumes.get_disksize_mbytes() == 2144

    @patch('os.path.exists')
    def test_get_disksize_mbytes_partitions(self, mock_exists):
        mock_exists.side_effect = lambda path: path != 'root_dir/var/tmp'
        assert self.setup_partitions.get_disksize_mbytes() == 732

    @patch('os.path.exists')
    def test_get_disksize_mbytes_clones(self, mock_exists):
        mock_exists.side_effect = lambda path: path != 'root_dir/var/tmp'
        self.setup_partitions.custom_partitions['var'] = ptable_entry_type(
            mbsize=100,
            clone=1,
            partition_name='var',
            partition_type='t.linux',
            mountpoint='/var',
            filesystem='ext3'
        )
        assert self.setup_partitions.get_disksize_mbytes(
            root_clone=1, boot_clone=1
        ) == 842

    @patch('os.path.exists')
    def test_get_disksize_mbytes_oem_volumes(self, mock_exists):
        mock_exists.return_value = True
        root_size = self.size.accumulate_mbyte_file_sizes.return_value
        assert self.setup_oem_volumes.get_disksize_mbytes() == \
            Defaults.get_lvm_overhead_mbytes() + \
            Defaults.get_default_legacy_bios_mbytes() + \
            Defaults.get_default_efi_boot_mbytes() + \
            Defaults.get_default_boot_mbytes() + \
            root_size + \
            5 * Defaults.get_min_volume_mbytes('ext3')

    @patch('os.path.exists')
    def test_get_disksize_mbytes_root_volume(self, mock_exists):
        mock_exists.return_value = True
        root_size = self.size.accumulate_mbyte_file_sizes.return_value
        with self._caplog.at_level(logging.WARNING):
            assert self.setup_root_volume.get_disksize_mbytes() == \
                Defaults.get_lvm_overhead_mbytes() + \
                Defaults.get_default_legacy_bios_mbytes() + \
                Defaults.get_default_efi_boot_mbytes() + \
                Defaults.get_default_boot_mbytes() + \
                root_size

    def test_get_boot_label(self):
        assert self.setup.get_boot_label() == 'BOOT'

    def test_get_efi_label(self):
        assert self.setup.get_efi_label() == 'EFI'

    def test_get_default_root_label(self):
        assert self.setup.get_root_label() == 'ROOT'

    def test_get_custom_root_label(self):
        assert self.setup_ppc.get_root_label() == 'MYLABEL'

    def _init_bootpart_check(self):
        self.setup.root_filesystem_is_overlay = None
        self.setup.bootpart_requested = None
        self.setup.mdraid = None
        self.setup.volume_manager = None
        self.setup.filesystem = None
        self.setup.bootloader = None
