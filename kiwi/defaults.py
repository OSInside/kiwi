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
import platform
import re
from pkg_resources import resource_filename
from version import __githash__


class Defaults(object):
    """
        Default values and export methods
    """
    def __init__(self):
        self.defaults = {
            # alignment in bytes
            'kiwi_align': 1048576,
            # start sector number
            'kiwi_startsector': 2048,
            # sectorsize in bytes
            'kiwi_sectorsize': 512,
            # inode size in bytes for inode based filesystems
            'kiwi_inode_size': 256,
            # inode ratio for inode based filesystems
            'kiwi_inode_ratio': 16384,
            # minimum inode number for inode based filesystems
            'kiwi_min_inodes': 20000,
            # kiwi git revision
            'kiwi_revision': self.__kiwi_revision()
        }
        self.profile_key_list = [
            'kiwi_align',
            'kiwi_startsector',
            'kiwi_sectorsize',
            'kiwi_revision'
        ]

    @classmethod
    def get_shim_name(self):
        return 'shim.efi'

    @classmethod
    def get_signed_grub_name(self):
        return 'grub.efi'

    @classmethod
    def get_default_volume_group_name(self):
        return 'systemVG'

    @classmethod
    def get_min_volume_mbytes(self):
        return 30

    @classmethod
    def get_default_boot_mbytes(self):
        return 200

    @classmethod
    def get_default_efi_boot_mbytes(self):
        return 200

    @classmethod
    def get_default_legacy_bios_mbytes(self):
        return 2

    @classmethod
    def get_firmware_types(self):
        return {
            'x86_64': ['efi', 'uefi', 'bios', 'ec2hvm', 'ec2'],
            'i586': ['bios'],
            'i686': ['bios'],
            'aarch64': ['vboot'],
            'arm64': ['vboot'],
            'armv5el': ['vboot'],
            'armv5tel': ['vboot'],
            'armv6l': ['vboot'],
            'armv7l': ['vboot'],
            'ppc': ['ofw'],
            'ppc64': ['ofw'],
            'ppc64le': ['ofw'],
            's390': [],
            's390x': [],
        }

    @classmethod
    def get_default_inode_size(self):
        return 256

    @classmethod
    def get_archive_image_types(self):
        return ['tbz']

    @classmethod
    def get_container_image_types(self):
        return ['docker', 'aci']

    @classmethod
    def get_filesystem_image_types(self):
        return [
            'ext2', 'ext3', 'ext4', 'btrfs', 'squashfs',
            'xfs', 'fat16', 'fat32'
        ]

    @classmethod
    def get_disk_image_types(self):
        return ['oem', 'vmx']

    @classmethod
    def get_live_image_types(self):
        return ['iso']

    @classmethod
    def get_network_image_types(self):
        return ['pxe']

    @classmethod
    def get_boot_image_description_path(self):
        return Defaults.project_file('boot/arch/' + platform.machine())

    @classmethod
    def get_boot_image_strip_file(self):
        return Defaults.project_file('config/strip.xml')

    @classmethod
    def get_schema_file(self):
        return Defaults.project_file('schema/kiwi.rng')

    @classmethod
    def get_common_functions_file(self):
        return Defaults.project_file('config/functions.sh')

    @classmethod
    def get_xsl_stylesheet_file(self):
        return Defaults.project_file('xsl/master.xsl')

    @classmethod
    def project_file(self, filename):
        return resource_filename('kiwi', filename)

    def get(self, key):
        if key in self.defaults:
            return self.defaults[key]

    def to_profile(self, profile):
        for key in sorted(self.profile_key_list):
            profile.add(key, self.get(key))

    def __kiwi_revision(self):
        githash = re.match('\$Id: (.*) \$', __githash__)
        if githash:
            return githash.group(1)
