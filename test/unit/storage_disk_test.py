from mock import patch

import mock

from .test_helper import patch_open

from kiwi.storage.disk import Disk


class TestDisk(object):
    @patch('kiwi.storage.disk.Partitioner')
    @patch_open
    def setup(self, mock_open, mock_partitioner):
        self.tempfile = mock.Mock()
        self.tempfile.name = 'tempfile'
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

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

    @patch('os.path.exists')
    def test_get_device(self, mock_exists):
        mock_exists.return_value = True
        self.disk.partition_map['root'] = '/dev/root-device'
        assert self.disk.get_device()['root'].get_device() == '/dev/root-device'

    def test_is_loop(self):
        self.disk.is_loop()
        self.storage_provider.is_loop.called_once_with()

    def test_create_root_partition(self):
        self.disk.create_root_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.lxroot', 100, 't.linux'
        )

    def test_create_root_which_is_also_boot_partition(self):
        self.disk.create_root_partition(200)
        self.partitioner.create.assert_called_once_with(
            'p.lxroot', 200, 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_BootPart'] == 1

    def test_create_root_which_is_also_read_write_partition(self):
        self.disk.public_partition_id_map['kiwi_ROPart'] = 1
        self.disk.create_root_partition(200)
        self.partitioner.create.assert_called_once_with(
            'p.lxroot', 200, 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_RWPart'] == 1

    def test_create_root_lvm_partition(self):
        self.disk.create_root_lvm_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.lxlvm', 100, 't.lvm'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_RootPartVol'] == 'LVRoot'

    def test_create_root_raid_partition(self):
        self.disk.create_root_raid_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.lxraid', 100, 't.raid'
        )
        assert self.disk.public_partition_id_map['kiwi_RootPart'] == 1
        assert self.disk.public_partition_id_map['kiwi_RaidPart'] == 1

    def test_create_root_readonly_partition(self):
        self.disk.create_root_readonly_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.lxreadonly', 100, 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_ROPart'] == 1

    def test_create_boot_partition(self):
        self.disk.create_boot_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.lxboot', 100, 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_BootPart'] == 1

    def test_create_efi_csm_partition(self):
        self.disk.create_efi_csm_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.legacy', 100, 't.csm'
        )
        assert self.disk.public_partition_id_map['kiwi_BiosGrub'] == 1

    def test_create_efi_partition(self):
        self.disk.create_efi_partition(100)
        self.partitioner.create.assert_called_once_with(
            'p.UEFI', 100, 't.efi'
        )
        assert self.disk.public_partition_id_map['kiwi_EfiPart'] == 1

    def test_create_spare_partition(self):
        self.disk.create_spare_partition(42)
        self.partitioner.create.assert_called_once_with(
            'p.spare', 42, 't.linux'
        )
        assert self.disk.public_partition_id_map['kiwi_SparePart'] == 1

    @patch('kiwi.storage.disk.Command.run')
    def test_create_prep_partition(self, mock_command):
        self.disk.create_prep_partition(8)
        self.partitioner.create.assert_called_once_with(
            'p.prep', 8, 't.prep'
        )
        assert self.disk.public_partition_id_map['kiwi_PrepPart'] == 1

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_efi_partition(self, mock_command):
        self.disk.create_efi_partition(100)
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/mapper/loop0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_prep_partition(self, mock_command):
        self.disk.create_prep_partition(8)
        self.disk.map_partitions()
        assert self.disk.partition_map == {'prep': '/dev/mapper/loop0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_linux_dev_sda(self, mock_command):
        self.storage_provider.is_loop.return_value = False
        self.storage_provider.get_device = mock.Mock(
            return_value='/dev/sda'
        )
        self.disk.create_efi_partition(100)
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/sda1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_device_map_linux_dev_c0d0(self, mock_command):
        self.storage_provider.is_loop.return_value = False
        self.storage_provider.get_device = mock.Mock(
            return_value='/dev/c0d0'
        )
        self.disk.create_efi_partition(100)
        self.disk.map_partitions()
        assert self.disk.partition_map == {'efi': '/dev/c0d0p1'}
        self.disk.is_mapped = False

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_boot_partition(self, mock_command):
        self.disk.create_boot_partition(100)
        self.disk.create_root_partition(100)
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_root_partition(self, mock_command):
        self.disk.create_root_partition(100)
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_activate_boot_partition_is_prep_partition(self, mock_command):
        self.disk.create_prep_partition(8)
        self.disk.activate_boot_partition()
        self.partitioner.set_flag(1, 'f.active')

    @patch('kiwi.storage.disk.Command.run')
    def test_wipe_gpt(self, mock_command):
        self.disk.wipe()
        mock_command.assert_called_once_with(
            ['sgdisk', '--zap-all', '/dev/loop0']
        )

    @patch('kiwi.storage.disk.Command.run')
    @patch_open
    @patch('kiwi.storage.disk.NamedTemporaryFile')
    @patch('kiwi.logger.log.debug')
    def test_wipe_dasd(self, mock_debug, mock_temp, mock_open, mock_command):
        mock_command.side_effect = Exception
        self.disk.table_type = 'dasd'
        mock_temp.return_value = self.tempfile
        mock_open.return_value = self.context_manager_mock
        self.disk.wipe()
        self.file_mock.write.assert_called_once_with(
            'y\n\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdasd -f /dev/loop0']
        )
        assert mock_debug.called

    @patch('kiwi.storage.disk.Command.run')
    def test_map_partitions_loop(self, mock_command):
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

    @patch('kiwi.storage.disk.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_destructor(self, mock_log_warn, mock_command):
        self.disk.is_mapped = True
        self.disk.partition_map = {'root': '/dev/mapper/loop0p1'}
        mock_command.side_effect = Exception
        self.disk.__del__()
        mock_command.assert_called_once_with(
            ['dmsetup', 'remove', '/dev/mapper/loop0p1']
        )
        assert mock_log_warn.called
        self.disk.is_mapped = False

    def test_get_public_partition_id_map(self):
        assert self.disk.get_public_partition_id_map() == {}

    def test_create_hybrid_mbr(self):
        self.disk.create_hybrid_mbr()
        self.partitioner.set_hybrid_mbr.assert_called_once_with()

    def test_create_mbr(self):
        self.disk.create_mbr()
        self.partitioner.set_mbr.assert_called_once_with()
