import logging
from mock import patch
from pytest import fixture
import mock

import kiwi

from kiwi.storage.setup import DiskSetup
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.defaults import Defaults


class TestDiskSetup:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
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

        mock_machine.return_value = 'ppc64'
        description = XMLDescription(
            '../data/example_ppc_disk_size_config.xml'
        )
        self.setup_ppc = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

        mock_machine.return_value = 'arm64'
        description = XMLDescription(
            '../data/example_arm_disk_size_config.xml'
        )
        self.setup_arm = DiskSetup(
            XMLState(description.load()), 'root_dir'
        )

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
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_grub2_s390x_emu(self):
        self._init_bootpart_check()
        self.setup.bootloader = 'grub2_s390x_emu'
        assert self.setup.need_boot_partition() is True

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
        self.setup.build_type_name = 'vmx'
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
        self.setup.build_type_name = 'vmx'
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
    def test_get_disksize_mbytes_volumes(self, mock_exists):
        mock_exists.side_effect = lambda path: path != 'root_dir/newfolder'
        root_size = self.size.accumulate_mbyte_file_sizes.return_value
        with self._caplog.at_level(logging.WARNING):
            assert self.setup_volumes.get_disksize_mbytes() == \
                Defaults.get_lvm_overhead_mbytes() + \
                Defaults.get_default_legacy_bios_mbytes() + \
                Defaults.get_default_efi_boot_mbytes() + \
                Defaults.get_default_boot_mbytes() + \
                root_size + \
                1024 - root_size + \
                500 + Defaults.get_min_volume_mbytes() + \
                30 + Defaults.get_min_volume_mbytes() + \
                Defaults.get_min_volume_mbytes() + \
                Defaults.get_min_volume_mbytes() + \
                Defaults.get_min_volume_mbytes()

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
            5 * Defaults.get_min_volume_mbytes()

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
        self.setup.bootloader = 'grub2_s390x_emu'
        assert self.setup.get_boot_label() == 'ZIPL'

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
