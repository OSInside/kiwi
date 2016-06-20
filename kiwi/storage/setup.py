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
from collections import namedtuple

# project
from ..firmware import FirmWare
from ..system.size import SystemSize
from ..defaults import Defaults
from ..logger import log


class DiskSetup(object):
    """
    Implement disk setup methods providing information required
    before building a disk image

    Attributes

    * :attr:`configured_size`
        Configured size setup

    * :attr:`build_type_name`
        Configured build type name

    * :attr:`filesystem`
        Configured filesystem name

    * :attr:`bootpart_requested`
        Configured request for a boot partition

    * :attr:`bootpart_mbytes`
        Configured boot partition size

    * :attr:`mdraid`
        Configured raid setup

    * :attr:`luks`
        Configured LUKS credentials

    * :attr:`volume_manager`
        Configured volume manager name

    * :attr:`bootloader`
        Configured bootloader

    * :attr:`oemconfig`
        Configured oemconfig section

    * :attr:`volumes`
        Configured volumes

    * :attr:`firmware`
        Instance of FirmWare

    * :attr:`rootsize`
        Instance of SystemSize

    * :attr:`root_dir`
        root directory path name

    * :attr:`xml_state`
        Instance of XMLState
    """
    def __init__(self, xml_state, root_dir):
        self.root_filesystem_is_overlay = xml_state.build_type.get_overlayroot()
        self.configured_size = xml_state.get_build_type_size()
        self.build_type_name = xml_state.get_build_type_name()
        self.filesystem = xml_state.build_type.get_filesystem()
        self.bootpart_requested = xml_state.build_type.get_bootpartition()
        self.bootpart_mbytes = xml_state.build_type.get_bootpartsize()
        self.mdraid = xml_state.build_type.get_mdraid()
        self.luks = xml_state.build_type.get_luks()
        self.volume_manager = xml_state.get_volume_management()
        self.bootloader = xml_state.build_type.get_bootloader()
        self.oemconfig = xml_state.get_build_type_oemconfig_section()
        self.volumes = xml_state.get_volumes()

        self.firmware = FirmWare(
            xml_state
        )
        self.rootsize = SystemSize(
            root_dir
        )

        self.root_dir = root_dir
        self.xml_state = xml_state

    def get_disksize_mbytes(self):
        """
        Precalculate disk size requirements in mbytes

        :return: disk size mbytes
        :rtype: int
        """
        log.info('Precalculating required disk size')
        calculated_disk_mbytes = 0
        root_filesystem_mbytes = self.rootsize.customize(
            self.rootsize.accumulate_mbyte_file_sizes(), self.filesystem
        )
        calculated_disk_mbytes += root_filesystem_mbytes
        log.info(
            '--> system data with filesystem overhead needs %s MB',
            root_filesystem_mbytes
        )
        if self.volume_manager and self.volume_manager == 'lvm':
            if self.build_type_name == 'vmx':
                # only for vmx types we need to add the configured volume
                # sizes. oem disks are self expandable and will resize to
                # the configured sizes on first boot of the disk image
                volume_mbytes = self._accumulate_volume_size(
                    root_filesystem_mbytes
                )
                if volume_mbytes:
                    calculated_disk_mbytes += volume_mbytes
                    log.info(
                        '--> volume(s) size setup adding %s MB', volume_mbytes
                    )

        vboot_mbytes = self.firmware.get_vboot_partition_size()
        if vboot_mbytes:
            calculated_disk_mbytes += vboot_mbytes
            log.info(
                '--> virtual boot partition adding %s MB',
                vboot_mbytes
            )

        legacy_bios_mbytes = self.firmware.get_legacy_bios_partition_size()
        if legacy_bios_mbytes:
            calculated_disk_mbytes += legacy_bios_mbytes
            log.info(
                '--> legacy bios boot partition adding %s MB',
                legacy_bios_mbytes
            )

        boot_mbytes = self.boot_partition_size()
        if boot_mbytes:
            calculated_disk_mbytes += boot_mbytes
            log.info(
                '--> boot partition adding %s MB', boot_mbytes
            )

        efi_mbytes = self.firmware.get_efi_partition_size()
        if efi_mbytes:
            calculated_disk_mbytes += efi_mbytes
            log.info(
                '--> EFI partition adding %s MB', efi_mbytes
            )

        prep_mbytes = self.firmware.get_prep_partition_size()
        if prep_mbytes:
            calculated_disk_mbytes += prep_mbytes
            log.info(
                '--> PReP partition adding %s MB', prep_mbytes
            )

        recovery_mbytes = self._inplace_recovery_partition_size()
        if recovery_mbytes:
            calculated_disk_mbytes += recovery_mbytes
            log.info(
                '--> In-place recovery partition adding: %s MB',
                recovery_mbytes
            )

        if not self.configured_size:
            log.info(
                'Using calculated disk size: %d MB',
                calculated_disk_mbytes
            )
            return calculated_disk_mbytes
        elif self.configured_size.additive:
            result_disk_mbytes = \
                self.configured_size.mbytes + calculated_disk_mbytes
            log.info(
                'Using configured disk size: %d MB + %d MB calculated = %d MB',
                self.configured_size.mbytes,
                calculated_disk_mbytes,
                result_disk_mbytes
            )
            return result_disk_mbytes
        else:
            log.info(
                'Using configured disk size: %d MB',
                self.configured_size.mbytes
            )
            if self.configured_size.mbytes < calculated_disk_mbytes:
                log.warning(
                    '--> Configured size smaller than calculated size: %d MB',
                    calculated_disk_mbytes
                )
            return self.configured_size.mbytes

    def need_boot_partition(self):
        """
        Decide if an extra boot partition is needed. This is done with
        the bootpartition attribute from the type, however if it is not
        set it depends on some other type configuration parameters if
        we need a boot partition or not

        :rtype: bool
        """
        if self.bootpart_requested is True:
            return True
        if self.bootpart_requested is False:
            return False
        if self.mdraid:
            return True
        if self.volume_manager:
            return True
        if self.filesystem == 'btrfs':
            return True
        if self.filesystem == 'xfs':
            return True
        if self.root_filesystem_is_overlay:
            return True
        if self.bootloader == 'grub2_s390x_emu':
            return True
        if self.luks:
            return True

    def get_boot_label(self):
        """
        Filesystem Label to use for the boot partition

        :return: label name
        :rtype: string
        """
        label = 'BOOT'
        if self.bootloader == 'grub2_s390x_emu':
            label = 'ZIPL'
        return label

    def get_root_label(self):
        """
        Filesystem Label to use for the root partition

        If not specified in the XML configuration the default
        root label is set to 'ROOT'

        :return: label name
        :rtype: string
        """
        root_label = self.xml_state.build_type.get_rootfs_label()
        if not root_label:
            root_label = 'ROOT'
        return root_label

    def get_efi_label(self):
        """
        Filesystem Label to use for the EFI partition

        :return: label name
        :rtype: string
        """
        return 'EFI'

    def boot_partition_size(self):
        """
        Size of the boot partition in mbytes

        :return: boot size mbytes
        :rtype: int
        """
        if self.need_boot_partition():
            if self.bootpart_mbytes:
                return self.bootpart_mbytes
            else:
                return Defaults.get_default_boot_mbytes()

    def _inplace_recovery_partition_size(self):
        """
        In inplace recovery mode the recovery archive is created at
        install time. This requires free space on the disk. The
        amount of free space is specified with the oem-recovery-part-size
        attribute. If specified we add the given size to the disk.
        If not specified an inplace setup at install time will be
        moved to the first boot of an oem image when the recovery
        partition has been created
        """
        if self.oemconfig and self.oemconfig.get_oem_inplace_recovery():
            recovery_mbytes = self.oemconfig.get_oem_recovery_part_size()
            if recovery_mbytes:
                return int(recovery_mbytes[0] * 1.7)

    def _accumulate_volume_size(self, root_mbytes):
        """
        Calculate number of mbytes to add to the disk to allow
        the creaton of the volumes with their configured size
        """
        disk_volume_mbytes = 0

        data_volume_mbytes = self._calculate_volume_mbytes()
        root_volume = self._get_root_volume_configuration()

        for volume in self.volumes:
            if volume.realpath and not volume.realpath == '/' and volume.size:
                [size_type, req_size] = volume.size.split(':')
                disk_add_mbytes = 0
                if size_type == 'freespace':
                    disk_add_mbytes += int(req_size) + \
                        Defaults.get_min_volume_mbytes()
                else:
                    disk_add_mbytes += int(req_size) - \
                        data_volume_mbytes.volume[volume.realpath]
                if disk_add_mbytes > 0:
                    disk_volume_mbytes += disk_add_mbytes
                else:
                    log.warning(
                        'volume size of %s MB for %s is too small, skipped',
                        int(req_size), volume.realpath
                    )

        if root_volume:
            if root_volume.size_type == 'freespace':
                disk_add_mbytes = root_volume.req_size + \
                    Defaults.get_min_volume_mbytes()
            else:
                disk_add_mbytes = root_volume.req_size - \
                    root_mbytes + data_volume_mbytes.total

            if disk_add_mbytes > 0:
                disk_volume_mbytes += disk_add_mbytes
            else:
                log.warning(
                    'root volume size of %s MB is too small, skipped',
                    root_volume.req_size
                )

        return disk_volume_mbytes

    def _get_root_volume_configuration(self):
        """
        Provide LVRoot volume configuration if present and in
        use according to the selected volume management. So far
        this only affects the LVM volume manager
        """
        root_volume_type = namedtuple(
            'root_volume_type', ['size_type', 'req_size']
        )
        for volume in self.volumes:
            if volume.name == 'LVRoot':
                if volume.size:
                    [size_type, req_size] = volume.size.split(':')
                    return root_volume_type(
                        size_type=size_type,
                        req_size=int(req_size)
                    )

    def _calculate_volume_mbytes(self):
        """
        Calculate the number of mbytes each volume path currently
        consumes and also provide a total number of these values
        """
        volume_mbytes_type = namedtuple(
            'volume_mbytes_type', ['volume', 'total']
        )
        volume_mbytes = {}
        volume_total = 0
        for volume in self.volumes:
            if volume.realpath and not volume.realpath == '/':
                path_to_volume = self.root_dir + '/' + volume.realpath
                if os.path.exists(path_to_volume):
                    volume_size = SystemSize(path_to_volume)
                    volume_mbytes[volume.realpath] = volume_size.customize(
                        volume_size.accumulate_mbyte_file_sizes(),
                        self.filesystem
                    )
                    volume_total += volume_mbytes[volume.realpath]

        return volume_mbytes_type(
            volume=volume_mbytes,
            total=volume_total
        )
