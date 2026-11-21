import logging
import sys
from unittest.mock import call, patch, mock_open, Mock, MagicMock, ANY
from pytest import raises, fixture
import kiwi.builder.disk

from ..test_helper import argv_kiwi_tests

from collections import OrderedDict
from collections import namedtuple
from types import SimpleNamespace
from builtins import bytes

from kiwi.defaults import Defaults
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.builder.disk import DiskBuilder
from kiwi.storage.disk import ptable_entry_type
from kiwi.storage.mapped_device import MappedDevice
from kiwi.partitioner.gpt import PartitionerGpt
from kiwi.xml_state import DracutT
from kiwi.utils.reproducible import Reproducible
from kiwi.storage.repart import (
    SystemdRepart,
    RepartPartition,
    RepartBtrfsLayout,
)
from kiwi.xml_state import volume_type

from kiwi.exceptions import (
    KiwiDiskBuilderRepartError,
    KiwiDiskBootImageError,
    KiwiInstallMediaError,
    KiwiVolumeManagerSetupError,
)


class TestDiskBuilder:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_exists):
        Defaults.set_platform_name('x86_64')

        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            else:
                return True

        mock_exists.side_effect = side_effect
        description = XMLDescription('../data/example_disk_config.xml')
        self.device_map = {
            'root': MappedDevice('/dev/root-device', Mock()),
            'swap': MappedDevice('/dev/swap-device', Mock()),
            'readonly': MappedDevice('/dev/readonly-root-device', Mock()),
            'boot': MappedDevice('/dev/boot-device', Mock()),
            'prep': MappedDevice('/dev/prep-device', Mock()),
            'efi': MappedDevice('/dev/efi-device', Mock()),
            'spare': MappedDevice('/dev/spare-device', Mock()),
            'var': MappedDevice('/dev/spare-device', Mock()),
        }
        self.id_map = {'kiwi_RootPart': 1, 'kiwi_BootPart': 1}
        self.id_map_sorted = OrderedDict(sorted(self.id_map.items()))
        self.boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
        self.block_operation = Mock()
        self.block_operation.get_blkid = Mock(return_value='blkid_result')
        self.block_operation.get_filesystem = Mock(
            return_value='blkid_result_fs'
        )
        kiwi.builder.disk.BlockID = Mock(return_value=self.block_operation)
        kernel_info = Mock()
        kernel_info.version = '1.2.3'
        kernel_info.name = 'vmlinuz-1.2.3-default'
        self.kernel = Mock()
        self.kernel.get_kernel = Mock(return_value=kernel_info)
        self.kernel.get_xen_hypervisor = Mock()
        self.kernel.copy_kernel = Mock()
        self.kernel.copy_xen_hypervisor = Mock()
        kiwi.builder.disk.Kernel = Mock(return_value=self.kernel)
        # no directory of the root tree is created on the test host
        kiwi.builder.disk.Path = Mock()
        kiwi.builder.disk.MountManager = MagicMock()
        self.disk_setup = Mock()
        self.disk_setup.get_disksize_mbytes.return_value = 1024
        self.disk_setup.boot_partition_size.return_value = 0
        self.disk_setup.get_efi_label = Mock(return_value='EFI')
        self.disk_setup.get_root_label = Mock(return_value='ROOT')
        self.disk_setup.get_boot_label = Mock(return_value='BOOT')
        self.disk_setup.need_boot_partition = Mock(return_value=True)
        self.bootloader_install = Mock()
        kiwi.builder.disk.BootLoaderInstall.new = MagicMock(
            return_value=self.bootloader_install
        )
        self.bootloader_config = Mock()
        self.bootloader_config.use_disk_password = True
        self.bootloader_config.get_boot_cmdline = Mock(
            return_value='boot_cmdline'
        )
        kiwi.builder.disk.create_boot_loader_config = MagicMock(
            return_value=self.bootloader_config
        )
        kiwi.builder.disk.DiskSetup = MagicMock(return_value=self.disk_setup)
        self.runtime_config = Mock()
        kiwi.builder.disk.RuntimeConfig = MagicMock(
            return_value=self.runtime_config
        )
        self.boot_image_task = Mock()
        self.boot_image_task.boot_root_directory = 'boot_dir'
        self.boot_image_task.kernel_filename = 'kernel'
        self.boot_image_task.initrd_filename = 'initrd'
        self.boot_image_task.xen_hypervisor_filename = 'xen_hypervisor'
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='linux.vmx', initrd_name='initrd.vmx'
        )
        kiwi.builder.disk.BootImage.new = Mock(
            return_value=self.boot_image_task
        )
        self.firmware = Mock()
        self.firmware.get_legacy_bios_partition_size.return_value = 0
        self.firmware.get_efi_partition_size.return_value = 0
        self.firmware.get_prep_partition_size.return_value = 0
        self.firmware.efi_mode = Mock(return_value='efi')
        kiwi.builder.disk.FirmWare = Mock(return_value=self.firmware)
        self.setup = Mock()
        kiwi.builder.disk.SystemSetup = Mock(return_value=self.setup)
        self.install_image = Mock()
        kiwi.builder.disk.InstallImageBuilder = Mock(
            return_value=self.install_image
        )
        self.raid_root = Mock()
        self.raid_root.get_device.return_value = MappedDevice(
            '/dev/md0', Mock()
        )
        kiwi.builder.disk.RaidDevice = Mock(return_value=self.raid_root)
        self.integrity_root = Mock()
        self.integrity_root.get_device.return_value = MappedDevice(
            '/dev/integrityRoot', Mock()
        )
        kiwi.builder.disk.IntegrityDevice = Mock(
            return_value=self.integrity_root
        )
        self.luks_root = Mock()
        self.luks_root.passphrase = 'passphrase'
        kiwi.builder.disk.LuksDevice = Mock(return_value=self.luks_root)
        self.fstab = Mock()
        kiwi.builder.disk.Fstab = Mock(return_value=self.fstab)
        self.xml_state = XMLState(description.load())
        self.disk_builder = DiskBuilder(
            self.xml_state,
            'target_dir',
            'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']},
        )
        self.disk_builder.bundle_format = '%N'
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.build_type_name = 'oem'
        self.disk_builder.image_format = None

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def test_setup_warn_no_initrd_support(self):
        self.boot_image_task.has_initrd_support = Mock(return_value=False)
        with self._caplog.at_level(logging.WARNING):
            DiskBuilder(self.xml_state, 'target_dir', 'root_dir')

    def test_setup_ix86(self):
        Defaults.set_platform_name('i686')
        description = XMLDescription('../data/example_disk_config.xml')
        disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        assert disk_builder.arch == 'ix86'

    @patch('kiwi.xml_parse.type_.get_efimountoptions')
    def test_write_generic_fstab_efi_mount_options(
        self, mock_get_efimountoptions
    ):
        mock_get_efimountoptions.return_value = 'umask=0077,shortname=winnt'
        description = XMLDescription('../data/example_disk_config.xml')
        disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        assert disk_builder.custom_efi_mount_args == [
            'umask=0077,shortname=winnt'
        ]
        disk_builder.fstab = Mock()
        disk_builder.volume_manager_name = None
        setup = Mock()
        disk_builder._write_generic_fstab(
            {'root': self.device_map['root'], 'efi': self.device_map['efi']},
            setup,
            None,
        )
        assert (
            call(
                'UUID=blkid_result /boot/efi blkid_result_fs '
                'umask=0077,shortname=winnt 0 0'
            )
            in disk_builder.fstab.add_entry.call_args_list
        )
        setup.create_fstab.assert_called_once_with(disk_builder.fstab)

    @patch('kiwi.builder.disk.Disk')
    def test_disk_instance_apply_dps_codes(self, mock_Disk):
        loop_provider = Mock()
        # the example description does not request the DPS type codes
        self.disk_builder._disk_instance(loop_provider)
        assert mock_Disk.call_args.kwargs['apply_dps_codes'] is False
        self.disk_builder.apply_dps_codes = True
        self.disk_builder._disk_instance(loop_provider)
        assert mock_Disk.call_args.kwargs['apply_dps_codes'] is True

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_invalid_type_for_install_media(self, mock_cmd, mock_fs):
        self.disk_builder.build_type_name = 'kis'
        with patch('builtins.open'):
            with raises(KiwiInstallMediaError):
                self.disk_builder.create_disk()

    def test_create_disk_overlay_with_volume_setup_not_supported(self):
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.volume_manager_name = 'lvm'
        with raises(KiwiVolumeManagerSetupError):
            self.disk_builder.create_disk()

    @patch('kiwi.builder.disk.InstallImageBuilder')
    def test_create_install_media(self, mock_install_image):
        result_instance = Mock()
        mock_install_image.return_value = self.install_image
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.install_iso = True
        self.disk_builder.install_pxe = True

        self.disk_builder.create_install_media(result_instance)

        self.install_image.create_install_iso.assert_called_once_with()
        self.install_image.create_install_pxe_archive.assert_called_once_with()
        mock_install_image.assert_called_once_with(
            ANY,
            'root_dir',
            'target_dir',
            None,
            {'signing_keys': ['key_file_a', 'key_file_b']},
        )

    @patch('kiwi.builder.disk.InstallImageBuilder')
    def test_create_install_mediai_custom_boot(self, mock_install_image):
        result_instance = Mock()
        mock_install_image.return_value = self.install_image
        self.disk_builder.initrd_system = 'kiwi'
        self.disk_builder.install_pxe = True

        self.disk_builder.create_install_media(result_instance)

        self.install_image.create_install_pxe_archive.assert_called_once_with()
        mock_install_image.assert_called_once_with(
            ANY,
            'root_dir',
            'target_dir',
            ANY,
            {'signing_keys': ['key_file_a', 'key_file_b']},
        )

    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('os.path.exists')
    def test_create_disk_standard_root_with_kiwi_initrd(
        self,
        mock_path,
        mock_ImageSystem,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_LoopDevice,
        mock_Disk,
        mock_create_boot_loader_config,
    ):
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        mock_path.return_value = True
        mock_rand.return_value = 15

        filesystem = MagicMock()
        mock_fs.return_value = filesystem

        self.firmware.get_legacy_bios_partition_size.return_value = 2
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'kiwi'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        self.setup.create_recovery_archive.assert_called_once_with()

        call = self.setup.export_modprobe_setup.call_args_list[0]
        assert self.setup.export_modprobe_setup.call_args_list[0] == call(
            'boot_dir'
        )

        self.disk_setup.get_disksize_mbytes.assert_called_once_with(
            root_clone=0, boot_clone=0
        )
        loop_provider.create.assert_called_once_with()
        disk.wipe.assert_called_once_with()
        disk.create_efi_csm_partition.assert_called_once_with(
            self.firmware.get_legacy_bios_partition_size(), None
        )
        disk.create_efi_partition.assert_called_once_with(
            self.firmware.get_efi_partition_size(), None
        )
        disk.create_boot_partition.assert_called_once_with(
            format(self.disk_setup.boot_partition_size()), 0, None
        )
        disk.create_swap_partition.assert_called_once_with('128')
        disk.create_prep_partition.assert_called_once_with(
            self.firmware.get_prep_partition_size()
        )
        disk.create_root_partition.assert_called_once_with('all_free', 0, None)
        disk.map_partitions.assert_called_once_with()
        bootloader_config.setup_disk_boot_images.assert_called_once_with(
            '0815', '0815'
        )
        bootloader_config.write_meta_data.assert_called_once_with(
            root_device='/dev/readonly-root-device',
            write_device='/dev/root-device',
            boot_options='',
        )
        bootloader_config.setup_disk_image_config.assert_called_once_with(
            boot_options={
                'device_map': self.device_map,
                'boot_image': self.boot_image_task,
                'boot_device': '/dev/boot-device',
                'root_device': '/dev/readonly-root-device',
                'write_device': '/dev/root-device',
                'firmware': self.firmware,
                'target_removable': None,
                'efi_device': '/dev/efi-device',
                'prep_device': '/dev/prep-device',
                'install_options': [],
                'shim_options': [],
            }
        )
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device',
        )

        self.boot_image_task.prepare.assert_called_once_with()

        call = (
            filesystem.__enter__.return_value.create_on_device.call_args_list[0]
        )
        assert (
            filesystem.__enter__.return_value.create_on_device.call_args_list[0]
            == call(label='EFI')
        )
        call = (
            filesystem.__enter__.return_value.create_on_device.call_args_list[1]
        )
        assert (
            filesystem.__enter__.return_value.create_on_device.call_args_list[1]
            == call(label='BOOT')
        )

        call = filesystem.create_on_device.call_args_list[0]
        assert filesystem.create_on_device.call_args_list[0] == call(
            label='ROOT'
        )

        call = filesystem.__enter__.return_value.sync_data.call_args_list[0]
        assert (
            filesystem.__enter__.return_value.sync_data.call_args_list[0]
            == call()
        )
        call = filesystem.__enter__.return_value.sync_data.call_args_list[1]
        assert filesystem.__enter__.return_value.sync_data.call_args_list[
            1
        ] == call(['efi/*'])
        call = filesystem.sync_data.call_args_list[0]
        assert filesystem.sync_data.call_args_list[0] == call(
            [
                'image',
                '.kconfig',
                'run/*',
                'tmp/*',
                '.buildenv',
                'var/cache/kiwi',
                'boot/*',
                'boot/.*',
                'boot/efi/*',
                'boot/efi/.*',
            ]
        )
        assert m_open.call_args_list[0:4] == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('boot_dir/config.bootoptions', 'w'),
            call('/dev/some-loop', 'wb'),
        ]
        assert m_open.return_value.write.call_args_list == [
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n'),
            call('0x0f0f0f0f\n'),
            call('boot_cmdline\n'),
            call(bytes(b'\x0f\x0f\x0f\x0f')),
        ]
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initrd.vmx']),
        ]
        self.block_operation.get_blkid.assert_has_calls([call('PARTUUID')])
        self.setup.export_package_list.assert_called_once_with('target_dir')
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.VolumeManager.new')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('kiwi.builder.disk.CloneDevice')
    def test_create_lvm_disk_standard_root_with_clone(
        self,
        mock_CloneDevice,
        mock_Temporary_new_file,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_volume_manager,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        filesystem = Mock()
        filesystem.filename = ''
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.custom_partitions = {
            'var': ptable_entry_type(
                mbsize=100,
                clone=1,
                partition_name='p.lxvar',
                partition_type='t.linux',
                partition_id=None,
                mountpoint='/var',
                filesystem='ext3',
                label='var',
            )
        }
        volume_manager = Mock()
        volume_manager.get_device = Mock(
            return_value={
                'root': MappedDevice('/dev/systemVG/LVRoot', Mock()),
                'swap': MappedDevice('/dev/systemVG/LVSwap', Mock()),
            }
        )
        volume_manager.get_fstab = Mock(return_value=['fstab_volume_entries'])
        mock_volume_manager.return_value = volume_manager
        self.disk_builder.root_clone_count = 1
        self.disk_builder.boot_clone_count = 1
        self.disk_builder.volume_manager_name = 'lvm'
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.initrd_system = 'dracut'
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        self.device_map['rootclone1'] = MappedDevice('/dev/root-device', Mock())
        self.device_map['bootclone1'] = MappedDevice('/dev/boot-device', Mock())
        self.device_map['varclone1'] = MappedDevice('/dev/var-device', Mock())
        # Test in lvm mode (no root overlay)
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()
        volume_manager.umount_volumes.call_args_list[
            0
        ].assert_called_once_with()

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('kiwi.builder.disk.CloneDevice')
    def test_create_disk_standard_root_with_clone(
        self,
        mock_CloneDevice,
        mock_Temporary_new_file,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        filesystem = Mock()
        filesystem.filename = ''
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.custom_partitions = {
            'var': ptable_entry_type(
                mbsize=100,
                clone=1,
                partition_name='p.lxvar',
                partition_type='t.linux',
                partition_id=None,
                mountpoint='/var',
                filesystem='ext3',
                label='var',
            )
        }
        self.disk_builder.root_clone_count = 1
        self.disk_builder.boot_clone_count = 1
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        self.device_map['rootclone1'] = MappedDevice('/dev/root-device', Mock())
        self.device_map['bootclone1'] = MappedDevice('/dev/boot-device', Mock())
        self.device_map['varclone1'] = MappedDevice('/dev/var-device', Mock())

        # Test in standard mode (no root overlay)
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        disk.create_boot_partition.assert_called_once_with(
            format(self.disk_setup.boot_partition_size()), 1, None
        )
        disk.create_root_partition.assert_called_once_with(
            'clone:443:443', 1, None
        )
        disk.create_custom_partitions.assert_called_once_with(
            self.disk_builder.custom_partitions
        )
        assert mock_CloneDevice.return_value.clone.call_args_list == [
            call([self.device_map['varclone1']]),
            call([self.device_map['bootclone1']]),
            call([self.device_map['rootclone1']]),
        ]

        # Test in spare part mode
        self.disk_builder.spare_part_mbsize = 42
        self.disk_builder.spare_part_is_last = True
        disk.create_root_partition.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        disk.create_root_partition.assert_called_once_with(
            'clone:422:422', 1, None
        )

        # Test in overlay mode a root clone is created from
        # the root readonly partition and not from the root (rw)
        # partition.
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.spare_part_mbsize = None
        self.disk_builder.spare_part_is_last = False
        disk.create_root_partition.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        disk.create_root_readonly_partition.assert_called_once_with(10, 1)
        disk.create_root_partition.assert_called_once_with('all_free', 0, None)

        # Test in verity mode
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_is_overlay = False
        mock_CloneDevice.reset_mock()
        disk.create_root_partition.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        filesystem.create_verity_layer.assert_called_once_with(10, 'tempfile')
        assert mock_CloneDevice.return_value.clone.call_args_list == [
            call([self.device_map['varclone1']]),
            call([self.device_map['bootclone1']]),
            call([self.device_map['rootclone1']]),
        ]

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.Temporary.new_file')
    def test_create_disk_standard_root_with_dm_integrity(
        self,
        mock_Temporary_new_file,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        filesystem = MagicMock()
        mock_fs.return_value = filesystem
        self.disk_builder.integrity = True
        self.disk_builder.integrity_legacy_hmac = True
        self.disk_builder.root_filesystem_embed_integrity_metadata = True
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        self.integrity_root.create_integritytab.assert_called_once_with(
            'root_dir/etc/integritytab'
        )
        self.integrity_root.create_integrity_metadata.assert_called_once_with()
        self.integrity_root.sign_integrity_metadata.assert_called_once_with()
        self.integrity_root.write_integrity_metadata.assert_called_once_with()
        assert (
            filesystem.__enter__.return_value.create_on_device.call_args_list
            == [call(label='EFI'), call(label='BOOT'), call(label='SWAP')]
        )
        assert filesystem.create_on_device.call_args_list == [
            # root must be created DM_METADATA_OFFSET smaller
            call(label='ROOT', size=-4096, unit='b')
        ]

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.VeritySetup')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('kiwi.builder.disk.BlockID')
    @patch('os.access')
    def test_create_disk_standard_root_with_dracut_initrd_readonly_root_squashfs(
        self,
        mock_os_access,
        mock_BlockID,
        mock_Temporary_new_file,
        mock_VeritySetup,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_LoopDevice,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_BlockID.return_value.get_filesystem.return_value = 'squashfs'
        mock_BlockID.return_value.get_blkid.return_value = 'some'
        mock_os_access.return_value = False
        system = Mock()
        system.mountpoint.return_value = 'diskroot'
        mock_ImageSystem.return_value.__enter__.return_value = system
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        mock_rand.return_value = 15
        filesystem = MagicMock()
        mock_fs.return_value = filesystem
        self.firmware.get_legacy_bios_partition_size.return_value = 2
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_embed_verity_metadata = True
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.bootloader = 'systemd_boot'
        self.setup.script_exists.return_value = True
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        print(mock_command.call_args_list)
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(['blockdev', '--getsize64', '/dev/root-device']),
            call(['dd', 'if=tempfile', 'of=/dev/root-device']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(
                [
                    'cp',
                    'root_dir/boot/initramfs-1.2.3.img',
                    'diskroot/boot/efi/os/initramfs-1.2.3.img',
                ]
            ),
        ]

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.VeritySetup')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('kiwi.builder.disk.BlockID')
    @patch('os.access')
    def test_create_disk_standard_root_with_dracut_initrd_readonly_root_erofs(
        self,
        mock_os_access,
        mock_BlockID,
        mock_Temporary_new_file,
        mock_VeritySetup,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_LoopDevice,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_BlockID.return_value.get_filesystem.return_value = 'erofs'
        mock_BlockID.return_value.get_blkid.return_value = 'some'
        mock_os_access.return_value = False
        system = Mock()
        system.mountpoint.return_value = 'diskroot'
        mock_ImageSystem.return_value.__enter__.return_value = system
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        mock_rand.return_value = 15
        filesystem = MagicMock()
        mock_fs.return_value = filesystem
        self.firmware.get_legacy_bios_partition_size.return_value = 2
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_embed_verity_metadata = True
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.bootloader = 'systemd_boot'
        self.setup.script_exists.return_value = True
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        print(mock_command.call_args_list)
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(['blockdev', '--getsize64', '/dev/root-device']),
            call(['dd', 'if=tempfile', 'of=/dev/root-device']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(
                [
                    'cp',
                    'root_dir/boot/initramfs-1.2.3.img',
                    'diskroot/boot/efi/os/initramfs-1.2.3.img',
                ]
            ),
        ]

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.VeritySetup')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('os.access')
    def test_create_disk_standard_root_with_dracut_initrd(
        self,
        mock_os_access,
        mock_Temporary_new_file,
        mock_VeritySetup,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_LoopDevice,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_os_access.return_value = True
        system = Mock()
        system.mountpoint.return_value = 'diskroot'
        mock_ImageSystem.return_value.__enter__.return_value = system
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img',
        )
        mock_path.return_value = True
        mock_rand.return_value = 15
        filesystem = MagicMock()
        mock_fs.return_value = filesystem
        self.firmware.get_legacy_bios_partition_size.return_value = 2
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_embed_verity_metadata = True
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        self.setup.script_exists.return_value = True
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        self.setup.create_recovery_archive.assert_called_once_with()
        self.disk_setup.get_disksize_mbytes.assert_called_once_with(
            root_clone=0, boot_clone=0
        )
        assert loop_provider.create.call_args_list == [call(), call()]
        disk.wipe.assert_called_once_with()
        disk.create_efi_csm_partition.assert_called_once_with(
            self.firmware.get_legacy_bios_partition_size(), None
        )
        disk.create_efi_partition.assert_called_once_with(
            self.firmware.get_efi_partition_size(), None
        )
        disk.create_boot_partition.assert_called_once_with(
            format(self.disk_setup.boot_partition_size()), 0, None
        )
        disk.create_prep_partition.assert_called_once_with(
            self.firmware.get_prep_partition_size()
        )
        disk.create_root_partition.assert_called_once_with('all_free', 0, None)
        disk.map_partitions.assert_called_once_with()
        bootloader_config.setup_disk_boot_images.assert_called_once_with(
            '0815', '0815'
        )
        bootloader_config.write_meta_data.assert_called_once_with(
            root_device='/dev/readonly-root-device',
            write_device='/dev/root-device',
            boot_options='',
        )
        bootloader_config.setup_disk_image_config.assert_called_once_with(
            boot_options={
                'device_map': self.device_map,
                'boot_image': self.boot_image_task,
                'boot_device': '/dev/boot-device',
                'root_device': '/dev/readonly-root-device',
                'write_device': '/dev/root-device',
                'firmware': self.firmware,
                'target_removable': None,
                'efi_device': '/dev/efi-device',
                'prep_device': '/dev/prep-device',
                'install_options': [],
                'shim_options': [],
            }
        )
        assert self.setup.script_exists.call_args_list == [
            call('pre_disk_sync.sh'),
            call('disk.sh'),
        ]
        disk_system.call_pre_disk_script.assert_called_once_with()
        disk_system.call_disk_script.assert_called_once_with()
        disk_system.cleanup.assert_called_once_with()
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device',
        )
        self.boot_image_task.prepare.assert_called_once_with()

        filesystem.create_on_device.assert_called_once_with(label='ROOT')

        assert (
            filesystem.__enter__.return_value.create_on_device.call_args_list[0]
            == call(label='EFI')
        )
        assert (
            filesystem.__enter__.return_value.create_on_device.call_args_list[1]
            == call(label='BOOT')
        )

        assert (
            filesystem.__enter__.return_value.sync_data.call_args_list[0]
            == call()
        )
        assert filesystem.__enter__.return_value.sync_data.call_args_list[
            1
        ] == call(['efi/*'])

        assert filesystem.__enter__.return_value.sync_data.call_args_list[
            2
        ] == call(
            [
                'image',
                '.kconfig',
                'run/*',
                'tmp/*',
                '.buildenv',
                'var/cache/kiwi',
                'boot/*',
                'boot/.*',
                'boot/efi/*',
                'boot/efi/.*',
            ]
        )
        assert m_open.call_args_list == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('boot_dir/config.bootoptions', 'w'),
            call('/dev/some-loop', 'wb'),
            call('root_dir/etc/veritytab', 'w'),
        ]
        m_open.return_value.write.assert_has_calls(
            [
                call('kiwi_BootPart="1"\n'),
                call('kiwi_RootPart="1"\n'),
                call('0x0f0f0f0f\n'),
                call('boot_cmdline\n'),
                call(bytes(b'\x0f\x0f\x0f\x0f')),
            ]
        )
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(['blockdev', '--getsize64', '/dev/root-device']),
            call(['dd', 'if=tempfile', 'of=/dev/root-device']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img']),
            call(
                [
                    'cp',
                    'root_dir/boot/initramfs-1.2.3.img',
                    'diskroot/boot/initramfs-1.2.3.img',
                ]
            ),
        ]
        self.block_operation.get_blkid.assert_has_calls([call('PARTUUID')])
        self.setup.export_package_list.assert_called_once_with('target_dir')
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        # config.partids is written but not used by the dracut initrd
        assert self.boot_image_task.include_file.call_args_list == [
            call('/recovery.partition.size'),
            call(filename='/etc/veritytab', delete_after_include=True),
        ]
        self.boot_image_task.include_module.assert_called_once_with(
            'kiwi-repart'
        )
        self.boot_image_task.omit_module.assert_called_once_with('multipath')
        assert (
            self.boot_image_task.write_system_config_file.call_args_list == []
        )
        filesystem.__enter__.return_value.create_verity_layer.assert_called_once_with(
            10, 'tempfile'
        )
        filesystem.__enter__.return_value.create_verification_metadata.assert_called_once_with(
            '/dev/root-device'
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.VeritySetup')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('os.access')
    def test_create_disk_standard_root_with_kernel_flavors(
        self,
        mock_os_access,
        mock_Temporary_new_file,
        mock_VeritySetup,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_LoopDevice,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        # An initrd is created for the kernel of each flavor, also
        # when it is created again with the veritytab included
        mock_os_access.side_effect = lambda path, mode: path != 'diskroot/boot/'
        system = Mock()
        system.mountpoint.return_value = 'diskroot'
        mock_ImageSystem.return_value.__enter__.return_value = system
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        mock_LoopDevice.return_value.__enter__.return_value = Mock()
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_Temporary_new_file.return_value = tempfile
        mock_os_path_getsize.return_value = 42
        self.boot_image_task.get_boot_names.side_effect = (
            lambda flavor: self.boot_names_type(
                kernel_name=f'vmlinuz-1.2.3-{flavor}',
                initrd_name=f'initrd-1.2.3-{flavor}',
            )
        )
        mock_path.return_value = True
        mock_rand.return_value = 15
        mock_fs.return_value = MagicMock()
        self.firmware.get_legacy_bios_partition_size.return_value = 2
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_embed_verity_metadata = True
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.bootloader = 'systemd_boot'
        self.disk_builder.kernel_flavors = ['rt', 'default']
        self.setup.script_exists.return_value = False

        with patch('builtins.open', mock_open(), create=True):
            self.disk_builder.create_disk()

        # files included with delete_after_include are kept until
        # the initrd of the last flavor is created
        mbrid = self.disk_builder.mbrid
        assert self.boot_image_task.create_initrd.call_args_list == [
            call(mbrid, flavor='rt', delete_included_files=False),
            call(mbrid, flavor='default', delete_included_files=True),
            call(mbrid, flavor='rt', delete_included_files=False),
            call(mbrid, flavor='default', delete_included_files=True),
        ]
        initrd_commands = [
            command
            for command in mock_command.call_args_list
            if 'initrd' in ' '.join(command[0][0])
        ]
        assert initrd_commands == [
            call(['mv', 'initrd', 'root_dir/boot/initrd-1.2.3-rt']),
            call(['mv', 'initrd', 'root_dir/boot/initrd-1.2.3-default']),
            call(['mv', 'initrd', 'root_dir/boot/initrd-1.2.3-rt']),
            call(['mv', 'initrd', 'root_dir/boot/initrd-1.2.3-default']),
            call(
                [
                    'cp',
                    'root_dir/boot/initrd-1.2.3-rt',
                    'diskroot/boot/efi/os/initrd-1.2.3-rt',
                ]
            ),
            call(
                [
                    'cp',
                    'root_dir/boot/initrd-1.2.3-default',
                    'diskroot/boot/efi/os/initrd-1.2.3-default',
                ]
            ),
        ]

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.SystemSetup')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('kiwi.builder.disk.Temporary.new_file')
    def test_create_disk_standard_root_with_fixed_rootfs_size(
        self,
        mock_Temporary_new_file,
        mock_ImageSystem,
        mock_SystemSetup,
        mock_os_path_getsize,
        mock_path,
        mock_grub_dir,
        mock_command,
        mock_rand,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        self.disk_builder.root_filesystem_embed_verity_metadata = False
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.volume_manager_name = None
        self.setup.script_exists.return_value = False
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.root_clone_count = 1
        self.disk_builder.oem_systemsize = 1024
        self.disk_builder.oem_resize = False

        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        disk.create_root_partition.assert_called_once_with(
            'clone:1024:1024', 1, None
        )

    @patch('kiwi.builder.disk.Path')
    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.DeviceProvider')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.Temporary.new_file')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.BlockID')
    @patch('kiwi.builder.disk.MountManager')
    def test_create_disk_standard_root_is_overlay(
        self,
        mock_MountManager,
        mock_BlockID,
        mock_rand,
        mock_temp,
        mock_getsize,
        mock_exists,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_DeviceProvider,
        mock_LoopDevice,
        mock_create_boot_loader_config,
        mock_Disk,
        mock_Path,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'partuuid'
        block_operation.get_filesystem.return_value = 'ext3'
        mock_BlockID.return_value = block_operation
        mock_rand.return_value = 15
        self.disk_builder.dracut_setup = DracutT(
            uefi=True, modules=[], drivers=[]
        )
        self.disk_builder.dracut_add_modules = ['some']
        self.disk_builder.dracut_omit_modules = ['some']
        self.disk_builder.dracut_add_drivers = ['driver1']
        self.disk_builder.dracut_omit_drivers = ['driver2']
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.root_filesystem_has_write_partition = False
        self.disk_builder.root_filesystem_verity_blocks = 10
        self.disk_builder.root_filesystem_embed_verity_metadata = True
        self.disk_builder.integrity = True
        self.disk_builder.root_filesystem_embed_integrity_metadata = True
        self.disk_builder.volume_manager_name = None
        fs = Mock()
        fs.veritysetup.verity_hash_offset = 'Some'
        fs.veritysetup.verity_dict = {'Roothash': 'Some'}
        mock_fs.return_value.__enter__.return_value = fs
        mock_getsize.return_value = 1048576
        tempfile = Mock()
        tempfile.name = 'kiwi-tempname'
        mock_temp.return_value = tempfile
        mock_exists.return_value = True
        self.disk_builder.initrd_system = 'dracut'
        disk.public_partition_id_map = self.id_map
        disk.public_partition_id_map['kiwi_ROPart'] = 1
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        mock_fs.assert_has_calls(
            [
                call(
                    'squashfs',
                    custom_args={'compression': None, 'create_options': []},
                    device_provider=mock_DeviceProvider.return_value,
                    root_dir='root_dir',
                )
            ]
        )
        fs.create_on_file.assert_has_calls(
            [
                call(exclude=['var/cache/kiwi'], filename='kiwi-tempname'),
                call(
                    exclude=[
                        '.kconfig',
                        'run/*',
                        'tmp/*',
                        '.buildenv',
                        'var/cache/kiwi',
                        'image/*',
                    ],
                    filename='kiwi-tempname',
                ),
            ],
            any_order=True,
        )
        fs.create_verity_layer.assert_called_once_with(10)
        fs.create_verification_metadata.assert_called_once_with(
            '/dev/integrityRoot'
        )
        self.integrity_root.create_integrity_metadata.assert_called_once_with()
        self.integrity_root.sign_integrity_metadata.assert_called_once_with()
        self.integrity_root.write_integrity_metadata.assert_called_once_with()
        disk.create_root_readonly_partition.assert_called_once_with(11, 0)
        assert mock_command.call_args_list[2] == call(
            ['blockdev', '--getsize64', '/dev/integrityRoot']
        )
        assert mock_command.call_args_list[3] == call(
            ['dd', 'if=kiwi-tempname', 'of=/dev/integrityRoot']
        )
        m_open.return_value.write.assert_has_calls(
            [
                # config.partids
                call('kiwi_BootPart="1"\n'),
                call('kiwi_RootPart="1"\n'),
                # mbrid
                call('0x0f0f0f0f\n'),
                # config.bootoptions
                call('boot_cmdline\n'),
                # some-loop
                call(b'\x0f\x0f\x0f\x0f'),
            ],
            any_order=True,
        )
        assert self.boot_image_task.include_module.call_args_list == [
            call('some'),
            call('kiwi-overlay'),
            call('kiwi-repart'),
        ]
        assert self.boot_image_task.omit_module.call_args_list == [
            call('some'),
            call('multipath'),
        ]
        self.boot_image_task.include_driver.assert_called_once_with('driver1')
        self.boot_image_task.omit_driver.assert_called_once_with('driver2')
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={'modules': ['kiwi-overlay']}
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_no_hypervisor_found(
        self, mock_command, mock_fs, mock_LoopDevice, mock_Disk
    ):
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        self.kernel.get_xen_hypervisor.return_value = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.xen_server = True

        with patch('builtins.open'):
            with raises(KiwiDiskBootImageError):
                self.disk_builder.create_disk()

    @patch('kiwi.mount_manager.BlockID')
    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_xen_server_boot(
        self,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
        mock_BlockID,
    ):
        mock_BlockID.return_value.get_filesystem.return_value = 'xfs'
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.xen_server = True
        self.firmware.efi_mode = Mock(return_value=False)

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'root_dir', '/boot/xen.gz'
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_standard_root_s390_boot(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        self.disk_builder.arch = 's390x'
        self.disk_builder.host_key_certificates = Mock()
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = Mock(return_value=False)
        self.disk_builder.bootloader = 'grub2_s390x_emu'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        bootloader_config.write.assert_called_once_with()

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_standard_root_secure_boot(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = Mock(return_value='uefi')
        with patch('builtins.open'):
            self.disk_builder.create_disk()

        bootloader_config.setup_disk_boot_images.assert_called_once_with(
            '0815', '0815'
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_mdraid_root(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.mdraid = 'mirroring'
        disk.public_partition_id_map = self.id_map

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_root_raid_partition.assert_called_once_with(
            'all_free', 0, None
        )
        self.raid_root.create_degraded_raid.assert_called_once_with(
            raid_level='mirroring'
        )
        self.raid_root.create_raid_config.assert_called_once_with(
            'boot_dir/etc/mdadm.conf'
        )
        assert disk.public_partition_id_map == {
            'kiwi_RaidPart': 1,
            'kiwi_RootPart': 1,
            'kiwi_BootPart': 1,
            'kiwi_RaidDev': '/dev/md0',
        }

        # A custom root partition number from the image description
        # reaches the raid partition
        disk.create_root_raid_partition.reset_mock()
        self.disk_builder.xml_state.build_type.get_rootpart_id = Mock(
            return_value='128'
        )
        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_root_raid_partition.assert_called_once_with(
            'all_free', 0, 128
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_luks_root(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.luks = 'passphrase'
        self.disk_setup.need_boot_partition.return_value = False
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.root_filesystem_has_write_partition = False
        self.disk_builder.boot_is_crypto = True
        disk.public_partition_id_map = self.id_map
        disk.public_partition_id_map['kiwi_ROPart'] = 1
        self.disk_builder.cmdline = 'rd.kiwi.oem.luks.reencrypt'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.luks_root.create_crypto_luks.assert_called_once_with(
            passphrase='passphrase',
            osname=None,
            options=[],
            keyfile='/root/.root.keyfile',
            randomize=True,
            root_dir='root_dir',
        )
        self.luks_root.create_crypttab.assert_called_once_with(
            'root_dir/etc/crypttab'
        )
        assert self.boot_image_task.include_file.call_args_list == [
            call('/root/.root.keyfile'),
            call('/config.partids'),
            call('/etc/crypttab'),
            call(filename='/root/.luks.header', delete_after_include=True),
            call(filename='/root/.luks.slot', delete_after_include=True),
            call(filename='/root/.slotpass', delete_after_include=True),
        ]
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={'install_items': ['/root/.root.keyfile']},
            config_file='root_dir/etc/dracut.conf.d/99-luks-boot.conf',
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('kiwi.builder.disk.BootLoaderInstall.new')
    def test_create_disk_luks_root_with_disk_password(
        self,
        mock_BootLoaderInstall,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.use_disk_password = True
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.luks = 'passphrase'
        self.disk_builder.use_disk_password = True
        self.disk_setup.need_boot_partition.return_value = False
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.root_filesystem_has_write_partition = True
        self.disk_builder.boot_is_crypto = True
        disk.public_partition_id_map = self.id_map
        disk.public_partition_id_map['kiwi_ROPart'] = 1
        bootloader = mock_BootLoaderInstall.return_value
        self.disk_builder.cmdline = 'rd.kiwi.oem.luks.reencrypt'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.luks_root.create_crypto_luks.assert_called_once_with(
            passphrase='passphrase',
            osname=None,
            options=[],
            keyfile='/root/.root.keyfile',
            randomize=True,
            root_dir='root_dir',
        )
        self.luks_root.create_crypttab.assert_called_once_with(
            'root_dir/etc/crypttab'
        )
        assert self.boot_image_task.include_file.call_args_list == [
            call('/root/.root.keyfile'),
            call('/config.partids'),
            call('/etc/crypttab'),
            call(filename='/root/.luks.header', delete_after_include=True),
            call(filename='/root/.luks.slot', delete_after_include=True),
            call(filename='/root/.slotpass', delete_after_include=True),
        ]
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={'install_items': ['/root/.root.keyfile']},
            config_file='root_dir/etc/dracut.conf.d/99-luks-boot.conf',
        )
        bootloader.set_disk_password.assert_called_once_with('passphrase')

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('kiwi.builder.disk.BlockID')
    def test_create_disk_uses_custom_partitions(
        self,
        mock_BlockID,
        mock_exists,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        self.fstype_mock_list = [
            'ext3',
            'squashfs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
            'some_fs',
        ]
        fstype = list(self.fstype_mock_list)

        def get_filesystem():
            return fstype.pop()

        block_operation = Mock()
        block_operation.get_filesystem.side_effect = get_filesystem
        block_operation.get_blkid.return_value = 'blkid_result'

        mock_BlockID.return_value = block_operation

        mock_exists.return_value = True
        self.disk_builder.custom_partitions = {
            'var': ptable_entry_type(
                mbsize=100,
                clone=0,
                partition_name='p.lxvar',
                partition_type='t.linux',
                partition_id=None,
                mountpoint='/var',
                filesystem='ext3',
                label='var',
            ),
            'spare': ptable_entry_type(
                mbsize=100,
                clone=0,
                partition_name='p.lxtmp',
                partition_type='t.linux',
                partition_id=None,
                mountpoint='/spare',
                filesystem='squashfs',
                label='',
            ),
        }
        self.disk_builder.volume_manager_name = None

        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.persistency_type = 'by-uuid'
        disk.create_custom_partitions.assert_called_once_with(
            self.disk_builder.custom_partitions
        )
        assert [
            call('PARTUUID=blkid_result /spare squashfs defaults 0 0')
        ] in self.disk_builder.fstab.add_entry.call_args_list

        assert [
            call('UUID=blkid_result /var ext3 defaults 0 0')
        ] in self.disk_builder.fstab.add_entry.call_args_list

        self.disk_builder.persistency_type = 'by-partuuid'
        fstype = list(self.fstype_mock_list)
        with patch('builtins.open'):
            self.disk_builder.create_disk()
        assert [
            call('PARTUUID=blkid_result /var ext3 defaults 0 0')
        ] in self.disk_builder.fstab.add_entry.call_args_list

        self.disk_builder.persistency_type = 'by-label'
        fstype = list(self.fstype_mock_list)
        with patch('builtins.open'):
            self.disk_builder.create_disk()
        assert [
            call('LABEL=blkid_result /var ext3 defaults 0 0')
        ] in self.disk_builder.fstab.add_entry.call_args_list

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.VolumeManager.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('os.path.exists')
    def test_create_disk_btrfs_managed_root(
        self,
        mock_exists,
        mock_ImageSystem,
        mock_grub_dir,
        mock_command,
        mock_volume_manager,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        mock_exists.return_value = True
        volume_manager = Mock()
        volume_manager.get_device = Mock(
            return_value={'root': MappedDevice('root', Mock())}
        )
        volume_manager.get_fstab = Mock(return_value=['fstab_volume_entries'])
        volume_manager.get_root_volume_name = Mock(return_value='@')
        mock_volume_manager.return_value = volume_manager
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = 'btrfs'
        self.disk_builder.btrfs_default_volume_requested = False

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        assert [
            call('UUID=blkid_result / blkid_result_fs ro,defaults,subvol=@ 0 0')
        ] in self.disk_builder.fstab.add_entry.call_args_list

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.VolumeManager.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('os.path.exists')
    def test_create_disk_btrfs_seed_for_partition_based_install(
        self,
        mock_exists,
        mock_ImageSystem,
        mock_grub_dir,
        mock_command,
        mock_volume_manager,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        mock_Disk.return_value.__enter__.return_value = (
            self._get_disk_instance()
        )
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        mock_exists.return_value = True
        volume_manager = Mock()
        volume_manager.get_device = Mock(
            return_value={'root': MappedDevice('/dev/root-device', Mock())}
        )
        volume_manager.get_fstab = Mock(return_value=['fstab_volume_entries'])
        volume_manager.get_root_volume_name = Mock(return_value='@')
        mock_volume_manager.return_value = volume_manager
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = 'btrfs'
        self.disk_builder.btrfs_default_volume_requested = False
        self.disk_builder.install_iso = True
        seed_call = call(['btrfstune', '-S', '1', '/dev/root-device'])

        # no seed requested, see XMLState.btrfs_seed_requested
        self.disk_builder.btrfs_seed_requested = False
        with patch('builtins.open'):
            self.disk_builder.create_disk()
        assert seed_call not in mock_command.call_args_list

        # seed requested, root is seed
        mock_command.reset_mock()
        self.disk_builder.btrfs_seed_requested = True
        with patch('builtins.open'):
            self.disk_builder.create_disk()
        assert seed_call in mock_command.call_args_list

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.VolumeManager.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('kiwi.builder.disk.ImageSystem')
    @patch('os.path.exists')
    def test_create_disk_volume_managed_root(
        self,
        mock_exists,
        mock_ImageSystem,
        mock_grub_dir,
        mock_command,
        mock_volume_manager,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        mock_exists.return_value = True
        volume_manager = Mock()
        volume_manager.get_device = Mock(
            return_value={
                'root': MappedDevice('/dev/systemVG/LVRoot', Mock()),
                'swap': MappedDevice('/dev/systemVG/LVSwap', Mock()),
            }
        )
        volume_manager.get_fstab = Mock(return_value=['fstab_volume_entries'])
        mock_volume_manager.return_value = volume_manager
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = 'lvm'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_root_lvm_partition.assert_called_once_with(
            'all_free', 0, None
        )
        volume_manager.setup.assert_called_once_with('systemVG')
        volume_manager.create_volumes.assert_called_once_with('btrfs')
        volume_manager.mount_volumes.call_args_list[0].assert_called_once_with()
        assert volume_manager.get_fstab.call_args_list == [
            call(None, 'btrfs'),
            call(None, 'btrfs'),
        ]
        volume_manager.sync_data.assert_called_once_with(
            [
                'image',
                '.kconfig',
                'run/*',
                'tmp/*',
                '.buildenv',
                'var/cache/kiwi',
                'boot/*',
                'boot/.*',
                'boot/efi/*',
                'boot/efi/.*',
            ]
        )
        self.setup.create_fstab.assert_called_once_with(self.disk_builder.fstab)
        self.boot_image_task.setup.create_fstab.assert_called_once_with(
            self.disk_builder.fstab
        )

        # A custom root partition number from the image description
        # reaches the lvm partition
        disk.create_root_lvm_partition.reset_mock()
        self.disk_builder.xml_state.build_type.get_rootpart_id = Mock(
            return_value='128'
        )
        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_root_lvm_partition.assert_called_once_with(
            'all_free', 0, 128
        )

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_hybrid_gpt_requested(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.hybrid_mbr = True

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_hybrid_mbr.assert_called_once_with()

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_force_mbr_requested(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.force_mbr = True

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_mbr.assert_called_once_with()

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_custom_start_sector_requested(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.disk_start_sector = 4096
        self.firmware.get_partition_table_type = Mock(return_value='msdos')

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.set_start_sector.assert_called_once_with(4096)

    def test_create(self):
        result = Mock()
        create_disk = Mock(return_value=result)
        create_install_media = Mock(return_value=result)
        append_unpartitioned = Mock()
        create_disk_format = Mock(return_value=result)

        self.disk_builder.create_disk = create_disk
        self.disk_builder.create_install_media = create_install_media
        self.disk_builder.append_unpartitioned_space = append_unpartitioned
        self.disk_builder.create_disk_format = create_disk_format

        self.disk_builder.create()

        create_disk.assert_called_once_with()
        create_install_media.assert_called_once_with(result)
        append_unpartitioned.assert_called_once_with()
        create_disk_format.assert_called_once_with(result)

    @patch('kiwi.builder.disk.Disk')
    @patch('kiwi.builder.disk.create_boot_loader_config')
    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_spare_part_requested(
        self,
        mock_grub_dir,
        mock_command,
        mock_fs,
        mock_create_boot_loader_config,
        mock_Disk,
    ):
        disk = self._get_disk_instance()
        mock_Disk.return_value.__enter__.return_value = disk
        bootloader_config = Mock()
        bootloader_config.get_boot_cmdline = Mock(return_value='boot_cmdline')
        mock_create_boot_loader_config.return_value.__enter__.return_value = (
            bootloader_config
        )
        filesystem = MagicMock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.spare_part_mbsize = 42
        self.disk_builder.spare_part_fs = 'ext4'
        self.disk_builder.spare_part_mountpoint = '/var'
        self.disk_builder.spare_part_is_last = False

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_spare_partition.assert_called_once_with('42')
        assert mock_fs.call_args_list[0] == call(
            self.disk_builder.spare_part_fs,
            self.device_map['spare'],
            'root_dir/var/',
            {'fs_attributes': None},
        )
        assert filesystem.sync_data.call_args_list.pop() == call(
            [
                'image',
                '.kconfig',
                'run/*',
                'tmp/*',
                '.buildenv',
                'var/cache/kiwi',
                'var/*',
                'var/.*',
                'boot/*',
                'boot/.*',
                'boot/efi/*',
                'boot/efi/.*',
            ]
        )
        assert [
            call('UUID=blkid_result / blkid_result_fs ro 0 0'),
            call('UUID=blkid_result /boot blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result /boot/efi blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result /var blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result swap blkid_result_fs defaults 0 0'),
        ] in self.disk_builder.fstab.add_entry.call_args_list

        disk.create_root_partition.reset_mock()
        disk.create_spare_partition.reset_mock()
        self.disk_builder.spare_part_is_last = True
        self.disk_builder.disk_resize_requested = False

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        disk.create_spare_partition.assert_called_once_with('all_free')

    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.Partitioner.new')
    @patch('kiwi.builder.disk.DiskFormat.new')
    def test_append_unpartitioned_space(
        self, mock_diskformat, mock_partitioner, mock_LoopDevice
    ):
        loop_provider = Mock()
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        partitioner = Mock()
        mock_partitioner.return_value = partitioner
        disk_format = Mock()
        mock_diskformat.return_value.__enter__.return_value = disk_format
        self.disk_builder.unpartitioned_bytes = 1024
        self.disk_builder.append_unpartitioned_space()
        disk_format.resize_raw_disk.assert_called_once_with(1024, append=True)
        loop_provider.create.assert_called_once_with(overwrite=False)
        assert partitioner.resize_table.called

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DiskFormat.new')
    def test_create_disk_format(self, mock_DiskFormat, mock_command, mock_fs):
        disk_subformat = Mock()
        mock_DiskFormat.return_value.__enter__.return_value = disk_subformat
        result_instance = Mock()
        filesystem = Mock()
        mock_fs.return_value.__enter__.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.image_format = 'vmdk'

        with patch('builtins.open'):
            self.disk_builder.create_disk_format(result_instance)

        disk_subformat.create_image_format.assert_called_once_with()

    def _get_disk_instance(self) -> Mock:
        disk = Mock()
        provider = Mock()
        partitioner = Mock()
        disk.get_uuid = Mock(return_value='0815')
        disk.get_public_partition_id_map = Mock(return_value=self.id_map_sorted)
        disk.get_device = Mock(return_value=self.device_map)
        provider.get_device = Mock(return_value='/dev/some-loop')
        partitioner.get_id = Mock(return_value=1)
        disk.storage_provider = provider
        disk.partitioner = partitioner
        return disk

    def test_get_root_readonly_compression_erofs(self):
        self.disk_builder.root_filesystem_read_only_type = 'erofs'
        self.disk_builder.xml_state.build_type.get_erofscompression = Mock(
            return_value='lz4hc,level=12'
        )
        assert (
            self.disk_builder._get_root_readonly_compression()
            == 'lz4hc,level=12'
        )

    def test_get_root_readonly_compression_squashfs(self):
        self.disk_builder.root_filesystem_read_only_type = 'squashfs'
        self.disk_builder.xml_state.build_type.get_squashfscompression = Mock(
            return_value='gzip'
        )
        assert self.disk_builder._get_root_readonly_compression() == 'gzip'

    def test_custom_partition_id(self):
        assert self.disk_builder._custom_partition_id('128') == 128
        assert self.disk_builder._custom_partition_id(None) is None

    def test_custom_partition_id_allows_the_partitioner_to_count_on(self):
        # The partitioner derives the next partition number from the last
        # one it was given. Handing it the raw string from the image
        # description made the next partition without an explicit number
        # fail with "can only concatenate str (not int) to str".
        partitioner = PartitionerGpt(Mock())
        with patch('kiwi.partitioner.gpt.Command.run'):
            partitioner.create(
                'p.UEFI',
                20,
                't.efi',
                partition_id=self.disk_builder._custom_partition_id('128'),
            )
            assert partitioner.partition_id == 128
            partitioner.create('p.lxlvm', 100, 't.lvm')
        assert partitioner.partition_id == 129

    def _setup_repart_builder(self):
        self.disk_builder.disk_builder = 'systemd-repart'
        self.disk_builder.bootloader = 'systemd_boot'
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.requested_filesystem = 'ext4'
        self.disk_builder.volume_manager_name = None
        self.disk_builder.mdraid = None
        self.disk_builder.luks = None
        self.disk_builder.integrity = None
        self.disk_builder.root_filesystem_verity_blocks = None
        self.disk_builder.custom_partitions = {}
        self.disk_builder.spare_part_mbsize = None
        self.disk_builder.root_clone_count = 0
        self.disk_builder.boot_clone_count = 0
        self.disk_builder.custom_root_creation_args = []
        self.disk_builder.unpartitioned_bytes = 0
        self.disk_builder.btrfs_seed_requested = False
        self.disk_builder.apply_dps_codes = True
        self.disk_builder.blocksize = 4096
        self.disk_builder.swap_mbytes = 128
        self.disk_builder.persistency_type = 'by-uuid'
        self.disk_builder.custom_root_mount_args = ['noatime']
        self.disk_builder.custom_efi_mount_args = []
        self.disk_builder.cmdline = 'splash'
        self.disk_builder.xml_state.build_type.set_editbootinstall(None)
        self.disk_setup.need_boot_partition.return_value = False
        self.firmware.get_partition_table_type.return_value = 'gpt'
        self.firmware.get_efi_partition_size.return_value = 20
        kiwi.builder.disk.create_boot_loader_config = MagicMock()
        kiwi.builder.disk.create_boot_loader_config.return_value.__enter__.return_value = (
            self.bootloader_config
        )

    def test_create_disk_repart_unsupported(self):
        self.disk_builder.disk_builder = 'systemd-repart'
        self.disk_builder.bootloader = 'zipl'
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder.create_disk()
        assert "bootloader 'zipl'" in format(issue.value)

    def test_check_repart_requirements(self):
        self._setup_repart_builder()
        self.disk_builder._check_repart_requirements()
        self.firmware.get_partition_table_type.return_value = 'msdos'
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder._check_repart_requirements()
        assert format(issue.value) == (
            'systemd-repart disk builder does not support: '
            'partition table other than gpt'
        )
        self.firmware.efi_mode.return_value = ''
        self.disk_builder.initrd_system = 'kiwi'
        self.disk_builder.requested_filesystem = 'squashfs'
        self.disk_builder.luks = 'secret'
        self.disk_builder.root_clone_count = 1
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder._check_repart_requirements()
        assert format(issue.value) == (
            'systemd-repart disk builder does not support: '
            "firmware without EFI, initrd system 'kiwi', "
            "filesystem 'squashfs', luks, partition clones"
        )

    def test_check_repart_requirements_grub2(self):
        self._setup_repart_builder()
        self.disk_builder.bootloader = 'grub2'
        self.firmware.legacy_bios_mode.return_value = False
        self.disk_builder._check_repart_requirements()
        self.firmware.legacy_bios_mode.return_value = True
        self.disk_builder.xen_server = True
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder._check_repart_requirements()
        assert format(issue.value) == (
            'systemd-repart disk builder does not support: '
            'legacy BIOS boot, eficsm must be false, xen hypervisor boot'
        )
        # legacy BIOS boot is ignored for systemd-boot
        self.disk_builder.bootloader = 'systemd_boot'
        self.disk_builder.xen_server = False
        self.disk_builder._check_repart_requirements()

    def _setup_repart_btrfs_volumes(self):
        self._setup_repart_builder()
        self.disk_builder.requested_filesystem = 'btrfs'
        self.disk_builder.volume_manager_name = 'btrfs'
        self.disk_builder.btrfs_default_volume_requested = True
        self.disk_builder.volumes = [
            volume_type(
                name='home',
                parent='',
                size='freespace:500',
                realpath='home',
                mountpoint='home',
                fullsize=False,
                label=None,
                attributes=['enable-for-filesystem-check'],
                is_root_volume=False,
            ),
            volume_type(
                name='',
                parent='',
                size=None,
                realpath='/',
                mountpoint=None,
                fullsize=True,
                label=None,
                attributes=[],
                is_root_volume=True,
            ),
        ]
        build_type = self.disk_builder.xml_state.build_type
        build_type.set_btrfs_root_is_subvolume(True)
        build_type.set_btrfs_root_is_snapper_snapshot(True)
        build_type.set_btrfs_root_is_readonly_snapshot(True)
        build_type.set_btrfs_quota_groups(False)

    def test_check_repart_requirements_volume_management(self):
        self._setup_repart_btrfs_volumes()
        self.disk_builder._check_repart_requirements()
        self.disk_builder.xml_state.build_type.set_btrfs_quota_groups(True)
        self.disk_builder.volumes[0] = self.disk_builder.volumes[0]._replace(
            attributes=['quota=1G', 'no-copy-on-write']
        )
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder._check_repart_requirements()
        assert format(issue.value) == (
            'systemd-repart disk builder does not support: '
            'btrfs quota groups, volume quota, volumes without copy-on-write'
        )
        self.disk_builder.volume_manager_name = 'lvm'
        with raises(KiwiDiskBuilderRepartError) as issue:
            self.disk_builder._check_repart_requirements()
        assert format(issue.value) == (
            'systemd-repart disk builder does not support: '
            "volume management 'lvm', volume quota, "
            'volumes without copy-on-write'
        )

    def test_get_repart_btrfs_layout(self):
        self._setup_repart_builder()
        assert self.disk_builder._get_repart_btrfs_layout() is None
        self._setup_repart_btrfs_volumes()
        layout = self.disk_builder._get_repart_btrfs_layout()
        assert layout.root_path == '/@/.snapshots/1/snapshot'
        assert layout.root_is_readonly_snapshot is True
        assert layout.default_volume_requested is True

    def test_get_repart_boot_cmdline_btrfs(self):
        self._setup_repart_btrfs_volumes()
        layout = RepartBtrfsLayout(
            self.disk_builder.volumes, True, default_volume_requested=False
        )
        assert self.disk_builder._get_repart_boot_cmdline('0815', layout) == (
            'splash root=PARTUUID=0815 rootflags=subvol=@'
        )
        self.disk_builder.cmdline = 'root=LABEL=ROOT rootflags=noatime'
        assert self.disk_builder._get_repart_boot_cmdline('0815', layout) == (
            'root=LABEL=ROOT rootflags=noatime'
        )

    def test_write_repart_fstab_to_system_image_btrfs_root_subvolume(self):
        self._setup_repart_btrfs_volumes()
        layout = RepartBtrfsLayout(
            self.disk_builder.volumes, True, default_volume_requested=False
        )
        root = RepartPartition('root', 'root', 'ROOT', '0815', 'btrfs')
        self.disk_builder._write_repart_fstab_to_system_image([root], layout)
        # the root subvolume is not the default subvolume, the
        # root tree must be mounted by subvol= option
        assert self.fstab.add_entry.call_args_list[0] == call(
            'PARTUUID=0815 / btrfs noatime,subvol=@ 0 1'
        )

    @patch('kiwi.builder.disk.SnapshotManagerSnapper')
    @patch('kiwi.builder.disk.os.chmod')
    @patch('kiwi.builder.disk.Path.create')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DataSync')
    @patch('kiwi.builder.disk.Temporary')
    @patch('kiwi.builder.disk.SystemIdentifier')
    @patch('kiwi.builder.disk.SystemdRepart')
    @patch('os.path.isdir')
    @patch.object(DiskBuilder, '_create_boot_files')
    @patch.object(DiskBuilder, '_write_recovery_metadata_to_boot_image')
    def test_build_disk_with_repart_btrfs_volumes(
        self,
        mock_write_recovery_metadata_to_boot_image,
        mock_create_boot_files,
        mock_os_path_isdir,
        mock_SystemdRepart,
        mock_SystemIdentifier,
        mock_Temporary,
        mock_DataSync,
        mock_Command_run,
        mock_Path_create,
        mock_os_chmod,
        mock_SnapshotManagerSnapper,
    ):
        self._setup_repart_btrfs_volumes()
        self.disk_builder.bootloader = 'grub2'
        self.disk_builder.swap_mbytes = 0
        mock_os_path_isdir.return_value = False
        temporary_dirs = iter(['staging', 'snapshots'])
        mock_Temporary.return_value.new_dir.side_effect = (
            lambda: SimpleNamespace(name=next(temporary_dirs))
        )
        mock_Command_run.return_value.output = 'fs-uuid\n'
        mock_SystemdRepart.get_filesystem_uuid.return_value = 'fs-uuid'
        self.setup.script_exists.return_value = False
        repart = mock_SystemdRepart.return_value
        repart.get_partition_id_map.return_value = {'efi': 1, 'root': 2}
        partitions = []
        repart.add_partition.side_effect = partitions.append
        repart.partitions = partitions
        repart.create.side_effect = lambda size: [
            {'uuid': partition.uuid, 'offset': 0} for partition in partitions
        ]
        with patch('builtins.open', mock_open()) as m_open:
            self.disk_builder._build_disk_with_repart(1024)

        root = partitions[-1]
        assert root.filesystem == 'btrfs'
        assert root.copy_files == [
            'snapshots/.snapshots:/@/.snapshots',
            'staging:/@/.snapshots/1/snapshot',
            'staging/home:/@/home',
        ]
        assert root.exclude_files == ['staging/boot/efi/']
        assert root.exclude_files_target == ['/@/.snapshots/1/snapshot/home/']
        assert root.make_directories == [
            '/@/.snapshots/1/snapshot/boot/efi',
            '/@',
            '/@/.snapshots',
            '/@/home',
            '/@/.snapshots/1/snapshot',
            '/@/.snapshots/1/snapshot/.snapshots',
        ]
        assert root.subvolumes == [
            '/@',
            '/@/.snapshots',
            '/@/home',
            '/@/.snapshots/1/snapshot:ro',
        ]
        assert root.default_subvolume == '/@/.snapshots/1/snapshot'
        efi = partitions[0]
        assert self.fstab.add_entry.call_args_list == [
            call(f'PARTUUID={efi.uuid} /boot/efi vfat defaults 0 0'),
            call(f'PARTUUID={root.uuid} / btrfs noatime,ro 0 0'),
            call(f'PARTUUID={root.uuid} /home btrfs noatime,subvol=@/home 0 2'),
            call(
                f'PARTUUID={root.uuid} /.snapshots btrfs '
                'noatime,subvol=@/.snapshots 0 0'
            ),
        ]
        # the snapshot is the default subvolume, no rootflags needed
        m_open.return_value.__enter__.return_value.write.assert_any_call(
            f'splash root=PARTUUID={root.uuid}\n'
        )
        assert call('staging/home') in mock_Path_create.call_args_list
        assert call('snapshots/.snapshots') in mock_Path_create.call_args_list
        mock_os_chmod.assert_called_once_with('snapshots/.snapshots', 0o750)
        mock_SnapshotManagerSnapper.setup_first_snapshot_on_tree.assert_called_once_with(
            'staging', 'snapshots/.snapshots'
        )
        btrfs_path = kiwi.builder.disk.create_boot_loader_config.call_args[1][
            'custom_args'
        ]['btrfs_path']
        assert btrfs_path('/boot') == '/@/.snapshots/1/snapshot/boot'

    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DataSync')
    @patch('kiwi.builder.disk.Temporary')
    @patch('kiwi.builder.disk.SystemIdentifier')
    @patch('kiwi.builder.disk.SystemdRepart.create')
    @patch('os.path.isdir')
    @patch.object(DiskBuilder, '_create_boot_files')
    @patch.object(DiskBuilder, '_write_recovery_metadata_to_boot_image')
    def test_create_disk_repart(
        self,
        mock_write_recovery_metadata_to_boot_image,
        mock_create_boot_files,
        mock_os_path_isdir,
        mock_SystemdRepart_create,
        mock_SystemIdentifier,
        mock_Temporary,
        mock_DataSync,
        mock_Command_run,
    ):
        self._setup_repart_builder()
        mock_os_path_isdir.return_value = True
        mock_Temporary.return_value.new_dir.return_value.name = 'staging'
        mock_Command_run.return_value.output = 'rootfs-uuid\n'
        self.setup.script_exists.return_value = True
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            efi_uuid = Reproducible.get_seeded_uuid('repart-partition-efi')
            swap_uuid = Reproducible.get_seeded_uuid('repart-partition-swap')
            root_uuid = Reproducible.get_seeded_uuid('repart-partition-root')
            mock_SystemdRepart_create.return_value = [
                {'uuid': efi_uuid, 'offset': 1048576},
                {'uuid': root_uuid, 'offset': 22020096},
            ]
            with patch('builtins.open', mock_open()) as m_open:
                self.disk_builder.create_disk()

        mock_Temporary.assert_called_once_with(
            prefix='kiwi_repart_root.', path='target_dir'
        )
        m_open.assert_any_call('boot_dir/config.partids', 'w')
        m_open.assert_any_call('boot_dir/config.bootoptions', 'w')
        file_handle = m_open.return_value.__enter__.return_value
        assert call('kiwi_EfiPart="1"\n') in file_handle.write.call_args_list
        assert call('kiwi_SwapPart="2"\n') in file_handle.write.call_args_list
        assert call('kiwi_RootPart="3"\n') in file_handle.write.call_args_list
        file_handle.write.assert_any_call(f'splash root=PARTUUID={root_uuid}\n')
        assert self.fstab.add_entry.call_args_list == [
            call(f'PARTUUID={efi_uuid} /boot/efi vfat defaults 0 0'),
            call(f'PARTUUID={swap_uuid} swap swap defaults 0 0'),
            call(f'PARTUUID={root_uuid} / ext4 noatime 0 1'),
        ]
        self.setup.create_fstab.assert_called_once_with(self.fstab)
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'ext4', 3
        )
        assert mock_DataSync.call_args_list == [
            call('root_dir/', 'staging'),
            call('root_dir/image/', 'staging/image'),
        ]
        self.setup.call_disk_script.assert_called_once_with(
            root_is_mountpoint=False
        )
        self.setup.call_pre_disk_script.assert_called_once_with()
        self.bootloader_config.setup_disk_boot_images.assert_called_once_with(
            SystemdRepart.get_filesystem_uuid(
                RepartPartition('root', 'root', 'ROOT', root_uuid, 'ext4')
            ),
            SystemdRepart.get_filesystem_uuid(
                RepartPartition('efi', 'esp', 'EFI', efi_uuid, 'vfat')
            ),
        )
        self.bootloader_config.setup_disk_image_config_on_tree.assert_called_once_with(
            'staging', f'splash root=PARTUUID={root_uuid}', self.boot_image_task
        )
        self.setup.cleanup.assert_called_once_with()
        mock_SystemdRepart_create.assert_called_once_with(1024)
        mock_SystemIdentifier.return_value.write_to_file.assert_called_once_with(
            self.disk_builder.diskname
        )
        mock_Command_run.assert_called_once_with(
            [
                'blkid',
                '-p',
                '-O',
                '22020096',
                '-s',
                'UUID',
                '-o',
                'value',
                self.disk_builder.diskname,
            ]
        )
        assert self.disk_builder.xml_state.get_root_partition_uuid() == (
            root_uuid
        )
        assert self.disk_builder.xml_state.get_root_filesystem_uuid() == (
            'rootfs-uuid'
        )

    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DataSync')
    @patch('kiwi.builder.disk.Temporary')
    @patch('kiwi.builder.disk.SystemIdentifier')
    @patch('kiwi.builder.disk.SystemdRepart')
    @patch('os.path.isdir')
    @patch.object(DiskBuilder, '_create_boot_files')
    @patch.object(DiskBuilder, '_write_recovery_metadata_to_boot_image')
    def test_build_disk_with_repart_by_label(
        self,
        mock_write_recovery_metadata_to_boot_image,
        mock_create_boot_files,
        mock_os_path_isdir,
        mock_SystemdRepart,
        mock_SystemIdentifier,
        mock_Temporary,
        mock_DataSync,
        mock_Command_run,
    ):
        self._setup_repart_builder()
        self.disk_builder.swap_mbytes = 0
        self.disk_builder.blocksize = None
        self.disk_builder.apply_dps_codes = False
        self.disk_builder.persistency_type = 'by-label'
        self.disk_builder.cmdline = 'root=/dev/sda3'
        mock_os_path_isdir.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'staging'
        mock_Command_run.return_value.output = ''
        self.setup.script_exists.return_value = False
        repart = mock_SystemdRepart.return_value
        repart.get_partition_id_map.return_value = {'efi': 1, 'root': 2}
        partitions = []
        repart.add_partition.side_effect = partitions.append
        repart.partitions = partitions
        with patch.dict('os.environ', {}, clear=True):
            with patch('builtins.open', mock_open()):
                self.disk_builder._build_disk_with_repart(1024)
            root = partitions[-1]
            repart.create.return_value = [{'uuid': root.uuid, 'offset': 0}]
            with patch('builtins.open', mock_open()):
                self.disk_builder._build_disk_with_repart(1024)
        mock_SystemdRepart.assert_called_with(
            self.disk_builder.diskname, 'x86_64', None
        )
        assert root.partition_type == 'linux-generic'
        assert root.uuid != partitions[0].uuid
        assert self.fstab.add_entry.call_args_list[:2] == [
            call('LABEL=EFI /boot/efi vfat defaults 0 0'),
            call('LABEL=ROOT / ext4 noatime 0 1'),
        ]
        self.bootloader_config.setup_disk_image_config_on_tree.assert_called_with(
            'staging', 'root=/dev/sda3', self.boot_image_task
        )
        mock_DataSync.assert_called_with('root_dir/', 'staging')
        self.setup.setup_selinux_file_contexts.assert_called_with()
        assert not self.setup.call_disk_script.called
        assert self.disk_builder.xml_state.get_root_filesystem_uuid() is None

    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DataSync')
    @patch('kiwi.builder.disk.Temporary')
    @patch('kiwi.builder.disk.SystemIdentifier')
    @patch('kiwi.builder.disk.SystemdRepart.create')
    @patch('os.path.isdir')
    @patch.object(DiskBuilder, '_create_boot_files')
    @patch.object(DiskBuilder, '_write_recovery_metadata_to_boot_image')
    def test_build_disk_with_repart_grub2(
        self,
        mock_write_recovery_metadata_to_boot_image,
        mock_create_boot_files,
        mock_os_path_isdir,
        mock_SystemdRepart_create,
        mock_SystemIdentifier,
        mock_Temporary,
        mock_DataSync,
        mock_Command_run,
    ):
        self._setup_repart_builder()
        self.disk_builder.bootloader = 'grub2'
        mock_os_path_isdir.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'staging'
        self.setup.script_exists.return_value = False
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            efi_uuid = Reproducible.get_seeded_uuid('repart-partition-efi')
            root_uuid = Reproducible.get_seeded_uuid('repart-partition-root')
        efi_fs_uuid = SystemdRepart.get_filesystem_uuid(
            RepartPartition('efi', 'esp', 'EFI', efi_uuid, 'vfat')
        )
        root_fs_uuid = SystemdRepart.get_filesystem_uuid(
            RepartPartition('root', 'root', 'ROOT', root_uuid, 'ext4')
        )
        mock_SystemdRepart_create.return_value = [
            {'uuid': efi_uuid, 'offset': 1048576},
            {'uuid': root_uuid, 'offset': 156237824},
        ]
        filesystem_uuids = {'1048576': efi_fs_uuid, '156237824': root_fs_uuid}

        def blkid(command):
            return Mock(output=f'{filesystem_uuids[command[3]]}\n')

        mock_Command_run.side_effect = blkid
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            with patch('builtins.open', mock_open()):
                self.disk_builder._build_disk_with_repart(1024)

        assert (
            kiwi.builder.disk.create_boot_loader_config.call_args[1][
                'custom_args'
            ]['offline']
            is True
        )
        self.bootloader_config.setup_disk_boot_images.assert_called_once_with(
            root_fs_uuid, efi_fs_uuid
        )
        assert [
            command[0][0][3] for command in mock_Command_run.call_args_list
        ] == ['156237824', '1048576']
        assert self.disk_builder.xml_state.get_root_filesystem_uuid() == (
            root_fs_uuid
        )

        # filesystem UUID not as expected by the grub2 config
        filesystem_uuids['156237824'] = 'other-uuid'
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            with patch('builtins.open', mock_open()):
                with raises(KiwiDiskBuilderRepartError) as issue:
                    self.disk_builder._build_disk_with_repart(1024)
        assert format(issue.value) == (
            "Unexpected root filesystem UUID 'other-uuid' created by "
            f"systemd-repart, the grub2 config expects {root_fs_uuid!r}"
        )

        # filesystem not found in the systemd-repart result
        mock_SystemdRepart_create.return_value = []
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            with patch('builtins.open', mock_open()):
                with raises(KiwiDiskBuilderRepartError) as issue:
                    self.disk_builder._build_disk_with_repart(1024)
        assert "Unexpected root filesystem UUID ''" in format(issue.value)

    def test_disk_builder_from_description(self, tmp_path):
        with open('../data/example_disk_config.xml') as source:
            xml_data = source.read().replace(
                '<type image="oem"',
                '<type image="oem" disk_builder="systemd-repart"',
                1,
            )
        description_file = tmp_path / 'config.xml'
        description_file.write_text(xml_data)
        xml_state = XMLState(XMLDescription(str(description_file)).load())
        assert xml_state.build_type.get_disk_builder() == 'systemd-repart'
        disk_builder = DiskBuilder(xml_state, 'target_dir', 'root_dir')
        assert disk_builder.disk_builder == 'systemd-repart'
        assert self.disk_builder.disk_builder == 'kiwi'
