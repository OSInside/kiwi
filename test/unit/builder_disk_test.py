import mock
from mock import call

import kiwi

from .test_helper import *
from collections import OrderedDict
from kiwi.exceptions import *
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.builder.disk import DiskBuilder
from kiwi.storage.mapped_device import MappedDevice

from builtins import bytes


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
            'readonly': MappedDevice('/dev/readonly-root-device', mock.Mock()),
            'boot': MappedDevice('/dev/boot-device', mock.Mock()),
            'prep': MappedDevice('/dev/prep-device', mock.Mock()),
            'efi': MappedDevice('/dev/efi-device', mock.Mock())
        }
        self.id_map = {
            'kiwi_RootPart': 1,
            'kiwi_BootPart': 1
        }
        self.id_map_sorted = OrderedDict(
            sorted(self.id_map.items())
        )
        self.block_operation = mock.Mock()
        self.block_operation.get_blkid = mock.Mock(
            return_value='blkid_result'
        )
        self.block_operation.get_filesystem = mock.Mock(
            return_value='filesystem'
        )
        kiwi.builder.disk.BlockID = mock.Mock(
            return_value=self.block_operation
        )
        self.loop_provider = mock.Mock()
        kiwi.builder.disk.LoopDevice = mock.Mock(
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
        self.disk.get_public_partition_id_map = mock.Mock(
            return_value=self.id_map_sorted
        )
        self.disk.get_device = mock.Mock(
            return_value=self.device_map
        )
        kernel_info = mock.Mock()
        kernel_info.version = '1.2.3'
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock(
            return_value=kernel_info
        )
        self.kernel.get_xen_hypervisor = mock.Mock()
        self.kernel.copy_kernel = mock.Mock()
        self.kernel.copy_xen_hypervisor = mock.Mock()
        kiwi.builder.disk.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.disk.subformat = mock.Mock()
        self.disk.subformat.get_target_name_for_format = mock.Mock(
            return_value='some-target-format-name'
        )
        kiwi.builder.disk.DiskFormat = mock.Mock(
            return_value=self.disk.subformat
        )
        kiwi.builder.disk.Disk = mock.Mock(
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
        kiwi.builder.disk.BootLoaderInstall = mock.MagicMock(
            return_value=self.bootloader_install
        )
        self.bootloader_config = mock.Mock()
        kiwi.builder.disk.BootLoaderConfig = mock.MagicMock(
            return_value=self.bootloader_config
        )
        kiwi.builder.disk.DiskSetup = mock.MagicMock(
            return_value=self.disk_setup
        )
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'boot_dir'
        self.boot_image_task.kernel_filename = 'kernel'
        self.boot_image_task.initrd_filename = 'initrd'
        self.boot_image_task.xen_hypervisor_filename = 'xen_hypervisor'
        kiwi.builder.disk.BootImage = mock.Mock(
            return_value=self.boot_image_task
        )
        self.firmware = mock.Mock()
        self.firmware.efi_mode = mock.Mock(
            return_value='efi'
        )
        kiwi.builder.disk.FirmWare = mock.Mock(
            return_value=self.firmware
        )
        self.setup = mock.Mock()
        kiwi.builder.disk.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        self.boot_image_kiwi = mock.Mock()
        self.boot_image_kiwi.boot_root_directory = 'boot_dir_kiwi'
        kiwi.builder.disk.BootImageKiwi = mock.Mock(
            return_value=self.boot_image_kiwi
        )
        self.install_image = mock.Mock()
        kiwi.builder.disk.InstallImageBuilder = mock.Mock(
            return_value=self.install_image
        )
        self.raid_root = mock.Mock()
        kiwi.builder.disk.RaidDevice = mock.Mock(
            return_value=self.raid_root
        )
        self.luks_root = mock.Mock()
        kiwi.builder.disk.LuksDevice = mock.Mock(
            return_value=self.luks_root
        )
        self.disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.build_type_name = 'oem'
        self.machine = mock.Mock()
        self.machine.get_domain = mock.Mock(
            return_value='dom0'
        )
        self.disk_builder.machine = self.machine
        self.disk_builder.image_format = None

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_setup_ix86(self, mock_machine, mock_exists):
        mock_machine.return_value = 'i686'
        description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        assert disk_builder.arch == 'ix86'

    @raises(KiwiInstallMediaError)
    def test_create_invalid_type_for_install_media(self):
        self.disk_builder.build_type_name = 'vmx'
        self.disk_builder.create()

    @raises(KiwiVolumeManagerSetupError)
    def test_create_disk_overlay_with_volume_setup_not_supported(self):
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.volume_manager_name = 'lvm'
        self.disk_builder.create_disk()

    @patch_open
    @patch('os.path.exists')
    @patch('pickle.load')
    @patch('kiwi.builder.disk.Path.wipe')
    def test_create_install_media(
        self, mock_wipe, mock_load, mock_path, mock_open
    ):
        result_instance = mock.Mock()
        mock_path.return_value = True
        self.disk_builder.install_iso = True
        self.disk_builder.install_pxe = True
        self.disk_builder.create_install_media(result_instance)
        self.install_image.create_install_iso.assert_called_once_with()
        self.install_image.create_install_pxe_archive.assert_called_once_with()
        mock_wipe.assert_called_once_with('target_dir/boot_image.pickledump')

    @patch('os.path.exists')
    @raises(KiwiInstallMediaError)
    def test_create_install_media_no_boot_instance_found(self, mock_path):
        result_instance = mock.Mock()
        mock_path.return_value = False
        self.disk_builder.install_iso = True
        self.disk_builder.create_install_media(result_instance)

    @patch('os.path.exists')
    @patch('pickle.load')
    @raises(KiwiInstallMediaError)
    def test_create_install_media_pickle_load_error(self, mock_load, mock_path):
        result_instance = mock.Mock()
        mock_load.side_effect = Exception
        mock_path.return_value = True
        self.disk_builder.install_iso = True
        self.disk_builder.create_install_media(result_instance)

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('os.path.exists')
    def test_create_disk_standard_root(
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
        self.disk_builder.initrd_system = 'dracut'

        self.disk_builder.create_disk()

        self.setup.create_recovery_archive.assert_called_once_with()
        call = self.setup.export_modprobe_setup.call_args_list[0]
        assert self.setup.export_modprobe_setup.call_args_list[0] == \
            call('boot_dir')
        call = self.setup.export_modprobe_setup.call_args_list[1]
        assert self.setup.export_modprobe_setup.call_args_list[1] == \
            call('boot_dir_kiwi')

        self.setup.set_selinux_file_contexts.assert_called_once_with(
            '/etc/selinux/targeted/contexts/files/file_contexts'
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
        self.disk.create_prep_partition.assert_called_once_with(
            self.firmware.get_prep_partition_size()
        )
        self.disk.create_root_partition.assert_called_once_with(
            'all_free'
        )
        self.disk.map_partitions.assert_called_once_with()
        self.bootloader_config.setup_disk_boot_images.assert_called_once_with(
            '0815'
        )
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            initrd='initrd-1.2.3', kernel='vmlinuz-1.2.3', uuid='0815'
        )
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device'
        )

        self.boot_image_kiwi.prepare.assert_called_once_with()

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
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ])
        assert mock_open.call_args_list == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('/dev/some-loop', 'wb'),
            call('boot_dir_kiwi/config.partids', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n'),
            call('0x0f0f0f0f\n'),
            call(bytes(b'\x0f\x0f\x0f\x0f')),
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n')
        ]
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initrd-1.2.3']),
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir_kiwi'])
        ]
        self.setup.export_rpm_package_list.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_rpm_package_verification.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_dracut_initrd_system(
        self, mock_command, mock_open, mock_fs
    ):
        self.disk_builder.initrd_system = 'dracut'
        kernel = mock.Mock()
        kernel.version = '1.2.3'
        self.kernel.get_kernel.return_value = kernel
        self.disk_builder.create_disk()
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            uuid='0815', initrd='initrd-1.2.3', kernel='vmlinuz-1.2.3'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch('kiwi.builder.disk.FileSystemSquashFs')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.NamedTemporaryFile')
    def test_create_disk_standard_root_is_overlay(
        self, mock_temp, mock_getsize, mock_exists, mock_command,
        mock_open, mock_squashfs, mock_fs
    ):
        self.disk_builder.root_filesystem_is_overlay = True
        squashfs = mock.Mock()
        mock_squashfs.return_value = squashfs
        mock_getsize.return_value = 1048576
        tempfile = mock.Mock()
        tempfile.name = 'tempname'
        mock_temp.return_value = tempfile
        mock_exists.return_value = True
        self.disk_builder.create_disk()
        assert mock_squashfs.call_args_list == [
            call(device_provider=None, root_dir='root_dir'),
            call(device_provider=None, root_dir='root_dir')
        ]
        assert squashfs.create_on_file.call_args_list == [
            call(exclude=['var/cache/kiwi'], filename='tempname'),
            call(exclude=[
                'image', '.profile', '.kconfig', 'var/cache/kiwi',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ], filename='tempname')
        ]
        self.disk.create_root_readonly_partition.assert_called_once_with(51)
        assert mock_command.call_args_list.pop() == call(
            ['dd', 'if=tempname', 'of=/dev/readonly-root-device']
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_dracut_initrd_system_on_arm(
        self, mock_command, mock_open, mock_fs
    ):
        self.disk_builder.initrd_system = 'dracut'
        self.disk_builder.arch = 'aarch64'
        kernel = mock.Mock()
        kernel.version = '1.2.3'
        self.kernel.get_kernel.return_value = kernel
        self.disk_builder.create_disk()
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            uuid='0815', initrd='initrd-1.2.3', kernel='zImage-1.2.3'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    @raises(KiwiDiskBootImageError)
    def test_create_disk_standard_root_no_kernel_found(
        self, mock_command, mock_open, mock_fs
    ):
        self.kernel.get_kernel.return_value = False
        self.disk_builder.create_disk()

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    @raises(KiwiDiskBootImageError)
    def test_create_disk_standard_root_no_hypervisor_found(
        self, mock_command, mock_open, mock_fs
    ):
        self.kernel.get_xen_hypervisor.return_value = False
        self.disk_builder.create_disk()

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_s390_boot(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = mock.Mock(
            return_value=False
        )
        self.disk_builder.bootloader = 'grub2_s390x_emu'
        self.disk_builder.create_disk()
        assert mock_fs.call_args_list[1] == call(
            'ext2', self.device_map['boot'], 'root_dir/boot/zipl/'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_secure_boot(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = mock.Mock(
            return_value='uefi'
        )
        self.disk_builder.create_disk()
        bootloader = self.bootloader_config
        bootloader.setup_disk_boot_images.assert_called_once_with('0815')

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_mdraid_root(self, mock_command, mock_open, mock_fs):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.mdraid = 'mirroring'
        self.disk_builder.create_disk()
        self.disk.create_root_raid_partition.assert_called_once_with(
            'all_free'
        )
        self.raid_root.create_degraded_raid.assert_called_once_with(
            raid_level='mirroring'
        )
        self.raid_root.create_raid_config.assert_called_once_with(
            'boot_dir/etc/mdadm.conf'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_luks_root(self, mock_command, mock_open, mock_fs):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.luks = 'passphrase'
        self.disk_builder.create_disk()
        self.luks_root.create_crypto_luks.assert_called_once_with(
            passphrase='passphrase', os=None
        )
        self.luks_root.create_crypttab.assert_called_once_with(
            'root_dir/etc/crypttab'
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch('kiwi.builder.disk.VolumeManager')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    @patch('os.path.exists')
    def test_create_disk_volume_managed_root(
        self, mock_exists, mock_command, mock_open, mock_volume_manager, mock_fs
    ):
        mock_exists.return_value = True
        volume_manager = mock.Mock()
        volume_manager.get_device = mock.Mock(
            return_value={
                'root': MappedDevice('/dev/systemVG/LVRoot', mock.Mock())
            }
        )
        volume_manager.get_fstab = mock.Mock(
            return_value=['fstab_volume_entries']
        )
        mock_volume_manager.return_value = volume_manager
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = 'lvm'
        self.disk_builder.create_disk()
        self.disk.create_root_lvm_partition.assert_called_once_with(
            'all_free'
        )
        volume_manager.setup.assert_called_once_with('systemVG')
        volume_manager.create_volumes.assert_called_once_with('btrfs')
        volume_manager.mount_volumes.call_args_list[0].assert_called_once_with()
        volume_manager.get_fstab.assert_called_once_with(None, 'btrfs')
        volume_manager.sync_data.assert_called_once_with([
            'image', '.profile', '.kconfig', 'var/cache/kiwi',
            'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
        ])
        volume_manager.umount_volumes.call_args_list[0].assert_called_once_with()
        self.setup.create_fstab.assert_called_once_with(
            [
                'fstab_volume_entries',
                'UUID=blkid_result / filesystem ro 0 0',
                'UUID=blkid_result /boot filesystem defaults 0 0',
                'UUID=blkid_result /boot/efi filesystem defaults 0 0'
            ]
        )
        self.boot_image_task.setup.create_fstab.assert_called_once_with(
            [
                'fstab_volume_entries',
                'UUID=blkid_result / filesystem ro 0 0',
                'UUID=blkid_result /boot filesystem defaults 0 0',
                'UUID=blkid_result /boot/efi filesystem defaults 0 0'
            ]
        )

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_hybrid_gpt_requested(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.hybrid_mbr = True
        self.disk_builder.create_disk()
        self.disk.create_hybrid_mbr.assert_called_once_with()

    @patch('kiwi.builder.disk.DiskBuilder')
    def test_create(
        self, mock_builder
    ):
        result = mock.Mock()
        builder = mock.Mock()
        builder.create_disk.return_value = result
        builder.create_install_media.return_value = result
        mock_builder.return_value = builder

        self.disk_builder.create()

        builder.create_disk.assert_called_once_with()
        builder.create_install_media.assert_called_once_with(result)
        builder.create_disk_format.assert_called_once_with(result)

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_vboot_firmware_requested(
        self, mock_command, mock_open, mock_fs
    ):
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.firmware.vboot_mode.return_value = True
        self.disk_builder.firmware.get_vboot_partition_size.return_value = 42
        self.disk_builder.create_disk()
        self.disk.create_vboot_partition.assert_called_once_with(42)

    @patch('kiwi.builder.disk.FileSystem')
    @patch_open
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_format(self, mock_command, mock_open, mock_fs):
        result_instance = mock.Mock()
        filesystem = mock.Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.image_format = 'vmdk'
        self.disk_builder.create_disk_format(result_instance)
        self.disk.subformat.create_image_format.assert_called_once_with()
