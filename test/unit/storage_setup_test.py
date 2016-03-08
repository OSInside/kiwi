from nose.tools import *
from mock import patch

import mock

from . import nose_helper

import kiwi

from kiwi.exceptions import *
from kiwi.storage.setup import DiskSetup
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription


class TestDiskSetup(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        size.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=42
        )
        kiwi.storage.setup.SystemSize = mock.Mock(
            return_value=size
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

    def test_need_boot_partition_on_request(self):
        self.__init_bootpart_check()
        self.setup.bootpart_requested = True
        assert self.setup.need_boot_partition() is True
        self.setup.bootpart_requested = False
        assert self.setup.need_boot_partition() is False

    def test_need_boot_partition_mdraid(self):
        self.__init_bootpart_check()
        self.setup.mdraid = True
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_luks(self):
        self.__init_bootpart_check()
        self.setup.luks = True
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_lvm(self):
        self.__init_bootpart_check()
        self.setup.volume_manager = 'lvm'
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_btrfs(self):
        self.__init_bootpart_check()
        self.setup.filesystem = 'btrfs'
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_xfs(self):
        self.__init_bootpart_check()
        self.setup.filesystem = 'xfs'
        assert self.setup.need_boot_partition() is True

    def test_need_boot_partition_grub2_s390x_emu(self):
        self.__init_bootpart_check()
        self.setup.bootloader = 'grub2_s390x_emu'
        assert self.setup.need_boot_partition() is True

    def test_boot_partition_size(self):
        self.setup.bootpart_requested = True
        assert self.setup.boot_partition_size() == 200
        self.setup.bootpart_mbytes = 42
        assert self.setup.boot_partition_size() == 42

    def test_get_disksize_mbytes(self):
        self.setup.configured_size = mock.Mock()
        self.setup.configured_size.additive = False
        self.setup.configured_size.mbytes = 1024
        assert self.setup.get_disksize_mbytes() == 1024

    def test_get_disksize_mbytes_with_ppc_prep_partition(self):
        assert self.setup_ppc.get_disksize_mbytes() == 250

    def test_get_disksize_mbytes_configured_additive(self):
        self.setup.configured_size = mock.Mock()
        self.setup.build_type_name = 'vmx'
        self.setup.configured_size.additive = True
        self.setup.configured_size.mbytes = 42
        assert self.setup.get_disksize_mbytes() == 784 + 42

    @patch('kiwi.logger.log.warning')
    def test_get_disksize_mbytes_configured(self, mock_log_warn):
        self.setup.configured_size = mock.Mock()
        self.setup.build_type_name = 'vmx'
        self.setup.configured_size.additive = False
        self.setup.configured_size.mbytes = 42
        assert self.setup.get_disksize_mbytes() == 42
        assert mock_log_warn.called

    def test_get_disksize_mbytes_empty_volumes(self):
        assert self.setup_empty_volumes.get_disksize_mbytes() == 444

    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_get_disksize_mbytes_volumes(self, mock_log_warn, mock_exists):
        mock_exists.return_value = True
        assert self.setup_volumes.get_disksize_mbytes() == 2076
        assert mock_log_warn.called

    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_get_disksize_mbytes_root_volume(self, mock_log_warn, mock_exists):
        mock_exists.return_value = True
        assert self.setup_root_volume.get_disksize_mbytes() == 444
        assert mock_log_warn.called

    def test_get_boot_label(self):
        assert self.setup.get_boot_label() == 'BOOT'
        self.setup.bootloader = 'grub2_s390x_emu'
        assert self.setup.get_boot_label() == 'ZIPL'

    def test_get_efi_label(self):
        assert self.setup.get_efi_label() == 'EFI'

    def test_get_root_label(self):
        assert self.setup.get_root_label() == 'ROOT'

    def __init_bootpart_check(self):
        self.setup.bootpart_requested = None
        self.setup.mdraid = None
        self.setup.volume_manager = None
        self.setup.filesystem = None
        self.setup.bootloader = None
