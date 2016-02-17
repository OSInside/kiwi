from nose.tools import *
from mock import patch
from mock import call
import mock

import kiwi

from . import nose_helper
from collections import OrderedDict
from kiwi.exceptions import *
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.disk_builder import DiskBuilder
from kiwi.mapped_device import MappedDevice


class TestDiskBuilder(object):
    @patch('os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        self.device_map = {
            'root': MappedDevice('/dev/root-device', mock.Mock()),
            'boot': MappedDevice('/dev/boot-device', mock.Mock()),
            'efi': MappedDevice('/dev/efi-device', mock.Mock())
        }
        self.id_map = {
            'kiwi_RootPart': 1,
            'kiwi_BootPart': 1
        }
        self.id_map_sorted = OrderedDict(
            sorted(self.id_map.items())
        )
        self.loop_provider = mock.Mock()
        kiwi.disk_builder.LoopDevice = mock.Mock(
            return_value=self.loop_provider
        )
        self.disk = mock.Mock()
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/some-loop'
        )
        self.disk.storage_provider = provider
        self.partitioner = mock.Mock()
        self.partitioner.get_id = mock.Mock(
            return_value=1
        )
        self.disk.partitioner = self.partitioner
        self.disk.get_uuid = mock.Mock(
            return_value='0815'
        )
        self.disk.get_partition_id_map = mock.Mock(
            return_value=self.id_map_sorted
        )
        self.disk.get_device = mock.Mock(
            return_value=self.device_map
        )
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock()
        self.kernel.get_xen_hypervisor = mock.Mock()
        self.kernel.copy_kernel = mock.Mock()
        self.kernel.copy_xen_hypervisor = mock.Mock()
        kiwi.disk_builder.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.disk_format = mock.Mock()
        self.disk_format.get_target_name_for_format = mock.Mock(
            return_value='some-target-format-name'
        )
        kiwi.disk_builder.DiskFormat = mock.Mock(
            return_value=self.disk_format
        )
        kiwi.disk_builder.Disk = mock.Mock(
            return_value=self.disk
        )
        self.disk_setup = mock.Mock()
        self.disk_setup.get_efi_label = mock.Mock(
            return_value='EFI'
        )
        self.disk_setup.get_root_label = mock.Mock(
            return_value='ROOT'
        )
        self.disk_setup.get_boot_label = mock.Mock(
            return_value='BOOT'
        )
        self.disk_setup.need_boot_partition = mock.Mock(
            return_value=True
        )
        self.bootloader_install = mock.Mock()
        kiwi.disk_builder.BootLoaderInstall = mock.MagicMock(
            return_value=self.bootloader_install
        )
        self.bootloader_config = mock.Mock()
        kiwi.disk_builder.BootLoaderConfig = mock.MagicMock(
            return_value=self.bootloader_config
        )
        kiwi.disk_builder.DiskSetup = mock.MagicMock(
            return_value=self.disk_setup
        )
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'boot_dir'
        self.boot_image_task.kernel_filename = 'kernel'
        self.boot_image_task.initrd_filename = 'initrd'
        self.boot_image_task.xen_hypervisor_filename = 'xen_hypervisor'
        kiwi.disk_builder.BootImageTask = mock.Mock(
            return_value=self.boot_image_task
        )
        self.firmware = mock.Mock()
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        kiwi.disk_builder.FirmWare = mock.Mock(
            return_value=self.firmware
        )
        self.system_setup = mock.Mock()
        kiwi.disk_builder.SystemSetup = mock.Mock(
            return_value=self.system_setup
        )
        self.install_image = mock.Mock()
        kiwi.disk_builder.InstallImageBuilder = mock.Mock(
            return_value=self.install_image
        )
        self.raid_root = mock.Mock()
        kiwi.disk_builder.RaidDevice = mock.Mock(
            return_value=self.raid_root
        )
        self.luks_root = mock.Mock()
        kiwi.disk_builder.LuksDevice = mock.Mock(
            return_value=self.luks_root
        )
        self.disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        self.disk_builder.build_type_name = 'oem'
        self.machine = mock.Mock()
        self.machine.get_domain = mock.Mock(
            return_value='dom0'
        )
        self.disk_builder.machine = self.machine
        self.disk_builder.image_format = None

    @raises(KiwiInstallMediaError)
    def test_create_invalid_type_for_install_media(self):
        self.disk_builder.build_type_name = 'vmx'
        self.disk_builder.create()

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('random.randrange')
    @patch('kiwi.disk_builder.Command.run')
    @patch('os.path.exists')
    def test_create_standard_root(
        self, mock_path, mock_command, mock_rand, mock_open, mock_fs
    ):
        mock_path.return_value = True
        mock_rand.return_value = 15
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_iso = True
        self.disk_builder.install_pxe = True

        self.disk_builder.create()

        self.system_setup.create_recovery_archive.assert_called_once_with()
        self.system_setup.export_modprobe_setup.assert_called_once_with(
            'boot_dir'
        )
        self.disk_setup.get_disksize_mbytes.assert_called_once_with()
        self.loop_provider.create.assert_called_once_with()
        self.disk.wipe.assert_called_once_with()
        self.disk.create_efi_csm_partition.assert_called_once_with(
            self.firmware.get_legacy_bios_partition_size()
        )
        self.disk.create_efi_partition.assert_called_once_with(
            self.firmware.get_efi_partition_size()
        )
        self.disk.create_boot_partition.assert_called_once_with(
            self.disk_setup.boot_partition_size()
        )
        self.disk.create_root_partition.assert_called_once_with(
            'all_free'
        )
        self.disk.map_partitions.assert_called_once_with()
        self.bootloader_config.setup_disk_boot_images.assert_called_once_with(
            '0815'
        )
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            '0815'
        )
        self.system_setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.system_setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device'
        )
        self.install_image.create_install_iso.assert_called_once_with()
        self.install_image.create_install_pxe_archive.assert_called_once_with()

        call = filesystem.create_on_device.call_args_list[0]
        assert filesystem.create_on_device.call_args_list[0] == \
            call(label='EFI')
        call = filesystem.create_on_device.call_args_list[1]
        assert filesystem.create_on_device.call_args_list[1] == \
            call(label='BOOT')
        call = filesystem.create_on_device.call_args_list[2]
        assert filesystem.create_on_device.call_args_list[2] == \
            call(label='ROOT')

        call = filesystem.sync_data.call_args_list[0]
        assert filesystem.sync_data.call_args_list[0] == \
            call()
        call = filesystem.sync_data.call_args_list[1]
        assert filesystem.sync_data.call_args_list[1] == \
            call(['efi/*'])
        call = filesystem.sync_data.call_args_list[2]
        assert filesystem.sync_data.call_args_list[2] == \
            call([
                'image', '.profile', '.kconfig', 'var/cache/kiwi',
                'boot/*', 'boot/.*'
            ])
        assert mock_open.call_args_list == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('/dev/some-loop', 'wb')
        ]
        assert file_mock.write.call_args_list == [
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n'),
            call('0x0f0f0f0f\n'),
            call(b'\x0f\x0f\x0f\x0f')
        ]
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initrd.vmx']),
        ]
        self.kernel.copy_kernel.assert_called_once_with(
            'root_dir', '/boot/linux.vmx'
        )
        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'root_dir', '/boot/xen.gz'
        )

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    @raises(KiwiDiskBootImageError)
    def test_create_standard_root_no_kernel_found(
        self, mock_command, mock_open, mock_fs
    ):
        self.kernel.get_kernel.return_value = False
        self.disk_builder.create()

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    @raises(KiwiDiskBootImageError)
    def test_create_standard_root_no_hypervisor_found(
        self, mock_command, mock_open, mock_fs
    ):
        self.kernel.get_xen_hypervisor.return_value = False
        self.disk_builder.create()

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_standard_root_s390_boot(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = mock.Mock(
            return_value=False
        )
        self.disk_builder.bootloader = 'grub2_s390x_emu'
        self.disk_builder.create()
        assert mock_fs.call_args_list[1] == call(
            'ext2', self.device_map['boot'], 'root_dir/boot/zipl/'
        )

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_standard_root_secure_boot(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        self.disk_builder.create()
        bootloader = self.bootloader_config
        bootloader.setup_disk_boot_images.assert_called_once_with('0815')

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_mdraid_root(self, mock_command, mock_open, mock_fs):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.mdraid = 'mirroring'
        self.disk_builder.create()
        self.disk.create_root_raid_partition.assert_called_once_with(
            'all_free'
        )
        self.raid_root.create_degraded_raid.assert_called_once_with(
            raid_level='mirroring'
        )
        self.raid_root.create_raid_config.assert_called_once_with(
            'boot_dir/etc/mdadm.conf'
        )

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_luks_root(self, mock_command, mock_open, mock_fs):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.luks = 'passphrase'
        self.disk_builder.create()
        self.luks_root.create_crypto_luks.assert_called_once_with(
            passphrase='passphrase', os=None
        )
        self.luks_root.create_crypttab.assert_called_once_with(
            'root_dir/etc/crypttab'
        )

    @patch('kiwi.disk_builder.FileSystem')
    @patch('kiwi.disk_builder.VolumeManager')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_volume_managed_root(
        self, mock_command, mock_open, mock_volume_manager, mock_fs
    ):
        volume_manager = mock.Mock()
        volume_manager.get_device = mock.Mock(
            return_value={'root': '/dev/systemVG/LVRoot'}
        )
        mock_volume_manager.return_value = volume_manager
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = 'lvm'
        self.disk_builder.create()
        self.disk.create_root_lvm_partition.assert_called_once_with(
            'all_free'
        )
        volume_manager.setup.assert_called_once_with('systemVG')
        volume_manager.create_volumes.assert_called_once_with('btrfs')
        volume_manager.mount_volumes.assert_called_once_with()
        volume_manager.sync_data.assert_called_once_with([
            'image', '.profile', '.kconfig', 'var/cache/kiwi',
            'boot/*', 'boot/.*'
        ])

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    def test_create_with_image_format(self, mock_command, mock_open, mock_fs):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.image_format = 'vmdk'
        self.disk_builder.create()
        self.disk_format.create_image_format.assert_called_once_with()

    @patch('kiwi.disk_builder.FileSystem')
    @patch('builtins.open')
    @patch('kiwi.disk_builder.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_create_with_ignore_format_on_install_media(
        self, mock_log_warn, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = True
        self.disk_builder.image_format = 'vmdk'
        self.disk_builder.create()
        assert mock_log_warn.called
