import sys
from mock import (
    call, patch, mock_open, Mock, MagicMock
)
from pytest import raises
import kiwi

from ..test_helper import argv_kiwi_tests

from collections import OrderedDict
from collections import namedtuple
from builtins import bytes

from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.builder.disk import DiskBuilder
from kiwi.storage.mapped_device import MappedDevice

from kiwi.exceptions import (
    KiwiDiskBootImageError,
    KiwiInstallMediaError,
    KiwiVolumeManagerSetupError
)


class TestDiskBuilder:
    @patch('os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'

        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            else:
                return True

        mock_exists.side_effect = side_effect
        description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        self.device_map = {
            'root': MappedDevice('/dev/root-device', Mock()),
            'swap': MappedDevice('/dev/swap-device', Mock()),
            'readonly': MappedDevice('/dev/readonly-root-device', Mock()),
            'boot': MappedDevice('/dev/boot-device', Mock()),
            'prep': MappedDevice('/dev/prep-device', Mock()),
            'efi': MappedDevice('/dev/efi-device', Mock()),
            'spare': MappedDevice('/dev/spare-device', Mock())
        }
        self.id_map = {
            'kiwi_RootPart': 1,
            'kiwi_BootPart': 1
        }
        self.id_map_sorted = OrderedDict(
            sorted(self.id_map.items())
        )
        self.boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
        self.block_operation = Mock()
        self.block_operation.get_blkid = Mock(
            return_value='blkid_result'
        )
        self.block_operation.get_filesystem = Mock(
            return_value='blkid_result_fs'
        )
        kiwi.builder.disk.BlockID = Mock(
            return_value=self.block_operation
        )
        self.loop_provider = Mock()
        kiwi.builder.disk.LoopDevice = Mock(
            return_value=self.loop_provider
        )
        self.disk = Mock()
        provider = Mock()
        provider.get_device = Mock(
            return_value='/dev/some-loop'
        )
        self.disk.storage_provider = provider
        self.partitioner = Mock()
        self.partitioner.get_id = Mock(
            return_value=1
        )
        self.disk.partitioner = self.partitioner
        self.disk.get_uuid = Mock(
            return_value='0815'
        )
        self.disk.get_public_partition_id_map = Mock(
            return_value=self.id_map_sorted
        )
        self.disk.get_device = Mock(
            return_value=self.device_map
        )
        kernel_info = Mock()
        kernel_info.version = '1.2.3'
        kernel_info.name = 'vmlinuz-1.2.3-default'
        self.kernel = Mock()
        self.kernel.get_kernel = Mock(
            return_value=kernel_info
        )
        self.kernel.get_xen_hypervisor = Mock()
        self.kernel.copy_kernel = Mock()
        self.kernel.copy_xen_hypervisor = Mock()
        kiwi.builder.disk.Kernel = Mock(
            return_value=self.kernel
        )
        kiwi.builder.disk.Disk = Mock(
            return_value=self.disk
        )
        self.disk_setup = Mock()
        self.disk_setup.get_disksize_mbytes.return_value = 1024
        self.disk_setup.boot_partition_size.return_value = 0
        self.disk_setup.get_efi_label = Mock(
            return_value='EFI'
        )
        self.disk_setup.get_root_label = Mock(
            return_value='ROOT'
        )
        self.disk_setup.get_boot_label = Mock(
            return_value='BOOT'
        )
        self.disk_setup.need_boot_partition = Mock(
            return_value=True
        )
        self.bootloader_install = Mock()
        kiwi.builder.disk.BootLoaderInstall.new = MagicMock(
            return_value=self.bootloader_install
        )
        self.bootloader_config = Mock()
        self.bootloader_config.get_boot_cmdline = Mock(
            return_value='boot_cmdline'
        )
        kiwi.builder.disk.BootLoaderConfig.new = MagicMock(
            return_value=self.bootloader_config
        )
        kiwi.builder.disk.DiskSetup = MagicMock(
            return_value=self.disk_setup
        )
        self.boot_image_task = Mock()
        self.boot_image_task.boot_root_directory = 'boot_dir'
        self.boot_image_task.kernel_filename = 'kernel'
        self.boot_image_task.initrd_filename = 'initrd'
        self.boot_image_task.xen_hypervisor_filename = 'xen_hypervisor'
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='linux.vmx',
            initrd_name='initrd.vmx'
        )
        kiwi.builder.disk.BootImage.new = Mock(
            return_value=self.boot_image_task
        )
        self.firmware = Mock()
        self.firmware.get_legacy_bios_partition_size.return_value = 0
        self.firmware.get_efi_partition_size.return_value = 0
        self.firmware.get_prep_partition_size.return_value = 0
        self.firmware.efi_mode = Mock(
            return_value='efi'
        )
        kiwi.builder.disk.FirmWare = Mock(
            return_value=self.firmware
        )
        self.setup = Mock()
        kiwi.builder.disk.SystemSetup = Mock(
            return_value=self.setup
        )
        self.install_image = Mock()
        kiwi.builder.disk.InstallImageBuilder = Mock(
            return_value=self.install_image
        )
        self.raid_root = Mock()
        self.raid_root.get_device.return_value = MappedDevice(
            '/dev/md0', Mock()
        )
        kiwi.builder.disk.RaidDevice = Mock(
            return_value=self.raid_root
        )
        self.luks_root = Mock()
        kiwi.builder.disk.LuksDevice = Mock(
            return_value=self.luks_root
        )
        self.fstab = Mock()
        kiwi.builder.disk.Fstab = Mock(
            return_value=self.fstab
        )
        self.disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )
        self.disk_builder.root_filesystem_is_overlay = False
        self.disk_builder.build_type_name = 'oem'
        self.disk_builder.image_format = None

    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('platform.machine')
    def test_setup_ix86(self, mock_machine):
        mock_machine.return_value = 'i686'
        description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        disk_builder = DiskBuilder(
            XMLState(description.load()), 'target_dir', 'root_dir'
        )
        assert disk_builder.arch == 'ix86'

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_invalid_type_for_install_media(
        self, mock_cmd, mock_fs
    ):
        self.disk_builder.build_type_name = 'kis'
        with patch('builtins.open'):
            with raises(KiwiInstallMediaError):
                self.disk_builder.create_disk()

    def test_create_disk_overlay_with_volume_setup_not_supported(self):
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.volume_manager_name = 'lvm'
        with raises(KiwiVolumeManagerSetupError):
            self.disk_builder.create_disk()

    @patch('os.path.exists')
    @patch('pickle.load')
    @patch('kiwi.builder.disk.Path.wipe')
    def test_create_install_media(
        self, mock_wipe, mock_load, mock_path
    ):
        result_instance = Mock()
        mock_path.return_value = True
        self.disk_builder.install_iso = True
        self.disk_builder.install_pxe = True
        with patch('builtins.open'):
            self.disk_builder.create_install_media(result_instance)
        self.install_image.create_install_iso.assert_called_once_with()
        self.install_image.create_install_pxe_archive.assert_called_once_with()
        mock_wipe.assert_called_once_with('target_dir/boot_image.pickledump')

    @patch('os.path.exists')
    def test_create_install_media_no_boot_instance_found(self, mock_path):
        result_instance = Mock()
        mock_path.return_value = False
        self.disk_builder.install_iso = True
        with raises(KiwiInstallMediaError):
            self.disk_builder.create_install_media(result_instance)

    @patch('os.path.exists')
    @patch('pickle.load')
    def test_create_install_media_pickle_load_error(self, mock_load, mock_path):
        result_instance = Mock()
        mock_load.side_effect = Exception
        mock_path.return_value = True
        self.disk_builder.install_iso = True
        with raises(KiwiInstallMediaError):
            self.disk_builder.create_install_media(result_instance)

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    def test_create_disk_standard_root_with_kiwi_initrd(
        self, mock_path, mock_grub_dir, mock_command, mock_rand, mock_fs
    ):
        mock_path.return_value = True
        mock_rand.return_value = 15
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'kiwi'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        self.setup.create_recovery_archive.assert_called_once_with()

        call = self.setup.export_modprobe_setup.call_args_list[0]
        assert self.setup.export_modprobe_setup.call_args_list[0] == \
            call('boot_dir')

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
        self.disk.create_swap_partition.assert_called_once_with(
            128
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
        self.bootloader_config.write_meta_data.assert_called_once_with(
            boot_options='', root_uuid='0815'
        )
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            boot_options={
                'boot_device': '/dev/boot-device',
                'root_device': '/dev/readonly-root-device',
                'firmware': self.firmware,
                'target_removable': None,
                'efi_device': '/dev/efi-device',
                'prep_device': '/dev/prep-device'
            }
        )
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device'
        )

        self.boot_image_task.prepare.assert_called_once_with()

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
                'image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ])
        assert m_open.call_args_list[0:4] == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('boot_dir/config.bootoptions', 'w'),
            call('/dev/some-loop', 'wb')
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
        self.block_operation.get_blkid.assert_has_calls(
            [call('PARTUUID')]
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('random.randrange')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('kiwi.builder.disk.SystemSetup')
    def test_create_disk_standard_root_with_dracut_initrd(
        self, mock_SystemSetup, mock_path, mock_grub_dir,
        mock_command, mock_rand, mock_fs
    ):
        self.boot_image_task.get_boot_names.return_value = self.boot_names_type(
            kernel_name='vmlinuz-1.2.3-default',
            initrd_name='initramfs-1.2.3.img'
        )
        mock_path.return_value = True
        mock_rand.return_value = 15
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.initrd_system = 'dracut'
        self.setup.script_exists.return_value = True
        disk_system = Mock()
        mock_SystemSetup.return_value = disk_system

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        self.setup.create_recovery_archive.assert_called_once_with()
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
        self.bootloader_config.write_meta_data.assert_called_once_with(
            boot_options='', root_uuid='0815'
        )
        self.bootloader_config.setup_disk_image_config.assert_called_once_with(
            boot_options={
                'boot_device': '/dev/boot-device',
                'root_device': '/dev/readonly-root-device',
                'firmware': self.firmware,
                'target_removable': None,
                'efi_device': '/dev/efi-device',
                'prep_device': '/dev/prep-device'
            }
        )
        self.setup.script_exists.assert_called_once_with('disk.sh')
        disk_system.import_description.assert_called_once_with()
        disk_system.call_disk_script.assert_called_once_with()
        self.setup.call_edit_boot_config_script.assert_called_once_with(
            'btrfs', 1
        )
        self.bootloader_install.install.assert_called_once_with()
        self.setup.call_edit_boot_install_script.assert_called_once_with(
            'target_dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.raw',
            '/dev/boot-device'
        )
        self.boot_image_task.prepare.assert_called_once_with()
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
                'image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ])
        assert m_open.call_args_list == [
            call('boot_dir/config.partids', 'w'),
            call('root_dir/boot/mbrid', 'w'),
            call('boot_dir/config.bootoptions', 'w'),
            call('/dev/some-loop', 'wb')
        ]
        assert m_open.return_value.write.call_args_list == [
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n'),
            call('0x0f0f0f0f\n'),
            call('boot_cmdline\n'),
            call(bytes(b'\x0f\x0f\x0f\x0f'))
        ]
        assert mock_command.call_args_list == [
            call(['cp', 'root_dir/recovery.partition.size', 'boot_dir']),
            call(['mv', 'initrd', 'root_dir/boot/initramfs-1.2.3.img'])
        ]
        self.block_operation.get_blkid.assert_has_calls(
            [call('PARTUUID')]
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        assert self.boot_image_task.include_file.call_args_list == [
            call('/config.partids'),
            call('/recovery.partition.size')
        ]
        self.boot_image_task.include_module.assert_called_once_with(
            'kiwi-repart'
        )
        self.boot_image_task.omit_module.assert_called_once_with('multipath')
        assert self.boot_image_task.write_system_config_file.call_args_list == \
            []

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.FileSystemSquashFs')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.builder.disk.NamedTemporaryFile')
    @patch('random.randrange')
    def test_create_disk_standard_root_is_overlay(
        self, mock_rand, mock_temp, mock_getsize, mock_exists,
        mock_grub_dir, mock_command, mock_squashfs, mock_fs
    ):
        mock_rand.return_value = 15
        self.disk_builder.root_filesystem_is_overlay = True
        self.disk_builder.volume_manager_name = None
        squashfs = Mock()
        mock_squashfs.return_value = squashfs
        mock_getsize.return_value = 1048576
        tempfile = Mock()
        tempfile.name = 'tempname'
        mock_temp.return_value = tempfile
        mock_exists.return_value = True
        self.disk_builder.initrd_system = 'dracut'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_builder.create_disk()

        assert mock_squashfs.call_args_list == [
            call(
                custom_args={'compression': None},
                device_provider=None, root_dir='root_dir'
            ), call(
                custom_args={'compression': None},
                device_provider=None, root_dir='root_dir'
            )
        ]
        assert squashfs.create_on_file.call_args_list == [
            call(exclude=['var/cache/kiwi'], filename='tempname'),
            call(exclude=[
                'image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ], filename='tempname')
        ]
        self.disk.create_root_readonly_partition.assert_called_once_with(11)
        assert mock_command.call_args_list[2] == call(
            ['dd', 'if=tempname', 'of=/dev/readonly-root-device']
        )
        assert m_open.return_value.write.call_args_list == [
            call('kiwi_BootPart="1"\n'),
            call('kiwi_RootPart="1"\n'),
            call('0x0f0f0f0f\n'),
            call('boot_cmdline\n'),
            call(b'\x0f\x0f\x0f\x0f')
        ]
        assert self.boot_image_task.include_module.call_args_list == [
            call('kiwi-overlay'), call('kiwi-repart')
        ]
        self.boot_image_task.omit_module.assert_called_once_with('multipath')
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={'modules': ['kiwi-overlay']}
        )

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_no_hypervisor_found(
        self, mock_command, mock_fs
    ):
        self.kernel.get_xen_hypervisor.return_value = False
        self.disk_builder.volume_manager_name = None
        self.disk_builder.xen_server = True

        with patch('builtins.open'):
            with raises(KiwiDiskBootImageError):
                self.disk_builder.create_disk()

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    def test_create_disk_standard_root_xen_server_boot(
        self, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.xen_server = True
        self.firmware.efi_mode = Mock(
            return_value=False
        )

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.kernel.copy_xen_hypervisor.assert_called_once_with(
            'root_dir', '/boot/xen.gz'
        )

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_standard_root_s390_boot(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        self.disk_builder.arch = 's390x'
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = Mock(
            return_value=False
        )
        self.disk_builder.bootloader = 'grub2_s390x_emu'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.bootloader_config.write.assert_called_once_with()

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_standard_root_secure_boot(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        with patch('builtins.open'):
            self.disk_builder.create_disk()

        bootloader = self.bootloader_config
        bootloader.setup_disk_boot_images.assert_called_once_with('0815')

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_mdraid_root(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.mdraid = 'mirroring'
        self.disk.public_partition_id_map = self.id_map

        with patch('builtins.open'):
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
        assert self.disk.public_partition_id_map == {
            'kiwi_RaidPart': 1, 'kiwi_RootPart': 1, 'kiwi_BootPart': 1,
            'kiwi_RaidDev': '/dev/md0'
        }

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_luks_root(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.luks = 'passphrase'
        self.disk_setup.need_boot_partition.return_value = False
        self.disk_builder.boot_is_crypto = True

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.luks_root.create_crypto_luks.assert_called_once_with(
            passphrase='passphrase', os=None, keyfile='root_dir/.root.keyfile'
        )
        self.luks_root.create_crypttab.assert_called_once_with(
            'root_dir/etc/crypttab'
        )
        assert self.boot_image_task.include_file.call_args_list == [
            call('/.root.keyfile'),
            call('/config.partids'),
            call('/etc/crypttab')
        ]
        self.boot_image_task.write_system_config_file.assert_called_once_with(
            config={'install_items': ['/.root.keyfile']},
            config_file='root_dir/etc/dracut.conf.d/99-luks-boot.conf'
        )

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.VolumeManager.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    @patch('os.path.exists')
    def test_create_disk_volume_managed_root(
        self, mock_exists, mock_grub_dir, mock_command,
        mock_volume_manager, mock_fs
    ):
        mock_exists.return_value = True
        volume_manager = Mock()
        volume_manager.get_device = Mock(
            return_value={
                'root': MappedDevice('/dev/systemVG/LVRoot', Mock()),
                'swap': MappedDevice('/dev/systemVG/LVSwap', Mock())
            }
        )
        volume_manager.get_fstab = Mock(
            return_value=['fstab_volume_entries']
        )
        mock_volume_manager.return_value = volume_manager
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = 'lvm'

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.disk.create_root_lvm_partition.assert_called_once_with('all_free')
        volume_manager.setup.assert_called_once_with('systemVG')
        volume_manager.create_volumes.assert_called_once_with('btrfs')
        volume_manager.mount_volumes.call_args_list[0].assert_called_once_with()
        assert volume_manager.get_fstab.call_args_list == [
            call(None, 'btrfs'),
            call(None, 'btrfs')
        ]
        volume_manager.sync_data.assert_called_once_with(
            [
                'image', '.profile', '.kconfig', '.buildenv', 'var/cache/kiwi',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ]
        )
        volume_manager.umount_volumes.call_args_list[0].assert_called_once_with(
        )
        self.setup.create_fstab.assert_called_once_with(
            self.disk_builder.fstab
        )
        self.boot_image_task.setup.create_fstab.assert_called_once_with(
            self.disk_builder.fstab
        )

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_hybrid_gpt_requested(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.hybrid_mbr = True

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.disk.create_hybrid_mbr.assert_called_once_with()

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_force_mbr_requested(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.force_mbr = True

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.disk.create_mbr.assert_called_once_with()

    @patch('kiwi.builder.disk.DiskBuilder')
    def test_create(
        self, mock_builder
    ):
        result = Mock()
        builder = Mock()
        builder.create_disk.return_value = result
        builder.create_install_media.return_value = result
        mock_builder.return_value = builder

        self.disk_builder.create()

        builder.create_disk.assert_called_once_with()
        builder.create_install_media.assert_called_once_with(result)
        builder.append_unpartitioned_space.assert_called_once_with()
        builder.create_disk_format.assert_called_once_with(result)

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.Defaults.get_grub_boot_directory_name')
    def test_create_disk_spare_part_requested(
        self, mock_grub_dir, mock_command, mock_fs
    ):
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.volume_manager_name = None
        self.disk_builder.install_media = False
        self.disk_builder.spare_part_mbsize = 42
        self.disk_builder.spare_part_fs = 'ext4'
        self.disk_builder.spare_part_mountpoint = '/var'
        self.disk_builder.spare_part_is_last = False

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.disk.create_spare_partition.assert_called_once_with(42)
        assert mock_fs.call_args_list[0] == call(
            self.disk_builder.spare_part_fs,
            self.device_map['spare'],
            'root_dir/var/',
            {'fs_attributes': None}
        )
        assert filesystem.sync_data.call_args_list.pop() == call(
            [
                'image', '.profile', '.kconfig', '.buildenv',
                'var/cache/kiwi', 'var/*', 'var/.*',
                'boot/*', 'boot/.*', 'boot/efi/*', 'boot/efi/.*'
            ]
        )
        assert [
            call('UUID=blkid_result / blkid_result_fs ro 0 0'),
            call('UUID=blkid_result /boot blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result /boot/efi blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result /var blkid_result_fs defaults 0 0'),
            call('UUID=blkid_result swap blkid_result_fs defaults 0 0'),
        ] in self.disk_builder.fstab.add_entry.call_args_list

        self.disk.create_root_partition.reset_mock()
        self.disk.create_spare_partition.reset_mock()
        self.disk_builder.spare_part_is_last = True
        self.disk_builder.disk_resize_requested = False

        with patch('builtins.open'):
            self.disk_builder.create_disk()

        self.disk.create_spare_partition.assert_called_once_with(
            'all_free'
        )

    @patch('kiwi.builder.disk.LoopDevice')
    @patch('kiwi.builder.disk.Partitioner.new')
    @patch('kiwi.builder.disk.DiskFormat.new')
    def test_append_unpartitioned_space(
        self, mock_diskformat, mock_partitioner, mock_loopdevice
    ):
        loopdevice = Mock()
        mock_loopdevice.return_value = loopdevice
        partitioner = Mock()
        mock_partitioner.return_value = partitioner
        disk_format = Mock()
        mock_diskformat.return_value = disk_format
        self.disk_builder.unpartitioned_bytes = 1024
        self.disk_builder.append_unpartitioned_space()
        disk_format.resize_raw_disk.assert_called_once_with(
            1024, append=True
        )
        loopdevice.create.assert_called_once_with(overwrite=False)
        assert partitioner.resize_table.called

    @patch('kiwi.builder.disk.FileSystem.new')
    @patch('kiwi.builder.disk.Command.run')
    @patch('kiwi.builder.disk.DiskFormat.new')
    def test_create_disk_format(self, mock_DiskFormat, mock_command, mock_fs):
        disk_subformat = Mock()
        mock_DiskFormat.return_value = disk_subformat
        result_instance = Mock()
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.disk_builder.install_media = False
        self.disk_builder.image_format = 'vmdk'

        with patch('builtins.open'):
            self.disk_builder.create_disk_format(result_instance)

        disk_subformat.create_image_format.assert_called_once_with()
