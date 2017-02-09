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
import platform
from pkg_resources import resource_filename

# project
from .version import __githash__


class Defaults(object):
    """
    Default values and export methods

    Attributes

    * :attr:`defaults`
        dict of default profile values

    * :attr:`profile_key_list`
        list of profile keys to import into an instance of Profile
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
            'kiwi_revision': __githash__
        }
        self.profile_key_list = [
            'kiwi_align',
            'kiwi_startsector',
            'kiwi_sectorsize',
            'kiwi_revision'
        ]

    @classmethod
    def is_obs_worker(self):
        # the presence of /.buildenv on the build host indicates
        # we are building inside of the open buildservice
        return os.path.exists('/.buildenv')

    @classmethod
    def get_s390_disk_block_size(self):
        """
        The default block size for s390 storage disks
        """
        return '4096'

    @classmethod
    def get_s390_disk_type(self):
        """
        The default disk type for s390 storage disks
        """
        return 'CDL'

    @classmethod
    def get_solvable_location(self):
        """
        The directory to store SAT solvables for repositories.
        The solvable files are used to perform package
        dependency and metadata resolution
        """
        return '/var/tmp/kiwi/satsolver'

    @classmethod
    def get_shared_cache_location(self):
        """
        The shared location is a directory which shares data from
        the image buildsystem host with the image root system.
        The location is returned as an absolute path stripped off
        by the leading '/'. This is because the path is transparently
        used on the host /<cache-dir> and inside of the image
        imageroot/<cache-dir>
        """
        from .cli import Cli
        return os.path.abspath(os.path.normpath(
            Cli().get_global_args().get('--shared-cache-dir')
        )).lstrip(os.sep)

    @classmethod
    def get_failsafe_kernel_options(self):
        """
        Failsafe boot kernel options

        :return: kernel options list
        :rtype: list
        """
        return ' '.join(
            [
                'ide=nodma',
                'apm=off',
                'noresume',
                'edd=off',
                'powersaved=off',
                'nohz=off',
                'highres=off',
                'processsor.max+cstate=1',
                'nomodeset',
                'x11failsafe'
            ]
        )

    @classmethod
    def get_video_mode_map(self):
        """
        Implements video mode map

        Assign a tuple to each kernel vesa hex id for each of the
        supported bootloaders

        :return: video type map
        :rtype: dict
        """
        video_type = namedtuple(
            'video_type', ['grub2', 'isolinux']
        )
        return {
            '0x301': video_type(grub2='640x480', isolinux='640 480'),
            '0x310': video_type(grub2='640x480', isolinux='640 480'),
            '0x311': video_type(grub2='640x480', isolinux='640 480'),
            '0x312': video_type(grub2='640x480', isolinux='640 480'),
            '0x303': video_type(grub2='800x600', isolinux='800 600'),
            '0x313': video_type(grub2='800x600', isolinux='800 600'),
            '0x314': video_type(grub2='800x600', isolinux='800 600'),
            '0x315': video_type(grub2='800x600', isolinux='800 600'),
            '0x305': video_type(grub2='1024x768', isolinux='1024 768'),
            '0x316': video_type(grub2='1024x768', isolinux='1024 768'),
            '0x317': video_type(grub2='1024x768', isolinux='1024 768'),
            '0x318': video_type(grub2='1024x768', isolinux='1024 768'),
            '0x307': video_type(grub2='1280x1024', isolinux='1280 1024'),
            '0x319': video_type(grub2='1280x1024', isolinux='1280 1024'),
            '0x31a': video_type(grub2='1280x1024', isolinux='1280 1024'),
            '0x31b': video_type(grub2='1280x1024', isolinux='1280 1024'),
        }

    @classmethod
    def get_default_video_mode(self):
        """
        Implements 800x600 default video mode

        :return: video mode name
        :rtype: string
        """
        return '0x303'

    @classmethod
    def get_grub_basic_modules(self, multiboot):
        """
        Implements list of basic grub modules

        :param bool multiboot: grub multiboot mode

        :return: module name
        :rtype: string
        """
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
            'lvm',
            'test'
        ]
        if multiboot:
            modules.append('multiboot')
        return modules

    @classmethod
    def get_grub_efi_modules(self, multiboot=False):
        """
        Implements list of grub efi modules

        :param bool multiboot: grub multiboot mode

        :return: module name
        :rtype: string
        """
        host_architecture = platform.machine()
        modules = Defaults.get_grub_basic_modules(multiboot) + [
            'part_gpt',
            'part_msdos',
            'efi_gop'
        ]
        if host_architecture == 'x86_64':
            modules += [
                'efi_uga',
                'linuxefi'
            ]
        return modules

    @classmethod
    def get_grub_bios_modules(self, multiboot=False):
        """
        Implements list of grub bios modules

        :param bool multiboot: grub multiboot mode

        :return: module name
        :rtype: string
        """
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
        """
        Implements list of grub ofw modules (ppc)

        :return: module name
        :rtype: string
        """
        modules = Defaults.get_grub_basic_modules(multiboot=False) + [
            'part_gpt',
            'part_msdos',
            'boot'
        ]
        return modules

    @classmethod
    def get_grub_path(self, lookup_path):
        """
        Depending on the distribution grub could be installed below
        a grub2 or grub directory. Therefore this information needs
        to be dynamically looked up

        :param string lookup_path: path name

        :return: grub2 install directory path name
        :rtype: string
        """
        for grub_name in ['grub2', 'grub']:
            grub_path = lookup_path + '/' + grub_name
            if os.path.exists(grub_path):
                return grub_path

    @classmethod
    def get_preparer(self):
        """
        Implements ISO preparer name

        :return: name
        :rtype: string
        """
        return 'KIWI - http://suse.github.com/kiwi'

    @classmethod
    def get_publisher(self):
        """
        Implements ISO publisher name

        :return: name
        :rtype: string
        """
        return 'SUSE LINUX GmbH'

    @classmethod
    def get_shim_name(self):
        return 'shim.efi'

    @classmethod
    def get_signed_grub_name(self):
        return 'grub.efi'

    @classmethod
    def get_default_volume_group_name(self):
        """
        Implements default LVM volume group name

        :return: name
        :rtype: string
        """
        return 'systemVG'

    @classmethod
    def get_min_volume_mbytes(self):
        """
        Implements default minimum LVM volume size in mbytes

        :return: mbsize
        :rtype: int
        """
        return 30

    @classmethod
    def get_default_boot_mbytes(self):
        """
        Implements default boot partition size in mbytes

        :return: mbsize
        :rtype: int
        """
        return 300

    @classmethod
    def get_default_efi_boot_mbytes(self):
        """
        Implements default EFI partition size in mbytes

        :return: mbsize
        :rtype: int
        """
        return 20

    @classmethod
    def get_recovery_spare_mbytes(self):
        """
        Implements spare size of recovery partition in mbytes

        :return: mbsize
        :rtype: int
        """
        return 300

    @classmethod
    def get_default_legacy_bios_mbytes(self):
        """
        Implements default size of bios_grub partition in mbytes

        :return: mbsize
        :rtype: int
        """
        return 2

    @classmethod
    def get_default_prep_mbytes(self):
        """
        Implements default size of prep partition in mbytes

        :return: mbsize
        :rtype: int
        """
        return 8

    @classmethod
    def get_disk_format_types(self):
        """
        Implements supported disk format types

        :return: disk types
        :rtype: list
        """
        return [
            'gce', 'qcow2', 'vmdk', 'vmx', 'vhd',
            'vhdfixed', 'vdi', 'vagrant.libvirt.box'
        ]

    @classmethod
    def get_firmware_types(self):
        """
        Implements supported architecture specific firmware types

        :return: firmware types
        :rtype: dict
        """
        return {
            'x86_64': ['efi', 'uefi', 'bios', 'ec2hvm', 'ec2'],
            'i586': ['bios'],
            'i686': ['bios'],
            'aarch64': ['efi', 'uefi'],
            'arm64': ['efi', 'uefi'],
            'armv5el': ['efi', 'uefi'],
            'armv5tel': ['efi', 'uefi'],
            'armv6hl': ['efi', 'uefi'],
            'armv6l': ['efi', 'uefi'],
            'armv7hl': ['efi', 'uefi'],
            'armv7l': ['efi', 'uefi'],
            'ppc': ['ofw'],
            'ppc64': ['ofw', 'opal'],
            'ppc64le': ['ofw', 'opal'],
            's390': [],
            's390x': []
        }

    @classmethod
    def get_default_firmware(self, arch):
        """
        Implements default firmware for specified architecture

        :param string arch: platform.machine

        :return: firmware
        :rtype: string
        """
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
        """
        Implements list of EFI capable firmware names. These are
        those for which kiwi supports the creation of an EFI
        bootable disk image

        :return: firmware names
        :rtype: list
        """
        return ['efi', 'uefi']

    @classmethod
    def get_ec2_capable_firmware_names(self):
        """
        Implements list of EC2 capable firmware names. These are
        those for which kiwi supports the creation of disk images
        bootable within the Amazon EC2 public cloud

        :return: firmware names
        :rtype: list
        """
        return ['ec2', 'ec2hvm']

    @classmethod
    def get_efi_module_directory_name(self, arch):
        """
        Implements architecture specific EFI directory name which
        stores the EFI binaries for the desired architecture.

        :param string arch: platform.machine

        :return: directory name
        :rtype: string
        """
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
        """
        Implements architecture specific EFI boot binary name

        :param string arch: platform.machine

        :return: name
        :rtype: string
        """
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
        """
        Implements default boot timeout in seconds

        :return: seconds
        :rtype: int
        """
        return 10

    @classmethod
    def get_default_inode_size(self):
        """
        Implements default size of inodes in bytes. This is only
        relevant for inode based filesystems

        :return: bytesize
        :rtype: int
        """
        return 256

    @classmethod
    def get_archive_image_types(self):
        """
        Implements list of supported archive image types

        :return: archive names
        :rtype: list
        """
        return ['tbz']

    @classmethod
    def get_container_image_types(self):
        """
        Implements list of supported container image types

        :return: container names
        :rtype: list
        """
        return ['docker', 'aci']

    @classmethod
    def get_filesystem_image_types(self):
        """
        Implements list of supported filesystem image types

        :return: filesystem names
        :rtype: list
        """
        return [
            'ext2', 'ext3', 'ext4', 'btrfs', 'squashfs',
            'xfs', 'fat16', 'fat32'
        ]

    @classmethod
    def get_live_iso_types(self):
        """
        Implements list of supported live ISO image types

        :return: live iso names
        :rtype: list
        """
        return {
            'overlay': 'squashfs',
            'clic': 'clicfs'
        }

    @classmethod
    def get_live_iso_client_parameters(self):
        """
        Implements parameters to setup the overlay filesystem used
        for the live ISO image. Each supported overlay filesystem
        needs the information about the target block device, the
        copy on write device and the used kernel union filesystem
        name

        :return: union client parameters
        :rtype: dict
        """
        return {
            'overlay': ['loop', 'tmpfs', 'overlay'],
            'clic': ['/dev/ram1', '/dev/ram1', 'clicfs']
        }

    @classmethod
    def get_default_live_iso_type(self):
        """
        Implements default live iso union type

        :return: live iso type
        :rtype: string
        """
        return 'overlay'

    @classmethod
    def get_disk_image_types(self):
        """
        Implements supported disk image types

        :return: disk image type names
        :rtype: list
        """
        return ['oem', 'vmx']

    @classmethod
    def get_live_image_types(self):
        """
        Implements supported live image types

        :return: live image type names
        :rtype: list
        """
        return ['iso']

    @classmethod
    def get_network_image_types(self):
        """
        Implements supported pxe image types

        :return: pxe image type names
        :rtype: list
        """
        return ['pxe']

    @classmethod
    def get_boot_image_description_path(self):
        """
        Implements bootloader path for ISO images

        :return: directory path
        :rtype: string
        """
        return Defaults.project_file('boot/arch/' + platform.machine())

    @classmethod
    def get_boot_image_strip_file(self):
        """
        Implements file path to bootloader strip metadata.
        This file contains information about the files and directories
        automatically striped out from the kiwi initrd

        :return: file path
        :rtype: string
        """
        return Defaults.project_file('config/strip.xml')

    @classmethod
    def get_schema_file(self):
        """
        Implements file path to kiwi RNG schema

        :return: file path
        :rtype: string
        """
        return Defaults.project_file('schema/kiwi.rng')

    @classmethod
    def get_common_functions_file(self):
        """
        Implements file path to bootloader functions metadata.
        This file contains bash functions used in the boot code
        from the kiwi initrd

        :return: file path
        :rtype: string
        """
        return Defaults.project_file('config/functions.sh')

    @classmethod
    def get_xsl_stylesheet_file(self):
        """
        Implements file path to kiwi XSLT style sheets

        :return: file path
        :rtype: string
        """
        return Defaults.project_file('xsl/master.xsl')

    @classmethod
    def project_file(self, filename):
        """
        Implements python module base directory search path
        The method uses the resource_filename method to identify
        files and directories from the application

        :param string filename: relative project file

        :return: full qualified filename
        :rtype: string
        """
        return resource_filename('kiwi', filename)

    def get(self, key):
        """
        Implements get method for profile elements

        :param string key: profile keyname

        :return: key value
        :rtype: string
        """
        if key in self.defaults:
            return self.defaults[key]

    def to_profile(self, profile):
        """
        Implements method to add list of profile keys and their values
        to the specified instance of a Profile class

        :param object profile: Profile instance
        """
        for key in sorted(self.profile_key_list):
            profile.add(key, self.get(key))
