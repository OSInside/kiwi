# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import os

# project
from bootloader_config import BootLoaderConfig
from bootloader_install import BootLoaderInstall
from image_identifier import ImageIdentifier
from internal_boot_image_task import BootImageTask
from disk_setup import DiskSetup
from loop_device import LoopDevice
from firmware import FirmWare
from disk import Disk
from raid_device import RaidDevice
from luks_device import LuksDevice
from filesystem import FileSystem
from volume_manager import VolumeManager
from logger import log
from command import Command
from system_setup import SystemSetup
from install_image_builder import InstallImageBuilder
from kernel import Kernel

from exceptions import (
    KiwiDiskBootImageError,
    KiwiInstallMediaError
)


class DiskBuilder(object):
    """
        Disk image builder
    """
    def __init__(self, xml_state, target_dir, source_dir):
        self.source_dir = source_dir
        self.custom_filesystem_args = None
        self.build_type_name = xml_state.get_build_type_name()
        self.install_iso = xml_state.build_type.get_installiso()
        self.install_stick = xml_state.build_type.get_installstick()
        self.install_pxe = xml_state.build_type.get_installpxe()
        self.blocksize = xml_state.build_type.get_target_blocksize()
        self.volume_manager_name = xml_state.get_volume_management()
        self.volumes = xml_state.get_volumes()
        self.volume_group_name = xml_state.get_volume_group_name()
        self.mdraid = xml_state.build_type.get_mdraid()
        self.luks = xml_state.build_type.get_luks()
        self.luks_os = xml_state.build_type.get_luksOS()
        self.machine = xml_state.get_build_type_machine_section()
        self.requested_filesystem = xml_state.build_type.get_filesystem()
        self.requested_boot_filesystem = \
            xml_state.build_type.get_bootfilesystem()
        self.bootloader = xml_state.build_type.get_bootloader()
        self.bootloader_config = BootLoaderConfig(
            self.bootloader, xml_state, source_dir
        )
        self.disk_setup = DiskSetup(
            xml_state, source_dir
        )
        self.boot_image_task = BootImageTask(
            xml_state, target_dir
        )
        self.firmware = FirmWare(
            xml_state.build_type.get_firmware()
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, description_dir=None, root_dir=self.source_dir
        )
        self.diskname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(), '.raw'
            ]
        )
        self.install_image = InstallImageBuilder(
            xml_state, target_dir, self.boot_image_task
        )
        # an instance of a class with the sync_data capability
        # representing the entire image system except for the boot/ area
        # which could live on another part of the disk
        self.system = None

        # an instance of a class with the sync_data capability
        # representing the boot/ area of the disk if not part of
        # self.system
        self.system_boot = None

        # an instance of a class with the sync_data capability
        # representing the boot/efi area of the disk
        self.system_efi = None

    def create(self):
        if self.__install_image_requested() and self.build_type_name != 'oem':
            raise KiwiInstallMediaError(
                'Install media requires oem type setup, got %s' %
                self.build_type_name
            )
        if not self.boot_image_task.required():
            raise KiwiDiskBootImageError(
                'disk images requires a boot setup in the type definition'
            )

        # prepare boot(initrd) root system
        log.info('Preparing boot system')
        self.boot_image_task.prepare()

        # precalculate needed disk size
        disksize_mbytes = self.disk_setup.get_disksize_mbytes()

        # create the disk
        log.info('Creating raw disk image %s', self.diskname)
        loop_provider = LoopDevice(
            self.diskname, disksize_mbytes, self.blocksize
        )
        loop_provider.create()

        self.disk = Disk(
            self.firmware.get_partition_table_type(), loop_provider
        )

        # create disk partitions and instance device map
        device_map = self.__build_and_map_disk_partitions()

        # create raid on current root device if requested
        if self.mdraid:
            self.raid_root = RaidDevice(device_map['root'])
            self.raid_root.create_degraded_raid(raid_level=self.mdraid)
            device_map['root'] = self.raid_root.get_device()

        # create luks on current root device if requested
        if self.luks:
            self.luks_root = LuksDevice(device_map['root'])
            self.luks_root.create_crypto_luks(
                passphrase=self.luks, os=self.luks_os
            )
            device_map['root'] = self.luks_root.get_device()

        # create filesystems on boot partition(s) if any
        self.__build_boot_filesystems(device_map)

        # create volumes and filesystems for root system
        if self.volume_manager_name:
            volume_manager_custom_parameters = {
                'root_filesystem_args': self.custom_filesystem_args,
                'root_label': self.disk_setup.get_root_label(),
            }
            volume_manager = VolumeManager(
                self.volume_manager_name, device_map['root'],
                self.source_dir + '/',
                self.volumes, volume_manager_custom_parameters
            )
            volume_manager.setup(
                self.volume_group_name
            )
            volume_manager.create_volumes(
                self.requested_filesystem
            )
            volume_manager.mount_volumes()
            self.system = volume_manager
            device_map['root'] = volume_manager.get_device()['root']
        else:
            log.info(
                'Creating root(%s) filesystem on %s',
                self.requested_filesystem, device_map['root'].get_device()
            )
            filesystem = FileSystem(
                self.requested_filesystem, device_map['root'],
                self.source_dir + '/',
                self.custom_filesystem_args
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_root_label()
            )
            self.system = filesystem

        # create a random image identifier
        self.mbrid = ImageIdentifier()
        self.mbrid.calculate_id()

        # create first stage metadata to boot
        self.__write_partition_id_config_to_boot_image()

        self.__write_recovery_metadata_to_boot_image()

        self.__write_image_identifier_to_system_image()

        self.__write_raid_config_to_boot_image()

        self.__write_crypttab_to_system_image()

        # create initrd cpio archive
        self.boot_image_task.create_initrd(self.mbrid)

        # create second stage metadata to boot
        self.__copy_first_boot_files_to_system_image()

        self.__write_bootloader_config_to_system_image(device_map)

        self.__install_bootloader(device_map)

        self.mbrid.write_to_disk(
            self.disk.storage_provider
        )

        # syncing system data to disk image
        log.info('Syncing system to image')
        if self.system_efi:
            log.info('--> Syncing EFI boot data to EFI partition')
            self.system_efi.sync_data()

        if self.system_boot:
            log.info('--> Syncing boot data at extra partition')
            self.system_boot.sync_data(
                self.__get_exclude_list_for_boot_data_sync()
            )

        log.info('--> Syncing root filesystem data')
        self.system.sync_data(
            self.__get_exclude_list_for_root_data_sync(device_map)
        )

        # create install media if requested
        if self.__install_image_requested():
            if self.install_iso or self.install_stick:
                log.info('Creating hybrid ISO installation image')
                self.install_image.create_install_iso()

            if self.install_pxe:
                log.info('Creating PXE installation archive')
                self.install_image.create_install_pxe_archive()

    def __install_image_requested(self):
        if self.install_iso or self.install_stick or self.install_pxe:
            return True
        return False

    def __get_exclude_list_for_root_data_sync(self, device_map):
        exclude_list = [
            'image', '.profile', '.kconfig', 'var/cache/kiwi'
        ]
        if 'boot' in device_map:
            exclude_list.append('boot/*')
            exclude_list.append('boot/.*')
        return exclude_list

    def __get_exclude_list_for_boot_data_sync(self):
        return ['efi/*']

    def __build_boot_filesystems(self, device_map):
        if 'efi' in device_map:
            log.info(
                'Creating EFI(fat16) filesystem on %s',
                device_map['efi'].get_device()
            )
            filesystem = FileSystem(
                'fat16', device_map['efi'], self.source_dir + '/boot/efi/'
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_efi_label()
            )
            self.system_efi = filesystem

        if 'boot' in device_map:
            boot_filesystem = self.requested_boot_filesystem
            if not boot_filesystem:
                boot_filesystem = self.requested_filesystem
            log.info(
                'Creating boot(%s) filesystem on %s',
                boot_filesystem, device_map['boot'].get_device()
            )
            filesystem = FileSystem(
                boot_filesystem, device_map['boot'], self.source_dir + '/boot/'
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_boot_label()
            )
            self.system_boot = filesystem

    def __build_and_map_disk_partitions(self):
        self.disk.wipe()
        if self.firmware.legacy_bios_mode():
            log.info('--> creating EFI CSM(legacy bios) partition')
            self.disk.create_efi_csm_partition(
                self.firmware.get_legacy_bios_partition_size()
            )

        if self.firmware.efi_mode():
            log.info('--> creating EFI partition')
            self.disk.create_efi_partition(
                self.firmware.get_efi_partition_size()
            )

        if self.disk_setup.need_boot_partition():
            log.info('--> creating boot partition')
            self.disk.create_boot_partition(
                self.disk_setup.boot_partition_size()
            )

        if self.volume_manager_name and self.volume_manager_name == 'lvm':
            log.info('--> creating LVM root partition')
            self.disk.create_root_lvm_partition('all_free')

        elif self.mdraid:
            log.info('--> creating mdraid root partition')
            self.disk.create_root_raid_partition('all_free')

        else:
            log.info('--> creating root partition')
            self.disk.create_root_partition('all_free')

        if self.firmware.bios_mode():
            log.info('--> setting active flag to primary boot partition')
            self.disk.activate_boot_partition()

        self.disk.map_partitions()
        return self.disk.get_device()

    def __write_partition_id_config_to_boot_image(self):
        log.info('Creating config.partids in boot system')
        filename = self.boot_image_task.boot_root_directory + '/config.partids'
        partition_id_map = self.disk.get_partition_id_map()
        with open(filename, 'w') as partids:
            for id_name, id_value in partition_id_map.iteritems():
                partids.write('%s="%s"\n' % (id_name, id_value))

    def __write_raid_config_to_boot_image(self):
        if self.mdraid:
            log.info('Creating etc/mdadm.conf in boot system')
            self.raid_root.create_raid_config(
                self.boot_image_task.boot_root_directory + '/etc/mdadm.conf'
            )

    def __write_crypttab_to_system_image(self):
        if self.luks:
            log.info('Creating etc/crypttab')
            self.luks_root.create_crypttab(
                self.source_dir + '/etc/crypttab'
            )

    def __write_image_identifier_to_system_image(self):
        log.info('Creating image identifier: %s', self.mbrid.get_id())
        self.mbrid.write(
            self.source_dir + '/boot/mbrid'
        )

    def __write_recovery_metadata_to_boot_image(self):
        if os.path.exists(self.source_dir + '/recovery.partition.size'):
            log.info('Copying recovery metadata to boot image')
            Command.run(
                [
                    'cp', self.source_dir + '/recovery.partition.size',
                    self.boot_image_task.boot_root_directory
                ]
            )

    def __write_bootloader_config_to_system_image(self, device_map):
        log.info('Creating %s bootloader configuration', self.bootloader)
        boot_device = device_map['root']
        if 'boot' in device_map:
            boot_device = device_map['boot']

        partition_id_map = self.disk.get_partition_id_map()
        boot_partition_id = partition_id_map['kiwi_RootPart']
        if 'kiwi_BootPart' in partition_id_map:
            boot_partition_id = partition_id_map['kiwi_BootPart']

        boot_uuid = self.disk.get_uuid(
            boot_device.get_device()
        )
        self.bootloader_config.setup_disk_boot_images(boot_uuid)
        self.bootloader_config.setup_disk_image_config(boot_uuid)
        self.bootloader_config.write()

        self.system_setup.call_edit_boot_config_script(
            self.requested_filesystem, boot_partition_id
        )

    def __install_bootloader(self, device_map):
        bootloader = BootLoaderInstall(
            self.bootloader, self.source_dir,
            self.disk.storage_provider
        )
        bootloader.install()

        boot_device = device_map['root']
        if 'boot' in device_map:
            boot_device = device_map['boot']
        self.system_setup.call_edit_boot_install_script(
            self.diskname, boot_device.get_device()
        )

    def __copy_first_boot_files_to_system_image(self):
        log.info('Copy boot files to system image')
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            log.info('--> boot image kernel as first boot linux.vmx')
            kernel.copy_kernel(
                self.source_dir, '/boot/linux.vmx'
            )
        else:
            raise KiwiDiskBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )
        if self.machine and self.machine.get_domain() == 'dom0':
            if kernel.get_xen_hypervisor():
                log.info('--> boot image Xen hypervisor as xen.gz')
                kernel.copy_xen_hypervisor(
                    self.source_dir, '/boot/xen.gz'
                )
            else:
                raise KiwiDiskBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )
        log.info('--> initrd archive as first boot initrd.vmx')
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                self.source_dir + '/boot/initrd.vmx'
            ]
        )
