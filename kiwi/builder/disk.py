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
import platform
import pickle
from collections import namedtuple
from tempfile import NamedTemporaryFile

# project
from ..defaults import Defaults
from ..bootloader.config import BootLoaderConfig
from ..bootloader.install import BootLoaderInstall
from ..system.identifier import SystemIdentifier
from ..boot.image import BootImage
from ..boot.image import BootImageKiwi
from ..storage.setup import DiskSetup
from ..storage.loop_device import LoopDevice
from ..firmware import FirmWare
from ..storage.disk import Disk
from ..storage.raid_device import RaidDevice
from ..storage.luks_device import LuksDevice
from ..filesystem import FileSystem
from ..filesystem.squashfs import FileSystemSquashFs
from ..volume_manager import VolumeManager
from ..logger import log
from ..command import Command
from ..system.setup import SystemSetup
from .install import InstallImageBuilder
from ..system.kernel import Kernel
from ..storage.subformat import DiskFormat
from ..system.result import Result
from ..utils.block import BlockID
from ..path import Path

from ..exceptions import (
    KiwiDiskBootImageError,
    KiwiInstallMediaError,
    KiwiVolumeManagerSetupError
)


class DiskBuilder(object):
    """
    Disk image builder

    Attributes

    * :attr:`arch`
        platform.machine

    * :attr:`root_dir`
        root directory path name

    * :attr:`target_dir`
        target directory path name

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`custom_root_mount_args`
        Configured custom root mount arguments

    * :attr:`build_type_name`
        Configured build type name, oem or vmx

    * :attr:`image_format`
        Configured disk image format

    * :attr:`install_iso`
        Request for install ISO image

    * :attr:`install_stick`
        Request for install Stick image, converts into a request
        for the install ISO image because it can handle both cases
        by the hybrid ISO setup

    * :attr:`install_pxe`
        Request for install PXE archive

    * :attr:`blocksize`
        Configured disk blocksize

    * :attr:`volume_manager_name`
        Configured volume manager

    * :attr:`volumes`
        Configured disk volumes

    * :attr:`volume_group_name`
        Configured volume group name

    * :attr:`mdraid`
        Request for md raid, degraded setup

    * :attr:`hybrid_mbr`
        Request to convert partition table to hybrid GPT/MBR'

    * :attr:`luks`
        LUKS encryption credentials, also triggers to
        encrypt the disk

    * :attr:`luks_os`
        Target operating system name for LUKS encryption

    * :attr:`machine`
        Configured build type machine section

    * :attr:`requested_filesystem`
        Configured root filesystem

    * :attr:`requested_boot_filesystem`
        Configured boot filesystem

    * :attr:`bootloader`
        Configured boot loader

    * :attr:`initrd_system`
        Configured initrd system

    * :attr:`disk_setup`
        Instance of DiskSetup

    * :attr:`boot_image`
        Instance of BootImage

    * :attr:`firmware`
        Instance of FirmWare

    * :attr:`system_setup`
        Instance of SystemSetup

    * :attr:`diskname`
        File name of the disk image

    * :attr:`install_media`
        Build of install media requested true|false

    * :attr:`system`
        Instance of a class with the sync_data capability
        representing the entire image system except for the boot/ area
        which could live on other parts of the disk

    * :attr:`system_boot`
        Instance of a class with the sync_data capability
        representing the boot/ area of the disk if not part of
        system

    * :attr:`system_efi`
        Instance of a class with the sync_data capability
        representing the boot/efi area of the disk

    * :attr:`generic_fstab_entries`
        List of generic/persistent fstab entries

    * :attr:`result`
        Instance of Result
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.arch = platform.machine()
        if self.arch == 'i686' or self.arch == 'i586':
            self.arch = 'ix86'
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.persistency_type = xml_state.build_type.get_devicepersistency()
        self.root_filesystem_is_overlay = xml_state.build_type.get_overlayroot()
        self.custom_root_mount_args = xml_state.get_fs_mount_option_list()
        self.build_type_name = xml_state.get_build_type_name()
        self.image_format = xml_state.build_type.get_format()
        self.install_iso = xml_state.build_type.get_installiso()
        self.install_stick = xml_state.build_type.get_installstick()
        self.install_pxe = xml_state.build_type.get_installpxe()
        self.blocksize = xml_state.build_type.get_target_blocksize()
        self.volume_manager_name = xml_state.get_volume_management()
        self.volumes = xml_state.get_volumes()
        self.volume_group_name = xml_state.get_volume_group_name()
        self.mdraid = xml_state.build_type.get_mdraid()
        self.hybrid_mbr = xml_state.build_type.get_gpt_hybrid_mbr()
        self.luks = xml_state.build_type.get_luks()
        self.luks_os = xml_state.build_type.get_luksOS()
        self.machine = xml_state.get_build_type_machine_section()
        self.requested_filesystem = xml_state.build_type.get_filesystem()
        self.requested_boot_filesystem = \
            xml_state.build_type.get_bootfilesystem()
        self.bootloader = xml_state.build_type.get_bootloader()
        self.initrd_system = xml_state.build_type.get_initrd_system()
        self.target_removable = xml_state.build_type.get_target_removable()
        self.disk_setup = DiskSetup(
            xml_state, root_dir
        )
        self.boot_image = BootImage(
            xml_state, target_dir, root_dir
        )
        self.firmware = FirmWare(
            xml_state
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.diskname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version(),
                '.raw'
            ]
        )
        self.install_media = self._install_image_requested()
        self.generic_fstab_entries = []

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

        # result store
        self.result = Result(xml_state)

    def create(self):
        """
        Build a bootable disk image and optional installation image
        The installation image is a bootable hybrid ISO image which
        embeds the disk image and an image installer

        Image types which triggers this builder are:

        * image="oem"
        * image="vmx"
        """
        disk = DiskBuilder(
            self.xml_state, self.target_dir, self.root_dir
        )
        result = disk.create_disk()

        # cleanup disk resources taken prior to next steps
        del disk

        disk_installer = DiskBuilder(
            self.xml_state, self.target_dir, self.root_dir
        )
        result = disk_installer.create_install_media(result)

        disk_format = DiskBuilder(
            self.xml_state, self.target_dir, self.root_dir
        )
        result = disk_format.create_disk_format(result)

        return result

    def create_disk(self):
        """
        Build a bootable raw disk image
        """
        if self.install_media and self.build_type_name != 'oem':
            raise KiwiInstallMediaError(
                'Install media requires oem type setup, got %s' %
                self.build_type_name
            )

        if self.root_filesystem_is_overlay and self.volume_manager_name:
            raise KiwiVolumeManagerSetupError(
                'Volume management together with root overlay is not supported'
            )

        # setup recovery archive, cleanup and create archive if requested
        self.system_setup.create_recovery_archive()

        # prepare boot(initrd) root system
        log.info('Preparing boot system')
        self.boot_image.prepare()

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

        # create the bootloader instance
        self.bootloader_config = BootLoaderConfig(
            self.bootloader, self.xml_state, self.root_dir,
            {'targetbase': loop_provider.get_device()}
        )

        # create disk partitions and instance device map
        device_map = self._build_and_map_disk_partitions()

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
        self._build_boot_filesystems(device_map)

        # create volumes and filesystems for root system
        if self.volume_manager_name:
            volume_manager_custom_parameters = {
                'fs_mount_options':
                    self.custom_root_mount_args,
                'root_label':
                    self.disk_setup.get_root_label(),
                'root_is_snapshot':
                    self.xml_state.build_type.get_btrfs_root_is_snapshot(),
                'image_type':
                    self.xml_state.get_build_type_name()
            }
            volume_manager = VolumeManager(
                self.volume_manager_name, device_map['root'],
                self.root_dir + '/',
                self.volumes,
                volume_manager_custom_parameters
            )
            volume_manager.setup(
                self.volume_group_name
            )
            volume_manager.create_volumes(
                self.requested_filesystem
            )
            volume_manager.mount_volumes()
            self.generic_fstab_entries += volume_manager.get_fstab(
                self.persistency_type, self.requested_filesystem
            )
            self.system = volume_manager
            device_map['root'] = volume_manager.get_device()['root']
        else:
            log.info(
                'Creating root(%s) filesystem on %s',
                self.requested_filesystem, device_map['root'].get_device()
            )
            filesystem_custom_parameters = {
                'mount_options': self.custom_root_mount_args
            }
            filesystem = FileSystem(
                self.requested_filesystem, device_map['root'],
                self.root_dir + '/',
                filesystem_custom_parameters
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_root_label()
            )
            self.system = filesystem

        # create a random image identifier
        self.mbrid = SystemIdentifier()
        self.mbrid.calculate_id()

        # create first stage metadata to boot image
        self._write_partition_id_config_to_boot_image()

        self._write_recovery_metadata_to_boot_image()

        self._write_raid_config_to_boot_image()

        self._write_generic_fstab_to_boot_image(device_map)

        self.system_setup.export_modprobe_setup(
            self.boot_image.boot_root_directory
        )

        # create first stage metadata to system image
        self._write_image_identifier_to_system_image()

        self._write_crypttab_to_system_image()

        self._write_generic_fstab_to_system_image(device_map)

        # create initrd cpio archive
        self.boot_image.create_initrd(self.mbrid)

        # create second stage metadata to system image
        self._copy_first_boot_files_to_system_image()

        self._write_bootloader_config_to_system_image(device_map)

        self.mbrid.write_to_disk(
            self.disk.storage_provider
        )

        # set SELinux file security contexts if context exists
        self._setup_selinux_file_contexts()

        # syncing system data to disk image
        log.info('Syncing system to image')
        if self.system_efi:
            log.info('--> Syncing EFI boot data to EFI partition')
            self.system_efi.sync_data()

        if self.system_boot:
            log.info('--> Syncing boot data at extra partition')
            self.system_boot.sync_data(
                self._get_exclude_list_for_boot_data_sync()
            )

        log.info('--> Syncing root filesystem data')
        if self.root_filesystem_is_overlay:
            squashed_root_file = NamedTemporaryFile()
            squashed_root = FileSystemSquashFs(
                device_provider=None, root_dir=self.root_dir
            )
            squashed_root.create_on_file(
                filename=squashed_root_file.name,
                exclude=self._get_exclude_list_for_root_data_sync(device_map)
            )
            Command.run(
                [
                    'dd',
                    'if=%s' % squashed_root_file.name,
                    'of=%s' % device_map['readonly'].get_device()
                ]
            )
        else:
            self.system.sync_data(
                self._get_exclude_list_for_root_data_sync(device_map)
            )

        # install boot loader
        self._install_bootloader(device_map)

        # set root filesystem properties
        self._setup_property_root_is_readonly_snapshot()

        # prepare for install media if requested
        if self.install_media:
            if self.initrd_system and self.initrd_system == 'dracut':
                # for the installation process we need a kiwi initrd
                # Therefore an extra install boot root system needs to
                # be prepared if dracut was set as the initrd system
                # to boot the system image
                log.info('Preparing extra install boot system')

                self.xml_state.build_type.set_initrd_system('kiwi')

                self.boot_image = BootImageKiwi(
                    self.xml_state, self.target_dir
                )

                self.boot_image.prepare()

                # apply disk builder metadata also needed in the install initrd
                self._write_partition_id_config_to_boot_image()
                self._write_recovery_metadata_to_boot_image()
                self._write_raid_config_to_boot_image()
                self.system_setup.export_modprobe_setup(
                    self.boot_image.boot_root_directory
                )

            log.info('Saving boot image instance to file')
            self.boot_image.dump(
                self.target_dir + '/boot_image.pickledump'
            )

        # store image file name in result
        self.result.add(
            key='disk_image',
            filename=self.diskname,
            use_for_bundle=True if not self.image_format else False,
            compress=True,
            shasum=True
        )

        # create image root metadata
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_rpm_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_rpm_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )

        return self.result

    def create_disk_format(self, result_instance):
        """
        Create a bootable disk format from a previously
        created raw disk image
        """
        if self.image_format:
            log.info('Creating %s Disk Format', self.image_format)
            disk_format = DiskFormat(
                self.image_format, self.xml_state,
                self.root_dir, self.target_dir
            )
            disk_format.create_image_format()
            disk_format.store_to_result(result_instance)

        return result_instance

    def create_install_media(self, result_instance):
        """
        Build an installation image. The installation image is a
        bootable hybrid ISO image which embeds the raw disk image
        and an image installer
        """
        if self.install_media:
            install_image = InstallImageBuilder(
                self.xml_state, self.target_dir,
                self._load_boot_image_instance()
            )

            if self.install_iso or self.install_stick:
                log.info('Creating hybrid ISO installation image')
                install_image.create_install_iso()
                result_instance.add(
                    key='installation_image',
                    filename=install_image.isoname,
                    use_for_bundle=True,
                    compress=False,
                    shasum=True
                )

            if self.install_pxe:
                log.info('Creating PXE installation archive')
                install_image.create_install_pxe_archive()
                result_instance.add(
                    key='installation_pxe_archive',
                    filename=install_image.pxename,
                    use_for_bundle=True,
                    compress=False,
                    shasum=True
                )

        return result_instance

    def _load_boot_image_instance(self):
        boot_image_dump_file = self.target_dir + '/boot_image.pickledump'
        if not os.path.exists(boot_image_dump_file):
            raise KiwiInstallMediaError(
                'No boot image instance dump %s found' % boot_image_dump_file
            )
        try:
            with open(boot_image_dump_file, 'rb') as boot_image_dump:
                boot_image = pickle.load(boot_image_dump)
            boot_image.enable_cleanup()
            Path.wipe(boot_image_dump_file)
        except Exception as e:
            raise KiwiInstallMediaError(
                'Failed to load boot image dump: %s' % type(e).__name__
            )
        return boot_image

    def _setup_selinux_file_contexts(self):
        security_context = '/etc/selinux/targeted/contexts/files/file_contexts'
        if os.path.exists(self.root_dir + security_context):
            self.system_setup.set_selinux_file_contexts(
                security_context
            )

    def _install_image_requested(self):
        if self.install_iso or self.install_stick or self.install_pxe:
            return True

    def _get_exclude_list_for_root_data_sync(self, device_map):
        exclude_list = [
            'image', '.profile', '.kconfig',
            Defaults.get_shared_cache_location()
        ]
        if 'boot' in device_map and self.bootloader == 'grub2_s390x_emu':
            exclude_list.append('boot/zipl/*')
            exclude_list.append('boot/zipl/.*')
        elif 'boot' in device_map:
            exclude_list.append('boot/*')
            exclude_list.append('boot/.*')
        if 'efi' in device_map:
            exclude_list.append('boot/efi/*')
            exclude_list.append('boot/efi/.*')
        return exclude_list

    def _get_exclude_list_for_boot_data_sync(self):
        return ['efi/*']

    def _build_boot_filesystems(self, device_map):
        if 'efi' in device_map:
            log.info(
                'Creating EFI(fat16) filesystem on %s',
                device_map['efi'].get_device()
            )
            filesystem = FileSystem(
                'fat16', device_map['efi'], self.root_dir + '/boot/efi/'
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_efi_label()
            )
            self.system_efi = filesystem

        if 'boot' in device_map:
            boot_filesystem = self.requested_boot_filesystem
            if not boot_filesystem:
                boot_filesystem = self.requested_filesystem
            boot_directory = self.root_dir + '/boot/'
            if self.bootloader == 'grub2_s390x_emu':
                boot_directory = self.root_dir + '/boot/zipl/'
                boot_filesystem = 'ext2'
            log.info(
                'Creating boot(%s) filesystem on %s',
                boot_filesystem, device_map['boot'].get_device()
            )
            filesystem = FileSystem(
                boot_filesystem, device_map['boot'], boot_directory
            )
            filesystem.create_on_device(
                label=self.disk_setup.get_boot_label()
            )
            self.system_boot = filesystem

    def _build_and_map_disk_partitions(self):
        self.disk.wipe()
        if self.firmware.vboot_mode():
            log.info('--> creating Virtual boot partition')
            self.disk.create_vboot_partition(
                self.firmware.get_vboot_partition_size()
            )

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

        if self.firmware.ofw_mode():
            log.info('--> creating PReP partition')
            self.disk.create_prep_partition(
                self.firmware.get_prep_partition_size()
            )

        if self.disk_setup.need_boot_partition():
            log.info('--> creating boot partition')
            self.disk.create_boot_partition(
                self.disk_setup.boot_partition_size()
            )

        if self.root_filesystem_is_overlay:
            log.info('--> creating readonly root partition')
            squashed_root_file = NamedTemporaryFile()
            squashed_root = FileSystemSquashFs(
                device_provider=None, root_dir=self.root_dir
            )
            squashed_root.create_on_file(
                filename=squashed_root_file.name,
                exclude=[Defaults.get_shared_cache_location()]
            )
            squashed_rootfs_mbsize = os.path.getsize(
                squashed_root_file.name
            ) / 1048576
            self.disk.create_root_readonly_partition(
                int(squashed_rootfs_mbsize + 50)
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

        if self.firmware.ofw_mode():
            log.info('--> setting active flag to primary PReP partition')
            self.disk.activate_boot_partition()

        if self.hybrid_mbr:
            log.info('--> converting partition table to hybrid GPT/MBR')
            self.disk.create_hybrid_mbr()

        self.disk.map_partitions()

        return self.disk.get_device()

    def _write_partition_id_config_to_boot_image(self):
        log.info('Creating config.partids in boot system')
        filename = self.boot_image.boot_root_directory + '/config.partids'
        partition_id_map = self.disk.get_public_partition_id_map()
        with open(filename, 'w') as partids:
            for id_name, id_value in list(partition_id_map.items()):
                partids.write('%s="%s"\n' % (id_name, id_value))

    def _write_raid_config_to_boot_image(self):
        if self.mdraid:
            log.info('Creating etc/mdadm.conf in boot system')
            self.raid_root.create_raid_config(
                self.boot_image.boot_root_directory + '/etc/mdadm.conf'
            )

    def _write_crypttab_to_system_image(self):
        if self.luks:
            log.info('Creating etc/crypttab')
            self.luks_root.create_crypttab(
                self.root_dir + '/etc/crypttab'
            )

    def _write_generic_fstab_to_system_image(self, device_map):
        log.info('Creating generic system etc/fstab')
        self._write_generic_fstab(device_map, self.system_setup)

    def _write_generic_fstab_to_boot_image(self, device_map):
        if not self.initrd_system or self.initrd_system == 'kiwi':
            log.info('Creating generic boot image etc/fstab')
            self._write_generic_fstab(device_map, self.boot_image.setup)

    def _write_generic_fstab(self, device_map, setup):
        root_is_snapshot = \
            self.xml_state.build_type.get_btrfs_root_is_snapshot()
        root_is_readonly_snapshot = \
            self.xml_state.build_type.get_btrfs_root_is_readonly_snapshot()

        fs_check_interval = '1 1'
        custom_root_mount_args = list(self.custom_root_mount_args)
        if root_is_snapshot and root_is_readonly_snapshot:
            custom_root_mount_args += ['ro']
            fs_check_interval = '0 0'

        self._add_generic_fstab_entry(
            device_map['root'].get_device(), '/',
            custom_root_mount_args, fs_check_interval
        )
        if 'boot' in device_map:
            if self.bootloader == 'grub2_s390x_emu':
                boot_mount_point = '/boot/zipl'
            else:
                boot_mount_point = '/boot'
            self._add_generic_fstab_entry(
                device_map['boot'].get_device(), boot_mount_point
            )
        if 'efi' in device_map:
            self._add_generic_fstab_entry(
                device_map['efi'].get_device(), '/boot/efi'
            )
        setup.create_fstab(
            self.generic_fstab_entries
        )

    def _add_generic_fstab_entry(
        self, device, mount_point, options=None, check='0 0'
    ):
        if not options:
            options = ['defaults']
        block_operation = BlockID(device)
        blkid_type = 'LABEL' if self.persistency_type == 'by-label' else 'UUID'
        device_id = block_operation.get_blkid(blkid_type)
        fstab_entry = ' '.join(
            [
                blkid_type + '=' + device_id, mount_point,
                block_operation.get_filesystem(), ','.join(options), check
            ]
        )
        if fstab_entry not in self.generic_fstab_entries:
            self.generic_fstab_entries.append(
                fstab_entry
            )

    def _write_image_identifier_to_system_image(self):
        log.info('Creating image identifier: %s', self.mbrid.get_id())
        self.mbrid.write(
            self.root_dir + '/boot/mbrid'
        )

    def _write_recovery_metadata_to_boot_image(self):
        if os.path.exists(self.root_dir + '/recovery.partition.size'):
            log.info('Copying recovery metadata to boot image')
            Command.run(
                [
                    'cp', self.root_dir + '/recovery.partition.size',
                    self.boot_image.boot_root_directory
                ]
            )

    def _write_bootloader_config_to_system_image(self, device_map):
        log.info('Creating %s bootloader configuration', self.bootloader)
        boot_names = self._get_boot_names()
        boot_device = device_map['root']
        if 'boot' in device_map:
            boot_device = device_map['boot']

        partition_id_map = self.disk.get_public_partition_id_map()
        boot_partition_id = partition_id_map['kiwi_RootPart']
        if 'kiwi_BootPart' in partition_id_map:
            boot_partition_id = partition_id_map['kiwi_BootPart']

        boot_uuid = self.disk.get_uuid(
            boot_device.get_device()
        )
        self.bootloader_config.setup_disk_boot_images(boot_uuid)
        self.bootloader_config.setup_disk_image_config(
            uuid=boot_uuid,
            kernel=boot_names.kernel_name,
            initrd=boot_names.initrd_name
        )
        self.bootloader_config.write()

        self.system_setup.call_edit_boot_config_script(
            self.requested_filesystem, boot_partition_id
        )

    def _install_bootloader(self, device_map):
        root_device = device_map['root']
        boot_device = root_device
        if 'boot' in device_map:
            boot_device = device_map['boot']

        if 'readonly' in device_map:
            root_device = device_map['readonly']

        custom_install_arguments = {
            'boot_device': boot_device.get_device(),
            'root_device': root_device.get_device(),
            'firmware': self.firmware,
            'target_removable': self.target_removable
        }

        if 'efi' in device_map:
            efi_device = device_map['efi']
            custom_install_arguments.update(
                {'efi_device': efi_device.get_device()}
            )

        if 'prep' in device_map:
            prep_device = device_map['prep']
            custom_install_arguments.update(
                {'prep_device': prep_device.get_device()}
            )

        if self.volume_manager_name:
            self.system.umount_volumes()
            custom_install_arguments.update(
                {'system_volumes': self.system.get_volumes()}
            )

        log.debug(
            "custom arguments for bootloader installation %s",
            custom_install_arguments
        )
        bootloader = BootLoaderInstall(
            self.bootloader, self.root_dir, self.disk.storage_provider,
            custom_install_arguments
        )
        if bootloader.install_required():
            bootloader.install()

        self.system_setup.call_edit_boot_install_script(
            self.diskname, boot_device.get_device()
        )

    def _setup_property_root_is_readonly_snapshot(self):
        if self.volume_manager_name:
            root_is_snapshot = \
                self.xml_state.build_type.get_btrfs_root_is_snapshot()
            root_is_readonly_snapshot = \
                self.xml_state.build_type.get_btrfs_root_is_readonly_snapshot()
            if root_is_snapshot and root_is_readonly_snapshot:
                log.info(
                    'Setting root filesystem into read-only mode'
                )
                self.system.mount_volumes()
                self.system.set_property_readonly_root()
                self.system.umount_volumes()

    def _copy_first_boot_files_to_system_image(self):
        boot_names = self._get_boot_names()
        if not self.initrd_system or self.initrd_system == 'kiwi':
            log.info('Copy boot files to system image')
            kernel = Kernel(self.boot_image.boot_root_directory)

            log.info('--> boot image kernel as %s', boot_names.kernel_name)
            kernel.copy_kernel(
                self.root_dir, ''.join(['/boot/', boot_names.kernel_name])
            )

            if self.machine and self.machine.get_domain() == 'dom0':
                if kernel.get_xen_hypervisor():
                    log.info('--> boot image Xen hypervisor as xen.gz')
                    kernel.copy_xen_hypervisor(
                        self.root_dir, '/boot/xen.gz'
                    )
                else:
                    raise KiwiDiskBootImageError(
                        'No hypervisor in boot image tree %s found' %
                        self.boot_image.boot_root_directory
                    )

        log.info('--> initrd archive as %s', boot_names.initrd_name)
        Command.run(
            [
                'mv', self.boot_image.initrd_filename,
                self.root_dir + ''.join(['/boot/', boot_names.initrd_name])
            ]
        )

    def _get_boot_names(self):
        boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
        kernel = Kernel(
            self.boot_image.boot_root_directory
        )
        kernel_info = kernel.get_kernel()
        if not kernel_info:
            raise KiwiDiskBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image.boot_root_directory
            )
        if self.initrd_system and self.initrd_system == 'dracut':
            kernel_name_prefix = 'vmlinuz-'
            if self.arch == 'aarch64' or self.arch.startswith('arm'):
                kernel_name_prefix = 'zImage-'
            return boot_names_type(
                kernel_name=kernel_name_prefix + kernel_info.version,
                initrd_name='initrd-' + kernel_info.version
            )
        else:
            return boot_names_type(
                kernel_name='linux.vmx',
                initrd_name='initrd.vmx'
            )
