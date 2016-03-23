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
from collections import namedtuple
import platform
import re
from pkg_resources import resource_filename
from .version import __githash__


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
    def get_video_mode_map(self):
        video_type = namedtuple(
            'video_type', ['grub2']
        )
        return {
            '0x301': video_type(grub2='640x480'),
            '0x310': video_type(grub2='640x480'),
            '0x311': video_type(grub2='640x480'),
            '0x312': video_type(grub2='640x480'),
            '0x303': video_type(grub2='800x600'),
            '0x313': video_type(grub2='800x600'),
            '0x314': video_type(grub2='800x600'),
            '0x315': video_type(grub2='800x600'),
            '0x305': video_type(grub2='1024x768'),
            '0x316': video_type(grub2='1024x768'),
            '0x317': video_type(grub2='1024x768'),
            '0x318': video_type(grub2='1024x768'),
            '0x307': video_type(grub2='1280x1024'),
            '0x319': video_type(grub2='1280x1024'),
            '0x31a': video_type(grub2='1280x1024'),
            '0x31b': video_type(grub2='1280x1024'),
        }

    @classmethod
    def get_default_video_mode(self):
        # 800x600 default video mode
        return '0x303'

    @classmethod
    def get_grub_basic_modules(self, multiboot):
        modules = [
            'ext2',
            'iso9660',
            'linux',
            'echo',
            'configfile',
            'search_label',
            'search_fs_file',
            'search',
            'search_fs_uuid',
            'ls',
            'normal',
            'gzio',
            'png',
            'fat',
            'gettext',
            'font',
            'minicmd',
            'gfxterm',
            'gfxmenu',
            'video',
            'video_fb',
            'xfs',
            'btrfs',
            'lvm'
        ]
        if multiboot:
            modules.append('multiboot')
        return modules

    @classmethod
    def get_grub_efi_modules(self, multiboot=False):
        modules = Defaults.get_grub_basic_modules(multiboot) + [
            'part_gpt',
            'efi_gop',
            'linuxefi'
        ]
        return modules

    @classmethod
    def get_grub_bios_modules(self, multiboot=False):
        modules = Defaults.get_grub_basic_modules(multiboot) + [
            'part_gpt',
            'part_msdos',
            'biosdisk',
            'vga',
            'vbe',
            'chain',
            'boot'
        ]
        return modules

    @classmethod
    def get_grub_ofw_modules(self):
        modules = Defaults.get_grub_basic_modules(multiboot=False) + [
            'part_gpt',
            'part_msdos',
            'boot'
        ]
        return modules

    @classmethod
    def get_preparer(self):
        return 'KIWI - http://suse.github.com/kiwi'

    @classmethod
    def get_publisher(self):
        return 'SUSE LINUX GmbH'

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
    def get_default_vboot_mbytes(self):
        return 10

    @classmethod
    def get_default_efi_boot_mbytes(self):
        return 200

    @classmethod
    def get_recovery_spare_mbytes(self):
        return 300

    @classmethod
    def get_default_legacy_bios_mbytes(self):
        return 2

    @classmethod
    def get_default_prep_mbytes(self):
        return 8

    @classmethod
    def get_disk_format_types(self):
        return ['gce', 'qcow2', 'vmdk', 'vhd', 'vhdfixed']

    @classmethod
    def get_firmware_types(self):
        return {
            'x86_64': ['efi', 'uefi', 'bios', 'ec2hvm', 'ec2'],
            'i586': ['bios'],
            'i686': ['bios'],
            'aarch64': ['efi', 'uefi', 'vboot'],
            'arm64': ['efi', 'uefi', 'vboot'],
            'armv5el': ['efi', 'uefi', 'vboot'],
            'armv5tel': ['efi', 'uefi', 'vboot'],
            'armv6hl': ['efi', 'uefi', 'vboot'],
            'armv6l': ['efi', 'uefi', 'vboot'],
            'armv7hl': ['efi', 'uefi', 'vboot'],
            'armv7l': ['efi', 'uefi', 'vboot'],
            'ppc': ['ofw'],
            'ppc64': ['ofw', 'opal'],
            'ppc64le': ['ofw', 'opal'],
            's390': [],
            's390x': []
        }

    @classmethod
    def get_default_firmware(self, arch):
        default_firmware = {
            'x86_64': 'bios',
            'i586': 'bios',
            'i686': 'bios',
            'ppc': 'ofw',
            'ppc64': 'ofw',
            'ppc64le': 'ofw',
            'arm64': 'efi',
            'armv5el': 'efi',
            'armv5tel': 'efi',
            'armv6hl': 'efi',
            'armv6l': 'efi',
            'armv7hl': 'efi',
            'armv7l': 'efi'
        }
        if arch in default_firmware:
            return default_firmware[arch]

    @classmethod
    def get_efi_capable_firmware_names(self):
        return ['efi', 'uefi', 'vboot']

    @classmethod
    def get_ec2_capable_firmware_names(self):
        return ['ec2', 'ec2hvm']

    @classmethod
    def get_efi_module_directory_name(self, arch):
        default_module_directory_names = {
            'x86_64': 'x86_64-efi',

            # There is no dedicated xen architecture but there are
            # modules provided for xen. Thus we treat it as an
            # architecture
            'x86_64_xen': 'x86_64-xen',

            'aarch64': 'arm64-efi',
            'arm64': 'arm64-efi',
            'armv5el': 'arm-efi',
            'armv5tel': 'arm-efi',
            'armv6l': 'arm-efi',
            'armv7l': 'arm-efi'
        }
        if arch in default_module_directory_names:
            return default_module_directory_names[arch]

    @classmethod
    def get_efi_image_name(self, arch):
        default_efi_image_names = {
            'x86_64': 'bootx64.efi',
            'aarch64': 'bootaa64.efi',
            'arm64': 'bootaa64.efi',
            'armv5el': 'bootarm.efi',
            'armv5tel': 'bootarm.efi',
            'armv6l': 'bootarm.efi',
            'armv7l': 'bootarm.efi'
        }
        if arch in default_efi_image_names:
            return default_efi_image_names[arch]

    @classmethod
    def get_default_boot_timeout_seconds(self):
        return 10

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
    def get_live_iso_types(self):
        return {
            'overlay': 'squashfs',
            'clic': 'clicfs'
        }

    @classmethod
    def get_live_iso_client_parameters(self):
        return {
            'overlay': ['loop', 'tmpfs', 'overlay'],
            'clic': ['/dev/ram1', '/dev/ram1', 'clicfs']
        }

    @classmethod
    def get_default_live_iso_type(self):
        return 'overlay'

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
