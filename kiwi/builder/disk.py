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
from contextlib import ExitStack
import os
import sys
import logging
from typing import (
    Dict, List, Optional, Tuple, Union
)
if sys.version_info >= (3, 8):
    from typing import TypedDict  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import TypedDict  # pragma: no cover

# project
import kiwi.defaults as defaults

from kiwi.utils.veritysetup import VeritySetup
from kiwi.utils.temporary import Temporary
from kiwi.system.mount import ImageSystem
from kiwi.storage.disk import ptable_entry_type
from kiwi.defaults import Defaults
from kiwi.filesystem.base import FileSystemBase
from kiwi.bootloader.config import create_boot_loader_config
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.bootloader.install import BootLoaderInstall
from kiwi.system.identifier import SystemIdentifier
from kiwi.boot.image import BootImage
from kiwi.storage.setup import DiskSetup
from kiwi.storage.loop_device import LoopDevice
from kiwi.storage.clone_device import CloneDevice
from kiwi.firmware import FirmWare
from kiwi.storage.disk import Disk
from kiwi.storage.raid_device import RaidDevice
from kiwi.storage.luks_device import LuksDevice
from kiwi.storage.integrity_device import (
    IntegrityDevice,
    integrity_credentials_type
)
from kiwi.storage.device_provider import DeviceProvider
from kiwi.filesystem import FileSystem
from kiwi.filesystem.squashfs import FileSystemSquashFs
from kiwi.volume_manager import VolumeManager
from kiwi.volume_manager.base import VolumeManagerBase
from kiwi.command import Command
from kiwi.system.setup import SystemSetup
from kiwi.builder.install import InstallImageBuilder
from kiwi.system.kernel import Kernel
from kiwi.storage.subformat import DiskFormat
from kiwi.system.result import Result
from kiwi.utils.block import BlockID
from kiwi.utils.fstab import Fstab
from kiwi.runtime_config import RuntimeConfig
from kiwi.partitioner import Partitioner
from kiwi.xml_state import XMLState

from kiwi.exceptions import (
    KiwiDiskBootImageError,
    KiwiInstallMediaError,
    KiwiVolumeManagerSetupError
)

log = logging.getLogger('kiwi')


class StorageMap(TypedDict):
    system: \
        Optional[Union[FileSystemBase, VolumeManagerBase]]
    system_boot: \
        Optional[FileSystemBase]
    system_efi: \
        Optional[FileSystemBase]
    system_spare: \
        Optional[FileSystemBase]
    system_custom_parts: \
        Dict[str, FileSystemBase]
    luks_root: \
        Optional[LuksDevice]
    raid_root: \
        Optional[RaidDevice]
    integrity_root: \
        Optional[IntegrityDevice]


class DiskBuilder:
    """
    **Disk image builder**

    :param object xml_state: Instance of :class:`XMLState`
    :param str target_dir: Target directory path name
    :param str root_dir: Root directory path name
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * signing_keys: list of package signing keys
        * xz_options: string of XZ compression parameters
    """
    def __init__(
        self, xml_state: XMLState, target_dir: str,
        root_dir: str, custom_args: Dict = None
    ):
        self.arch = Defaults.get_platform_name()
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.spare_part_mbsize = xml_state.get_build_type_spare_part_size()
        self.spare_part_fs = xml_state.build_type.get_spare_part_fs()
        self.spare_part_is_last = xml_state.build_type.get_spare_part_is_last()
        self.spare_part_mountpoint = \
            xml_state.build_type.get_spare_part_mountpoint()
        self.persistency_type = xml_state.build_type.get_devicepersistency()
        self.root_filesystem_is_overlay = xml_state.build_type.get_overlayroot()
        self.root_filesystem_has_write_partition = \
            xml_state.build_type.get_overlayroot_write_partition()
        self.root_filesystem_read_only_partsize = \
            xml_state.build_type.get_overlayroot_readonly_partsize()
        self.root_filesystem_verity_blocks = \
            xml_state.build_type.get_verity_blocks()
        self.root_filesystem_embed_verity_metadata = \
            xml_state.build_type.get_embed_verity_metadata()
        self.dosparttable_extended_layout = \
            xml_state.build_type.get_dosparttable_extended_layout()
        self.boot_clone_count = int(xml_state.build_type.get_boot_clone()) \
            if xml_state.build_type.get_boot_clone() else 0
        self.root_clone_count = int(xml_state.build_type.get_root_clone()) \
            if xml_state.build_type.get_root_clone() else 0
        self.custom_root_mount_args = xml_state.get_fs_mount_option_list()
        self.custom_root_creation_args = xml_state.get_fs_create_option_list()
        self.build_type_name = xml_state.get_build_type_name()
        self.image_format = xml_state.build_type.get_format()
        self.install_iso = xml_state.build_type.get_installiso()
        self.install_stick = xml_state.build_type.get_installstick()
        self.install_pxe = xml_state.build_type.get_installpxe()
        self.blocksize = xml_state.build_type.get_target_blocksize()
        self.volume_manager_name = xml_state.get_volume_management()
        self.volumes = xml_state.get_volumes()
        self.custom_partitions = xml_state.get_partitions()
        self.volume_group_name = xml_state.get_volume_group_name()
        self.mdraid = xml_state.build_type.get_mdraid()
        self.hybrid_mbr = xml_state.build_type.get_gpt_hybrid_mbr()
        self.force_mbr = xml_state.build_type.get_force_mbr()
        self.luks = xml_state.get_luks_credentials()
        self.use_disk_password = \
            xml_state.get_build_type_bootloader_use_disk_password()
        self.integrity = xml_state.build_type.get_standalone_integrity()
        self.integrity_legacy_hmac = \
            xml_state.build_type.get_integrity_legacy_hmac()
        self.integrity_keyfile = xml_state.build_type.get_integrity_keyfile()
        self.integrity_key_description = \
            xml_state.build_type.get_integrity_metadata_key_description()
        self.root_filesystem_embed_integrity_metadata = \
            xml_state.build_type.get_embed_integrity_metadata()
        self.luks_format_options = xml_state.get_luks_format_options()
        self.luks_randomize = xml_state.build_type.get_luks_randomize() \
            if xml_state.build_type.get_luks_randomize() is not None else True
        self.luks_os = xml_state.build_type.get_luksOS()
        self.xen_server = xml_state.is_xen_server()
        self.requested_filesystem = xml_state.build_type.get_filesystem()
        self.requested_boot_filesystem = \
            xml_state.build_type.get_bootfilesystem()
        self.bootloader = xml_state.get_build_type_bootloader_name()
        self.initrd_system = xml_state.get_initrd_system()
        self.target_removable = xml_state.build_type.get_target_removable()
        self.root_filesystem_is_multipath = \
            xml_state.get_oemconfig_oem_multipath_scan()
        self.btrfs_default_volume_requested = \
            xml_state.btrfs_default_volume_requested()
        self.oem_systemsize = xml_state.get_oemconfig_oem_systemsize()
        self.oem_resize = xml_state.get_oemconfig_oem_resize()
        self.disk_resize_requested = \
            xml_state.get_oemconfig_oem_resize()
        self.swap_mbytes = xml_state.get_oemconfig_swap_mbytes()
        self.disk_start_sector = xml_state.get_disk_start_sector()
        self.disk_setup = DiskSetup(
            xml_state, root_dir
        )
        self.unpartitioned_bytes = \
            xml_state.get_build_type_unpartitioned_bytes()
        self.custom_args = custom_args

        self.signing_keys = None
        if custom_args and 'signing_keys' in custom_args:
            self.signing_keys = custom_args['signing_keys']

        self.boot_image = BootImage.new(
            xml_state, target_dir, root_dir, signing_keys=self.signing_keys
        )
        self.firmware = FirmWare(
            xml_state
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.bundle_format = xml_state.get_build_type_bundle_format()
        self.diskname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version(),
                '.raw'
            ]
        )
        self.boot_is_crypto = True if self.luks and not \
            self.disk_setup.need_boot_partition() else False
        self.install_media = self._install_image_requested()
        self.fstab = Fstab()

        self.volume_manager_custom_parameters = {
            'fs_mount_options':
                self.custom_root_mount_args,
            'fs_create_options':
                self.custom_root_creation_args,
            'root_label':
                self.disk_setup.get_root_label(),
            'root_is_snapshot':
                self.xml_state.build_type.get_btrfs_root_is_snapshot(),
            'root_is_readonly_snapshot':
                self.xml_state.build_type.get_btrfs_root_is_readonly_snapshot(),
            'root_is_subvolume':
                self.xml_state.build_type.get_btrfs_root_is_subvolume(),
            'btrfs_default_volume_requested':
                self.btrfs_default_volume_requested,
            'quota_groups':
                self.xml_state.build_type.get_btrfs_quota_groups(),
            'resize_on_boot':
                self.disk_resize_requested
        }

        self.filesystem_custom_parameters = {
            'mount_options':
                self.custom_root_mount_args,
            'create_options':
                self.custom_root_creation_args
        }

        self.need_root_filesystem = False
        if not self.root_filesystem_is_overlay or \
           self.root_filesystem_has_write_partition is not False:
            self.need_root_filesystem = True

        # result store
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

        if not self.boot_image.has_initrd_support():
            log.warning('Building without initrd support !')

    def create(self) -> Result:
        """
        Build a bootable disk image and optional installation image
        The installation image is a bootable hybrid ISO image which
        embeds the disk image and an image installer

        Image types which triggers this builder are:

        * image="oem"

        :return: result

        :rtype: instance of :class:`Result`
        """
        result = self.create_disk()
        result = self.create_install_media(result)
        self.append_unpartitioned_space()
        return self.create_disk_format(result)

    def create_disk(self) -> Result:
        """
        Build a bootable raw disk image

        :raises KiwiInstallMediaError:
            if install media is required and image type is not oem
        :raises KiwiVolumeManagerSetupError:
            root overlay at the same time volumes are defined is not supported

        :return: result

        :rtype: instance of :class:`Result`
        """
        # initialize device dict
        self.storage_map: StorageMap = {
            'system': None,
            'system_boot': None,
            'system_efi': None,
            'system_spare': None,
            'system_custom_parts': {},
            'luks_root': None,
            'raid_root': None,
            'integrity_root': None
        }

        if self.install_media and self.build_type_name != 'oem':
            raise KiwiInstallMediaError(
                'Install media requires oem type setup, got {0}'.format(
                    self.build_type_name
                )
            )

        if self.root_filesystem_is_overlay and self.volume_manager_name:
            raise KiwiVolumeManagerSetupError(
                'Volume management together with root overlay is not supported'
            )

        # setup recovery archive, cleanup and create archive if requested
        self.system_setup.create_recovery_archive()

        # prepare initrd
        if self.boot_image.has_initrd_support():
            log.info('Preparing boot system')
            self.boot_image.prepare()

        # precalculate needed disk size
        disksize_mbytes = self.disk_setup.get_disksize_mbytes(
            root_clone=self.root_clone_count, boot_clone=self.boot_clone_count
        )

        # create the disk
        log.info('Creating raw disk image %s', self.diskname)
        with LoopDevice(
            self.diskname, disksize_mbytes, self.blocksize
        ) as loop_provider:
            loop_provider.create()

            # create the disk partitioner, still unmapped
            with self._disk_instance(loop_provider) as disk:
                # create disk partitions and instance device map
                device_map = self._build_and_map_disk_partitions(
                    disk, disksize_mbytes
                )

                # update device and disk id map if no root write partition
                if self.root_filesystem_is_overlay and \
                   self.root_filesystem_has_write_partition is False:
                    device_map['root'] = device_map['readonly']
                    disk.public_partition_id_map['kiwi_RootPart'] = \
                        disk.public_partition_id_map['kiwi_ROPart']

                with ExitStack() as stack:
                    if self.mdraid:
                        # create raid on current root device
                        raid_root = self._raid_instance(device_map)
                        stack.push(raid_root)
                        device_map = self._map_raid(
                            device_map, disk, raid_root
                        )

                    if self.integrity:
                        # create integrity on current root device
                        integrity_root = self._integrity_instance(device_map)
                        stack.push(integrity_root)
                        device_map = self._map_integrity(
                            device_map, integrity_root
                        )

                    if self.luks is not None:
                        # create luks on current root device
                        luks_root = self._luks_instance(device_map)
                        stack.push(luks_root)
                        device_map = self._map_luks(
                            device_map, luks_root
                        )

                    # create system layout for root system
                    device_map = self._create_system_instance(
                        device_map, stack
                    )
                    # build bootable disk
                    self._build_main_system(
                        stack,
                        device_map,
                        disk,
                        self.storage_map['system'],
                        self.storage_map['system_boot'],
                        self.storage_map['system_efi'],
                        self.storage_map['system_spare'],
                        self.storage_map['system_custom_parts'] or {},
                        self.storage_map['luks_root'],
                        self.storage_map['raid_root'],
                        self.storage_map['integrity_root']
                    )

        # store image bundle_format in result
        if self.bundle_format:
            self.result.add_bundle_format(self.bundle_format)

        # store image file name in result
        compression = self.runtime_config.get_bundle_compression(default=True)
        if self.luks is not None and self.luks_randomize:
            compression = False
        self.result.add(
            key='disk_image',
            filename=self.diskname,
            use_for_bundle=True if not self.image_format else False,
            compress=compression,
            shasum=True
        )

        # create image root metadata
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_changes',
            filename=self.system_setup.export_package_changes(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=True,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result

    def create_disk_format(self, result_instance: Result) -> Result:
        """
        Create a bootable disk format from a previously
        created raw disk image

        :param object result_instance: instance of :class:`Result`

        :return: updated result_instance

        :rtype: instance of :class:`Result`
        """
        if self.image_format:
            log.info('Creating %s Disk Format', self.image_format)
            with DiskFormat.new(
                self.image_format, self.xml_state,
                self.root_dir, self.target_dir
            ) as disk_format:
                disk_format.create_image_format()
                disk_format.store_to_result(result_instance)

        return result_instance

    def append_unpartitioned_space(self) -> None:
        """
        Extends the raw disk if an unpartitioned area is specified
        """
        if self.unpartitioned_bytes:
            log.info(
                'Expanding disk with %d bytes of unpartitioned space',
                self.unpartitioned_bytes
            )
            with DiskFormat.new(
                'raw', self.xml_state, self.root_dir, self.target_dir
            ) as disk_format:
                disk_format.resize_raw_disk(
                    self.unpartitioned_bytes, append=True
                )
                firmware = FirmWare(self.xml_state)
                with LoopDevice(disk_format.diskname) as loop_provider:
                    loop_provider.create(overwrite=False)
                    partitioner = Partitioner.new(
                        firmware.get_partition_table_type(), loop_provider
                    )
                    partitioner.resize_table()

    def create_install_media(self, result_instance: Result) -> Result:
        """
        Build an installation image. The installation image is a
        bootable hybrid ISO image which embeds the raw disk image
        and an image installer

        :param object result_instance: instance of :class:`Result`

        :return: updated result_instance with installation media

        :rtype: instance of :class:`Result`
        """
        if self.install_media:
            boot_image = None
            if self.initrd_system == 'kiwi':
                boot_image = self.boot_image
            install_image = InstallImageBuilder(
                self.xml_state, self.root_dir, self.target_dir,
                boot_image, self.custom_args
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
                    filename=install_image.pxetarball,
                    use_for_bundle=True,
                    compress=False,
                    shasum=True
                )

        return result_instance

    def _disk_instance(self, loop_provider: LoopDevice) -> Disk:
        return Disk(
            self.firmware.get_partition_table_type(),
            loop_provider,
            self.disk_start_sector,
            extended_layout=bool(self.dosparttable_extended_layout)
        )

    def _bootloader_instance(self, disk: Disk) -> BootLoaderConfigBase:
        custom_args = {
            'targetbase':
                disk.storage_provider.get_device(),
            'crypto_disk':
                True if self.luks is not None else False,
            'boot_is_crypto':
                self.boot_is_crypto,
            'config_options':
                self.xml_state.get_bootloader_config_options()
        }
        if self.bootloader.startswith('grub'):
            custom_args.update(
                Defaults.get_grub_custom_arguments(self.root_dir)
            )
        return create_boot_loader_config(
            name=self.bootloader,
            xml_state=self.xml_state,
            root_dir=self.root_dir,
            boot_dir=self.root_dir,
            custom_args=custom_args
        )

    def _raid_instance(self, device_map: Dict) -> RaidDevice:
        return RaidDevice(device_map['root'])

    def _luks_instance(self, device_map: Dict) -> LuksDevice:
        return LuksDevice(device_map['root'])

    def _integrity_instance(self, device_map: Dict) -> IntegrityDevice:
        return IntegrityDevice(
            device_map['root'],
            defaults.INTEGRITY_ALGORITHM,
            integrity_credentials_type(
                keydescription=self.integrity_key_description,
                keyfile=self.integrity_keyfile,
                keyfile_algorithm=defaults.INTEGRITY_KEY_ALGORITHM,
                options=[
                    'legacy_hmac'
                ] if self.integrity_legacy_hmac else []
            )
        )

    def _create_system_instance(
        self, device_map: Dict, stack: ExitStack
    ) -> Dict:
        # create spare filesystem on spare partition if present
        self.storage_map[
            'system_spare'
        ] = self._build_spare_filesystem(device_map)

        # create custom partitions and filesystems
        self.storage_map[
            'system_custom_parts'
        ] = self._build_custom_parts_filesystem(
            device_map, self.custom_partitions
        )

        # create filesystems on boot partition(s) if any
        self.storage_map['system_boot'], self.storage_map['system_efi'] = \
            self._build_boot_filesystems(device_map)

        if self.volume_manager_name:
            volume_manager = VolumeManager.new(
                self.volume_manager_name, device_map,
                self.root_dir + '/',
                self.volumes,
                self.volume_manager_custom_parameters
            )
            stack.push(volume_manager)
            device_map = self._map_root_volume_manager(
                device_map, volume_manager
            )
        elif self.need_root_filesystem:
            filesystem = FileSystem.new(
                self.requested_filesystem, device_map['root'],
                self.root_dir + '/',
                self.filesystem_custom_parameters
            )
            stack.push(filesystem)
            self._map_root_filesystem(device_map, filesystem)

        return device_map

    def _map_raid(
        self, device_map: Dict, disk: Disk, raid_root: RaidDevice
    ) -> Dict:
        # build the raid device
        raid_root.create_degraded_raid(raid_level=self.mdraid)
        device_map['root'] = raid_root.get_device()
        disk.public_partition_id_map['kiwi_RaidPart'] = \
            disk.public_partition_id_map['kiwi_RootPart']
        disk.public_partition_id_map['kiwi_RaidDev'] = \
            device_map['root'].get_device()
        self.storage_map['raid_root'] = raid_root
        return device_map

    def _map_integrity(
        self, device_map: Dict, integrity_root: IntegrityDevice
    ) -> Dict:
        # build the integrity device
        integrity_root.create_dm_integrity()
        device_map['integrity_root'] = device_map['root']
        device_map['root'] = integrity_root.get_device()
        if self.root_filesystem_is_overlay and \
           self.root_filesystem_has_write_partition is False:
            device_map['readonly'] = device_map['root']
        self.storage_map['integrity_root'] = integrity_root
        return device_map

    def _map_luks(
        self, device_map: Dict, luks_root: LuksDevice
    ) -> Dict:
        # build the luks
        self.luks_boot_keyname = '/root/.root.keyfile'
        self.luks_boot_keyfile = ''.join(
            [self.root_dir, self.luks_boot_keyname]
        )
        # use LUKS key file for the following conditions:
        # 1. /boot is encrypted
        #    In this case grub needs to read from LUKS via the
        #    cryptodisk module which at the moment always asks
        #    for the passphrase even when empty. The keyfile
        #    setup makes sure only one interaction on the grub
        #    stage is needed
        # 2. LUKS passphrase is configured as empty string
        #    In this case the keyfile allows to open the
        #    LUKS pool without asking
        #
        luks_need_keyfile = \
            True if self.boot_is_crypto or self.luks == '' else False
        luks_root.create_crypto_luks(
            passphrase=self.luks or '',
            osname=self.luks_os,
            options=self.luks_format_options,
            keyfile=self.luks_boot_keyname if luks_need_keyfile else '',
            randomize=self.luks_randomize,
            root_dir=self.root_dir
        )
        if luks_need_keyfile:
            self.luks_boot_keyfile_setup = ''.join(
                [self.root_dir, '/etc/dracut.conf.d/99-luks-boot.conf']
            )
            self.boot_image.write_system_config_file(
                config={'install_items': [self.luks_boot_keyname]},
                config_file=self.luks_boot_keyfile_setup
            )
            self.boot_image.include_file(
                '/root/' + os.path.basename(self.luks_boot_keyfile)
            )
        device_map['luks_root'] = device_map['root']
        device_map['root'] = luks_root.get_device()
        if self.root_filesystem_is_overlay and \
           self.root_filesystem_has_write_partition is False:
            device_map['readonly'] = device_map['root']
        self.storage_map['luks_root'] = luks_root
        return device_map

    def _map_root_volume_manager(
        self, device_map: Dict, volume_manager: VolumeManagerBase
    ) -> Dict:
        # build system root volumes and filesystems
        volume_manager.setup(
            self.volume_group_name
        )
        volume_manager.create_volumes(
            self.requested_filesystem
        )
        volume_manager.mount_volumes()
        device_map['root'] = volume_manager.get_device().get('root')
        device_map['swap'] = volume_manager.get_device().get('swap')
        self.storage_map['system'] = volume_manager
        return device_map

    def _map_root_filesystem(
        self, device_map: Dict, filesystem: FileSystemBase
    ) -> None:
        # build system root filesystem
        log.info(
            'Creating root({0}) filesystem on {1}'.format(
                self.requested_filesystem,
                device_map['root'].get_device()
            )
        )
        if self.root_filesystem_embed_integrity_metadata:
            filesystem.create_on_device(
                label=self.disk_setup.get_root_label(),
                size=-defaults.DM_METADATA_OFFSET,
                unit=defaults.UNIT.byte
            )
        else:
            filesystem.create_on_device(
                label=self.disk_setup.get_root_label(),
            )
        self.storage_map['system'] = filesystem

    def _build_main_system(
        self,
        stack: ExitStack,
        device_map: Dict,
        disk: Disk,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]],
        system_boot: Optional[FileSystemBase],
        system_efi: Optional[FileSystemBase],
        system_spare: Optional[FileSystemBase],
        system_custom_parts: Dict[str, FileSystemBase],
        luks_root: Optional[LuksDevice] = None,
        raid_root: Optional[RaidDevice] = None,
        integrity_root: Optional[IntegrityDevice] = None,
    ) -> None:
        # create swap on current root device if requested
        if self.swap_mbytes:
            with FileSystem.new(
                'swap', device_map['swap']
            ) as swap:
                swap.create_on_device(
                    label='SWAP'
                )

        # store root partition/filesystem uuid for profile
        self._preserve_root_partition_uuid(device_map)
        self._preserve_root_filesystem_uuid(device_map)

        # create a random image identifier
        self.mbrid = SystemIdentifier()
        self.mbrid.calculate_id()

        # create first stage metadata to boot image
        self._write_partition_id_config_to_boot_image(disk)

        self._write_recovery_metadata_to_boot_image()

        self._write_raid_config_to_boot_image(raid_root)

        self._write_generic_fstab_to_boot_image(device_map, system)

        self.system_setup.export_modprobe_setup(
            self.boot_image.boot_root_directory
        )

        # create first stage metadata to system image
        self._write_image_identifier_to_system_image()

        self._write_crypttab_to_system_image(luks_root)

        self._write_integritytab_to_system_image(integrity_root)

        self._write_generic_fstab_to_system_image(device_map, system)

        if self.initrd_system == 'dracut':
            if self.root_filesystem_is_multipath is False:
                self.boot_image.omit_module('multipath')
            if self.root_filesystem_is_overlay:
                self.boot_image.include_module('kiwi-overlay')
                self.boot_image.write_system_config_file(
                    config={'modules': ['kiwi-overlay']}
                )
            if self.disk_resize_requested:
                self.boot_image.include_module('kiwi-repart')

        # create initrd
        if self.boot_image.has_initrd_support():
            self.boot_image.create_initrd(self.mbrid)

        # create second stage metadata to system image
        self._copy_first_boot_files_to_system_image()

        with self._bootloader_instance(disk) as bootloader_config:
            # write bootloader meta data to system image
            if self.bootloader != 'custom':
                self._write_bootloader_meta_data_to_system_image(
                    device_map, disk, system, bootloader_config
                )

            # call edit_boot_config script
            partition_id_map = disk.get_public_partition_id_map()
            boot_partition_id = partition_id_map['kiwi_RootPart']
            if 'kiwi_BootPart' in partition_id_map:
                boot_partition_id = partition_id_map['kiwi_BootPart']
            self.system_setup.call_edit_boot_config_script(
                self.requested_filesystem, int(boot_partition_id)
            )

            # write MBR id
            self.mbrid.write_to_disk(
                disk.storage_provider
            )

            # run pre sync script hook
            if self.system_setup.script_exists(
                defaults.PRE_DISK_SYNC_SCRIPT
            ):
                disk_system = SystemSetup(
                    self.xml_state, self.root_dir
                )
                disk_system.call_pre_disk_script()

            # syncing system data to disk image
            self._sync_system_to_image(
                stack,
                device_map,
                system,
                system_boot,
                system_efi,
                system_spare,
                system_custom_parts,
                integrity_root
            )

            # run post sync script hook
            if system and self.system_setup.script_exists(
                defaults.POST_DISK_SYNC_SCRIPT
            ):
                with ImageSystem(
                    device_map, self.root_dir,
                    system.get_volumes() if self.volume_manager_name else {},
                    self.custom_partitions if self.custom_partitions else {}
                ) as image_system:
                    image_system.mount()
                    disk_system = SystemSetup(
                        self.xml_state, image_system.mountpoint()
                    )
                    disk_system.call_disk_script()

            # install boot loader
            if self.bootloader != 'custom':
                self._install_bootloader(
                    device_map, disk, system, bootloader_config
                )

            # call edit_boot_install script
            boot_device = device_map['root']
            if 'boot' in device_map:
                boot_device = device_map['boot']
            self.system_setup.call_edit_boot_install_script(
                self.diskname, boot_device.get_device()
            )

            # set root filesystem properties
            if system:
                self._setup_property_root_is_readonly_snapshot(system)

    def _install_image_requested(self) -> bool:
        return bool(
            self.install_iso or self.install_stick or self.install_pxe
        )

    def _get_exclude_list_for_root_data_sync(self, device_map: Dict) -> list:
        exclude_list = Defaults.\
            get_exclude_list_for_root_data_sync() + Defaults.\
            get_exclude_list_from_custom_exclude_files(self.root_dir)
        if 'spare' in device_map and self.spare_part_mountpoint:
            exclude_list.append(
                '{0}/*'.format(self.spare_part_mountpoint.lstrip(os.sep))
            )
            exclude_list.append(
                '{0}/.*'.format(self.spare_part_mountpoint.lstrip(os.sep))
            )
        if 'boot' in device_map \
           and 's390' in self.arch and self.bootloader == 'grub2_s390x_emu':
            exclude_list.append('boot/zipl/*')
            exclude_list.append('boot/zipl/.*')
        elif 'boot' in device_map:
            exclude_list.append('boot/*')
            exclude_list.append('boot/.*')
        if 'efi' in device_map:
            exclude_list.append('boot/efi/*')
            exclude_list.append('boot/efi/.*')
        if self.custom_partitions:
            for map_name in sorted(self.custom_partitions.keys()):
                if map_name in device_map and \
                   self.custom_partitions[map_name].mountpoint:
                    mountpoint = os.path.normpath(
                        self.custom_partitions[map_name].mountpoint
                    ).lstrip(os.sep)
                    exclude_list.append(f'{mountpoint}/*')
                    exclude_list.append(f'{mountpoint}/.*')
        return exclude_list

    @staticmethod
    def _get_exclude_list_for_boot_data_sync() -> list:
        return ['efi/*']

    def _build_custom_parts_filesystem(
        self, device_map: Dict,
        custom_partitions: Dict['str', ptable_entry_type]
    ) -> Dict[str, FileSystemBase]:
        filesystem_dict = {}
        partitions = custom_partitions or {}
        for map_name in sorted(partitions.keys()):
            if map_name in device_map:
                ptable_entry = partitions[map_name]
                if ptable_entry.filesystem:
                    with FileSystem.new(
                        ptable_entry.filesystem,
                        device_map[map_name],
                        f'{self.root_dir}{ptable_entry.mountpoint}/'
                    ) as filesystem:
                        if ptable_entry.filesystem == 'squashfs':
                            squashed_root_file = Temporary().new_file()
                            filesystem.create_on_file(
                                filename=squashed_root_file.name,
                                exclude=[Defaults.get_shared_cache_location()]
                            )
                            readonly_target = device_map[map_name].get_device()
                            readonly_target_bytesize = device_map[
                                map_name
                            ].get_byte_size(readonly_target)
                            log.info(
                                '--> {} {!r} file({} {}) -> {}({} {})'.format(
                                    'Dumping',
                                    map_name,
                                    os.path.getsize(squashed_root_file.name),
                                    'bytes',
                                    readonly_target,
                                    readonly_target_bytesize,
                                    'bytes'
                                )
                            )
                            Command.run(
                                [
                                    'dd',
                                    f'if={squashed_root_file.name}',
                                    f'of={readonly_target}'
                                ]
                            )
                        else:
                            filesystem.create_on_device(
                                label=map_name.upper()
                            )
                        filesystem_dict[map_name] = filesystem
        return filesystem_dict

    def _build_spare_filesystem(
        self, device_map: Dict
    ) -> Optional[FileSystemBase]:
        if 'spare' in device_map and self.spare_part_fs:
            spare_part_data_path = None
            spare_part_custom_parameters = {
                'fs_attributes':
                    self.xml_state.get_build_type_spare_part_fs_attributes()
            }
            if self.spare_part_mountpoint:
                spare_part_data_path = self.root_dir + '{0}/'.format(
                    self.spare_part_mountpoint
                )
            with FileSystem.new(
                self.spare_part_fs,
                device_map['spare'],
                spare_part_data_path,
                spare_part_custom_parameters
            ) as filesystem:
                filesystem.create_on_device(
                    label='SPARE'
                )
                return filesystem
        return None

    def _build_boot_filesystems(
        self, device_map: Dict
    ) -> Tuple[Optional[FileSystemBase], Optional[FileSystemBase]]:
        system_boot = None
        system_efi = None
        if 'efi' in device_map:
            log.info(
                'Creating EFI(fat16) filesystem on %s',
                device_map['efi'].get_device()
            )
            with FileSystem.new(
                'fat16', device_map['efi'], self.root_dir + '/boot/efi/'
            ) as filesystem:
                filesystem.create_on_device(
                    label=self.disk_setup.get_efi_label()
                )
                system_efi = filesystem

        if 'boot' in device_map:
            boot_filesystem = self.requested_boot_filesystem
            if not boot_filesystem:
                boot_filesystem = self.requested_filesystem
            boot_directory = self.root_dir + '/boot/'
            if 's390' in self.arch and self.bootloader == 'grub2_s390x_emu':
                boot_directory = self.root_dir + '/boot/zipl/'
            log.info(
                'Creating boot(%s) filesystem on %s',
                boot_filesystem, device_map['boot'].get_device()
            )
            with FileSystem.new(
                boot_filesystem, device_map['boot'], boot_directory
            ) as filesystem:
                filesystem.create_on_device(
                    label=self.disk_setup.get_boot_label()
                )
                system_boot = filesystem
        return system_boot, system_efi

    def _build_and_map_disk_partitions(
        self, disk: Disk, disksize_mbytes: float
    ) -> Dict:
        disk.wipe()
        disksize_used_mbytes = 0
        if self.firmware.legacy_bios_mode():
            log.info('--> creating EFI CSM(legacy bios) partition')
            partition_mbsize = self.firmware.get_legacy_bios_partition_size()
            disk.create_efi_csm_partition(
                partition_mbsize
            )
            disksize_used_mbytes += partition_mbsize

        if self.firmware.efi_mode():
            log.info('--> creating EFI partition')
            partition_mbsize = self.firmware.get_efi_partition_size()
            disk.create_efi_partition(
                partition_mbsize
            )
            disksize_used_mbytes += partition_mbsize

        if self.firmware.ofw_mode():
            log.info('--> creating PReP partition')
            partition_mbsize = self.firmware.get_prep_partition_size()
            disk.create_prep_partition(
                partition_mbsize
            )
            disksize_used_mbytes += partition_mbsize

        if self.disk_setup.need_boot_partition():
            log.info(
                '--> creating boot partition [with {0} clone(s)]'.format(
                    self.boot_clone_count
                )
            )
            partition_mbsize = self.disk_setup.boot_partition_size()
            disk.create_boot_partition(
                partition_mbsize, self.boot_clone_count
            )
            disksize_used_mbytes += \
                (self.boot_clone_count + 1) * partition_mbsize if \
                self.boot_clone_count else partition_mbsize

        if self.swap_mbytes:
            if not self.volume_manager_name \
               or self.volume_manager_name != 'lvm':
                log.info('--> creating SWAP partition')
                disk.create_swap_partition(
                    f'{self.swap_mbytes}'
                )
                disksize_used_mbytes += self.swap_mbytes

        if self.custom_partitions:
            log.info(
                '--> creating custom partition(s): {0}'.format(
                    sorted(self.custom_partitions.keys())
                )
            )
            disk.create_custom_partitions(self.custom_partitions)

        if self.spare_part_mbsize and not self.spare_part_is_last:
            log.info('--> creating spare partition')
            disk.create_spare_partition(
                f'{self.spare_part_mbsize}'
            )

        if self.root_filesystem_is_overlay:
            log.info('--> creating readonly root partition')
            squashed_rootfs_mbsize = self.root_filesystem_read_only_partsize
            if not self.root_filesystem_read_only_partsize:
                squashed_root_file = Temporary().new_file()
                with FileSystemSquashFs(
                    device_provider=DeviceProvider(), root_dir=self.root_dir,
                    custom_args={
                        'compression':
                            self.xml_state.build_type.get_squashfscompression()
                    }
                ) as squashed_root:
                    squashed_root.create_on_file(
                        filename=squashed_root_file.name,
                        exclude=[Defaults.get_shared_cache_location()]
                    )
                squashed_rootfs_mbsize = int(
                    os.path.getsize(squashed_root_file.name) / 1048576
                ) + Defaults.get_min_partition_mbytes()
            disk.create_root_readonly_partition(
                squashed_rootfs_mbsize, self.root_clone_count
            )
            disksize_used_mbytes += \
                (self.root_clone_count + 1) * squashed_rootfs_mbsize if \
                self.root_clone_count else squashed_rootfs_mbsize

        if self.spare_part_mbsize and self.spare_part_is_last:
            rootfs_mbsize = disksize_mbytes - disksize_used_mbytes - \
                self.spare_part_mbsize - Defaults.get_min_partition_mbytes()
        else:
            if self.oem_systemsize and not self.oem_resize:
                rootfs_mbsize = self.oem_systemsize
            else:
                rootfs_mbsize = 'all_free'
            log.info(
                '--> Using {0}MB for the root(rw) partition if present'.format(
                    rootfs_mbsize
                )
            )

        if self.root_filesystem_is_overlay and \
           self.root_filesystem_has_write_partition is False:
            log.warning(
                '--> overlayroot explicitly requested no write partition'
            )
        else:
            root_clone_count = self.root_clone_count
            if self.root_filesystem_is_overlay:
                # in overlay mode an eventual root clone is created from
                # the root readonly partition and not from the root (rw)
                # partition. Thus no further action needed here in this
                # case
                root_clone_count = 0
            if root_clone_count:
                if rootfs_mbsize == 'all_free':
                    clone_rootfs_mbsize = int(
                        (disksize_mbytes - disksize_used_mbytes) / (root_clone_count + 1)
                    ) + Defaults.get_min_partition_mbytes()
                    rootfs_mbsize = f'clone:all_free:{clone_rootfs_mbsize}'
                else:
                    rootfs_mbsize = f'clone:{rootfs_mbsize}:{rootfs_mbsize}'
            if self.volume_manager_name and self.volume_manager_name == 'lvm':
                log.info(
                    '--> creating {0} partition [with {1} clone(s)]'.format(
                        'root(LVM)', root_clone_count
                    )
                )
                disk.create_root_lvm_partition(rootfs_mbsize, root_clone_count)
            elif self.mdraid:
                log.info(
                    '--> creating {0} partition [with {1} clone(s)]'.format(
                        f'root(mdraid={self.mdraid})', root_clone_count
                    )
                )
                disk.create_root_raid_partition(rootfs_mbsize, root_clone_count)
            else:
                log.info(
                    '--> creating root partition [with {0} clone(s)]'.format(
                        root_clone_count
                    )
                )
                disk.create_root_partition(rootfs_mbsize, root_clone_count)

        if self.spare_part_mbsize and self.spare_part_is_last:
            log.info('--> creating spare partition')
            disk.create_spare_partition(
                'all_free'
            )

        if self.firmware.bios_mode():
            log.info('--> setting active flag to primary boot partition')
            disk.activate_boot_partition()

        if self.firmware.ofw_mode():
            log.info('--> setting active flag to primary PReP partition')
            disk.activate_boot_partition()

        if self.firmware.get_partition_table_type() == 'msdos' \
           and self.disk_start_sector:
            log.info(f'--> setting start sector to: {self.disk_start_sector}')
            disk.set_start_sector(self.disk_start_sector)

        if self.firmware.efi_mode():
            if self.force_mbr:
                log.info('--> converting partition table to MBR')
                disk.create_mbr()
            elif self.hybrid_mbr:
                log.info('--> converting partition table to hybrid GPT/MBR')
                disk.create_hybrid_mbr()

        disk.map_partitions()

        device_map = disk.get_device()
        device_map['origin_root'] = \
            device_map.get('readonly') or device_map['root']

        return device_map

    def _write_partition_id_config_to_boot_image(self, disk: Disk) -> None:
        log.info('Creating config.partids in boot system')
        filename = ''.join(
            [self.boot_image.boot_root_directory, '/config.partids']
        )
        partition_id_map = disk.get_public_partition_id_map()
        with open(filename, 'w') as partids:
            for id_name, id_value in list(partition_id_map.items()):
                partids.write('{0}="{1}"{2}'.format(
                    id_name, id_value, os.linesep)
                )
        self.boot_image.include_file(
            os.sep + os.path.basename(filename)
        )

    def _write_raid_config_to_boot_image(
        self, raid_root: Optional[RaidDevice]
    ) -> None:
        if raid_root is not None:
            log.info('Creating etc/mdadm.conf in boot system')
            filename = ''.join(
                [self.boot_image.boot_root_directory, '/etc/mdadm.conf']
            )
            raid_root.create_raid_config(filename)
            self.boot_image.include_file(
                os.sep + os.sep.join(['etc', os.path.basename(filename)])
            )

    def _write_integritytab_to_system_image(
        self, integrity_root: Optional[IntegrityDevice]
    ) -> None:
        if integrity_root:
            log.info('Creating etc/integritytab')
            filename = ''.join(
                [self.root_dir, '/etc/integritytab']
            )
            integrity_root.create_integritytab(filename)
            self.boot_image.include_file(
                os.sep + os.sep.join(['etc', os.path.basename(filename)])
            )

    def _write_crypttab_to_system_image(
        self, luks_root: Optional[LuksDevice]
    ) -> None:
        if luks_root is not None:
            log.info('Creating etc/crypttab')
            filename = ''.join(
                [self.root_dir, '/etc/crypttab']
            )
            luks_root.create_crypttab(filename)
            self.boot_image.include_file(
                os.sep + os.sep.join(['etc', os.path.basename(filename)])
            )

    def _write_generic_fstab_to_system_image(
        self, device_map: Dict,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]]
    ) -> None:
        log.info('Creating generic system etc/fstab')
        self._write_generic_fstab(device_map, self.system_setup, system)

    def _write_generic_fstab_to_boot_image(
        self, device_map: Dict,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]]
    ) -> None:
        if self.initrd_system == 'kiwi':
            log.info('Creating generic boot image etc/fstab')
            self._write_generic_fstab(
                device_map, self.boot_image.setup, system
            )

    def _write_generic_fstab(
        self, device_map: Dict, setup: SystemSetup,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]]
    ) -> None:
        root_is_snapshot = \
            self.xml_state.build_type.get_btrfs_root_is_snapshot()
        root_is_readonly_snapshot = \
            self.xml_state.build_type.get_btrfs_root_is_readonly_snapshot()

        fs_check_interval = '0 1'
        custom_root_mount_args = list(self.custom_root_mount_args)
        if root_is_snapshot and root_is_readonly_snapshot:
            custom_root_mount_args += ['ro']
            fs_check_interval = '0 0'

        if system and self.volume_manager_name \
           and self.volume_manager_name == 'btrfs' \
           and not self.btrfs_default_volume_requested:
            root_volume_name = system.get_root_volume_name()
            if root_volume_name != '/':
                custom_root_mount_args += [
                    f'defaults,subvol={root_volume_name}'
                ]

        self._add_fstab_entry(
            device_map['root'].get_device(), '/',
            custom_root_mount_args, fs_check_interval
        )
        if device_map.get('boot'):
            if 's390' in self.arch and self.bootloader == 'grub2_s390x_emu':
                boot_mount_point = '/boot/zipl'
            else:
                boot_mount_point = '/boot'
            self._add_fstab_entry(
                device_map['boot'].get_device(), boot_mount_point
            )
        if device_map.get('efi'):
            self._add_fstab_entry(
                device_map['efi'].get_device(), '/boot/efi'
            )
        if system and self.volume_manager_name:
            volume_fstab_entries = system.get_fstab(
                self.persistency_type, self.requested_filesystem
            )
            for volume_fstab_entry in volume_fstab_entries:
                self.fstab.add_entry(volume_fstab_entry)
        if device_map.get('spare') and \
           self.spare_part_fs and self.spare_part_mountpoint:
            self._add_fstab_entry(
                device_map['spare'].get_device(), self.spare_part_mountpoint
            )
        if device_map.get('swap'):
            self._add_fstab_entry(
                device_map['swap'].get_device(), 'swap'
            )
        if self.custom_partitions:
            for map_name in sorted(self.custom_partitions.keys()):
                if device_map.get(map_name) and \
                   self.custom_partitions[map_name].mountpoint:
                    self._add_fstab_entry(
                        device_map[map_name].get_device(),
                        self.custom_partitions[map_name].mountpoint
                    )
        setup.create_fstab(
            self.fstab
        )

    def _add_fstab_entry(
        self, device: str, mount_point: str,
        options: List = None, check: str = '0 0'
    ) -> None:
        if not options:
            options = ['defaults']
        block_operation = BlockID(device)
        filesystem = block_operation.get_filesystem()
        if self.volume_manager_name and self.volume_manager_name == 'lvm' \
           and (mount_point == '/' or mount_point == 'swap'):
            fstab_entry = ' '.join(
                [
                    device, mount_point,
                    filesystem, ','.join(options), check
                ]
            )
        else:
            if filesystem == 'squashfs':
                # squashfs does not provide a label or uuid
                blkid_type = 'PARTUUID'
            elif self.persistency_type == 'by-label':
                blkid_type = 'LABEL'
            elif self.persistency_type == 'by-partuuid':
                blkid_type = 'PARTUUID'
            else:
                blkid_type = 'UUID'
            device_id = block_operation.get_blkid(blkid_type)
            fstab_entry = ' '.join(
                [
                    blkid_type + '=' + device_id, mount_point,
                    filesystem, ','.join(options), check
                ]
            )
        self.fstab.add_entry(fstab_entry)

    def _preserve_root_partition_uuid(self, device_map: Dict) -> None:
        block_operation = BlockID(
            device_map['root'].get_device()
        )
        partition_uuid = block_operation.get_blkid('PARTUUID')
        if partition_uuid:
            self.xml_state.set_root_partition_uuid(
                partition_uuid
            )

    def _preserve_root_filesystem_uuid(self, device_map: Dict) -> None:
        block_operation = BlockID(
            device_map['root'].get_device()
        )
        rootfs_uuid = block_operation.get_blkid('UUID')
        if rootfs_uuid:
            self.xml_state.set_root_filesystem_uuid(
                rootfs_uuid
            )

    def _write_image_identifier_to_system_image(self) -> None:
        log.info('Creating image identifier: %s', self.mbrid.get_id())
        self.mbrid.write(
            self.root_dir + '/boot/mbrid'
        )

    def _write_recovery_metadata_to_boot_image(self) -> None:
        if os.path.exists(self.root_dir + '/recovery.partition.size'):
            log.info('Copying recovery metadata to boot image')
            recovery_metadata = ''.join(
                [self.root_dir, '/recovery.partition.size']
            )
            Command.run(
                ['cp', recovery_metadata, self.boot_image.boot_root_directory]
            )
            self.boot_image.include_file(
                os.sep + os.path.basename(recovery_metadata)
            )

    def _write_bootloader_meta_data_to_system_image(
        self, device_map: Dict, disk: Disk,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]],
        bootloader_config: BootLoaderConfigBase
    ) -> None:
        log.info('Creating %s bootloader configuration', self.bootloader)
        boot_options = []
        if self.mdraid:
            boot_options.append('rd.auto')
        if system and self.volume_manager_name \
           and self.volume_manager_name == 'btrfs' \
           and not self.btrfs_default_volume_requested \
           and system.get_root_volume_name() != '/':
            boot_options.append(
                f'rootflags=subvol={system.get_root_volume_name()}'
            )
        ro_device = device_map.get('readonly')
        root_device = device_map['root']
        boot_device = root_device
        if 'boot' in device_map:
            boot_device = device_map['boot']

        boot_uuid = disk.get_uuid(
            boot_device.get_device()
        )
        boot_uuid_unmapped = disk.get_uuid(
            device_map['luks_root'].get_device()
        ) if self.luks and self.boot_is_crypto else boot_uuid
        bootloader_config.setup_disk_boot_images(
            boot_uuid_unmapped
        )
        bootloader_config.write_meta_data(
            root_device=ro_device.
            get_device() if ro_device else root_device.get_device(),
            write_device=root_device.get_device(),
            boot_options=' '.join(boot_options)
        )

        log.info('Creating config.bootoptions')
        filename = ''.join(
            [self.boot_image.boot_root_directory, '/config.bootoptions']
        )
        kexec_boot_options = ' '.join(
            [
                bootloader_config.get_boot_cmdline(
                    ro_device.
                    get_device() if ro_device else root_device.get_device(),
                    device_map['root'].get_device()
                )
            ] + boot_options
        )
        with open(filename, 'w') as boot_optionsfp:
            boot_optionsfp.write(
                '{0}{1}'.format(kexec_boot_options, os.linesep)
            )

    def _sync_system_to_image(
        self,
        stack: ExitStack,
        device_map: Dict,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]],
        system_boot: Optional[FileSystemBase],
        system_efi: Optional[FileSystemBase],
        system_spare: Optional[FileSystemBase],
        system_custom_parts: Dict[str, FileSystemBase],
        integrity_root: Optional[IntegrityDevice]
    ) -> None:
        log.info('Syncing system to image')
        if system_spare:
            log.info('--> Syncing spare partition data')
            stack.push(system_spare.sync_data())

        for map_name in sorted(system_custom_parts.keys()):
            system_custom_part = system_custom_parts[map_name]
            log.info('--> Syncing custom partition(s) data')
            if not system_custom_part.filename:
                stack.push(system_custom_part.sync_data())
            if device_map.get(f'{map_name}clone1'):
                log.info(
                    f'--> Dumping {map_name!r} clone data at extra partition'
                )
                system_custom_part.umount()
                system_custom_part_clone = CloneDevice(
                    system_custom_part.device_provider, self.root_dir
                )
                system_custom_part_clone.clone(
                    self._get_clone_devices(f'{map_name}clone', device_map)
                )
                system_custom_part.mount()

        if system_efi:
            log.info('--> Syncing EFI boot data to EFI partition')
            stack.push(system_efi.sync_data())

        if system_boot:
            log.info('--> Syncing boot data at extra partition')
            stack.push(system_boot.sync_data(
                self._get_exclude_list_for_boot_data_sync()
            ))
            if device_map.get('bootclone1'):
                log.info(
                    '--> Dumping boot clone data at extra partition'
                )
                system_boot.umount()
                CloneDevice(system_boot.device_provider, self.root_dir).clone(
                    self._get_clone_devices('bootclone', device_map)
                )
                system_boot.mount()

        log.info('--> Syncing root filesystem data')
        if self.root_filesystem_is_overlay:
            squashed_root_file = Temporary().new_file()
            with FileSystemSquashFs(
                device_provider=DeviceProvider(), root_dir=self.root_dir,
                custom_args={
                    'compression':
                        self.xml_state.build_type.get_squashfscompression()
                }
            ) as squashed_root:
                exclude_list = self._get_exclude_list_for_root_data_sync(
                    device_map
                )
                # To allow running custom scripts in a read-only root
                # it's required to keep the /image mountpoint directory
                # such that it can be bind mounted from the unpacked
                # root tree
                exclude_list.remove('image')
                exclude_list.append('image/*')
                squashed_root.create_on_file(
                    filename=squashed_root_file.name,
                    exclude=exclude_list
                )

                if self.root_filesystem_verity_blocks:
                    squashed_root.create_verity_layer(
                        self.root_filesystem_verity_blocks if
                        self.root_filesystem_verity_blocks != 'all' else None
                    )

                readonly_target = device_map['readonly'].get_device()
                readonly_target_bytesize = device_map['readonly'].get_byte_size(
                    readonly_target
                )
                log.info(
                    '--> Dumping rootfs file({0} {1}) -> {2}({3} {1})'.format(
                        os.path.getsize(squashed_root_file.name), 'bytes',
                        readonly_target, readonly_target_bytesize
                    )
                )
                Command.run(
                    [
                        'dd',
                        'if=%s' % squashed_root_file.name,
                        'of=%s' % readonly_target
                    ]
                )
                if self.root_filesystem_embed_verity_metadata:
                    squashed_root.create_verification_metadata(
                        readonly_target
                    )
            if device_map.get('rootclone1'):
                log.info(
                    '--> Dumping readonly root clone data at extra partition'
                )
                CloneDevice(device_map['origin_root'], self.root_dir).clone(
                    self._get_clone_devices('rootclone', device_map)
                )
        elif self.root_filesystem_verity_blocks:
            root_target = device_map['root'].get_device()
            root_target_bytesize = device_map['root'].get_byte_size(
                root_target
            )
            verity_root_file_bytes = root_target_bytesize - VeritySetup(
                device_map['root'].get_device(),
                self.root_filesystem_verity_blocks if
                self.root_filesystem_verity_blocks != 'all' else None
            ).get_hash_byte_size()
            if self.root_filesystem_embed_verity_metadata:
                verity_root_file_bytes -= defaults.DM_METADATA_OFFSET
            verity_root_file = Temporary().new_file()
            with LoopDevice(
                verity_root_file.name, int(verity_root_file_bytes / 1048576)
            ) as loop_provider:
                loop_provider.create()
                filesystem_custom_parameters = {
                    'mount_options': self.custom_root_mount_args,
                    'create_options': self.custom_root_creation_args
                }
                with FileSystem.new(
                    self.requested_filesystem, loop_provider,
                    self.root_dir + '/',
                    filesystem_custom_parameters
                ) as filesystem:
                    filesystem.create_on_device(
                        label=self.disk_setup.get_root_label(),
                        uuid=BlockID(root_target).get_uuid()
                    )
                    filesystem.sync_data(
                        self._get_exclude_list_for_root_data_sync(device_map)
                    )
                filesystem.create_verity_layer(
                    self.root_filesystem_verity_blocks if
                    self.root_filesystem_verity_blocks != 'all' else None,
                    verity_root_file.name
                )

            log.info(
                '--> Dumping rootfs file({0} bytes) -> {1}({2} bytes)'.format(
                    os.path.getsize(verity_root_file.name),
                    root_target, root_target_bytesize
                )
            )
            Command.run(
                [
                    'dd',
                    'if=%s' % verity_root_file.name,
                    'of=%s' % root_target
                ]
            )
            if self.root_filesystem_embed_verity_metadata:
                filesystem.create_verification_metadata(
                    root_target
                )
            if device_map.get('rootclone1'):
                log.info(
                    '--> Dumping root clone data at extra partition'
                )
                CloneDevice(device_map['origin_root'], self.root_dir).clone(
                    self._get_clone_devices('rootclone', device_map)
                )
        elif system:
            system_mount = system.sync_data(
                self._get_exclude_list_for_root_data_sync(device_map)
            )
            if system_mount:
                stack.push(system_mount)
            if device_map.get('rootclone1'):
                log.info(
                    '--> Dumping root clone data at extra partition'
                )
                if self.volume_manager_name:
                    system.umount_volumes()
                else:
                    system.umount()
                CloneDevice(device_map['origin_root'], self.root_dir).clone(
                    self._get_clone_devices('rootclone', device_map)
                )
                if self.volume_manager_name:
                    system.mount_volumes()
                else:
                    system.mount()

        if integrity_root and \
           self.root_filesystem_embed_integrity_metadata:
            log.info('--> Creating integrity metadata...')
            integrity_root.create_integrity_metadata()
            log.info('--> Signing integrity metadata...')
            integrity_root.sign_integrity_metadata()
            integrity_root.write_integrity_metadata()

    def _install_bootloader(
        self, device_map: Dict, disk,
        system: Optional[Union[FileSystemBase, VolumeManagerBase]],
        bootloader_config: BootLoaderConfigBase
    ) -> None:
        root_device = device_map['root']
        boot_device = root_device
        readonly_device = None
        if 'boot' in device_map:
            boot_device = device_map['boot']

        if 'readonly' in device_map:
            readonly_device = device_map['readonly']

        custom_install_arguments = {
            'boot_device': boot_device.get_device(),
            'root_device':
                readonly_device.
                get_device() if readonly_device else root_device.get_device(),
            'write_device': root_device.get_device(),
            'firmware': self.firmware,
            'target_removable': self.target_removable,
            'install_options': self.xml_state.get_bootloader_install_options(),
            'shim_options': self.xml_state.get_bootloader_shim_options()
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

        if system and self.volume_manager_name:
            custom_install_arguments.update(
                {
                    'system_volumes': system.get_volumes(),
                    'system_root_volume':
                        system.get_root_volume_name()
                        if self.volume_manager_name == 'btrfs' else None
                }
            )

        # create bootloader config prior bootloader installation
        try:
            bootloader_config.setup_disk_image_config(
                boot_options=custom_install_arguments
            )
            if 's390' in self.arch:
                bootloader_config.write()
        finally:
            # cleanup bootloader config resources taken prior to next steps
            del bootloader_config

        if self.root_filesystem_has_write_partition is not False:
            log.debug(
                "custom arguments for bootloader installation %s",
                custom_install_arguments
            )
            bootloader = BootLoaderInstall.new(
                self.bootloader, self.xml_state, self.root_dir,
                disk.storage_provider, custom_install_arguments
            )
            if bootloader.install_required():
                bootloader.install()
            bootloader.secure_boot_install()

            if self.use_disk_password and self.luks:
                bootloader.set_disk_password(self.luks)
        else:
            log.warning(
                'No install of bootcode on read-only root possible'
            )

    def _setup_property_root_is_readonly_snapshot(
        self, system: Union[FileSystemBase, VolumeManagerBase]
    ) -> None:
        if self.volume_manager_name:
            root_is_snapshot = \
                self.xml_state.build_type.get_btrfs_root_is_snapshot()
            root_is_readonly_snapshot = \
                self.xml_state.build_type.get_btrfs_root_is_readonly_snapshot()
            if root_is_snapshot and root_is_readonly_snapshot:
                log.info(
                    'Setting root filesystem into read-only mode'
                )
                system.set_property_readonly_root()

    def _copy_first_boot_files_to_system_image(self) -> None:
        boot_names = self.boot_image.get_boot_names()
        if self.initrd_system == 'kiwi':
            log.info('Copy boot files to system image')
            kernel = Kernel(self.boot_image.boot_root_directory)

            log.info('--> boot image kernel as %s', boot_names.kernel_name)
            kernel.copy_kernel(
                self.root_dir, ''.join(['/boot/', boot_names.kernel_name])
            )

            if self.xen_server:
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

        if self.boot_image.initrd_filename:
            log.info('--> initrd archive as %s', boot_names.initrd_name)
            Command.run(
                [
                    'mv', self.boot_image.initrd_filename,
                    self.root_dir + ''.join(['/boot/', boot_names.initrd_name])
                ]
            )

    def _get_clone_devices(
        self, match: str, device_map: Dict[str, DeviceProvider]
    ) -> List[DeviceProvider]:
        result = []
        for map_name in sorted(device_map.keys()):
            if map_name.startswith(match):
                result.append(device_map[map_name])
        return result
