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
import glob
import sys
from six.moves import reload_module
from collections import namedtuple
import platform
from pkg_resources import resource_filename

# project
from .path import Path
from .version import __githash__


class Defaults(object):
    """
    **Implements default values**

    Provides class methods for default values and state information
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
    def get_xz_compression_options(self):
        """
        Provides compression options for the xz compressor

        :return:
            Contains list of options

            .. code:: python

                ['--option=value']

        :rtype: list
        """
        return [
            '--threads=0'
        ]

    @classmethod
    def is_buildservice_worker(self):
        """
        Checks if build host is an open buildservice machine

        The presence of /.buildenv on the build host indicates
        we are building inside of the open buildservice

        :return: True if obs worker, else False

        :rtype: bool
        """
        return os.path.exists(
            os.sep + Defaults.get_buildservice_env_name()
        )

    @classmethod
    def get_buildservice_env_name(self):
        """
        Provides the base name of the environment file in a
        buildservice worker

        :return: file basename

        :rtype: str
        """
        return '.buildenv'

    @classmethod
    def get_obs_download_server_url(self):
        """
        Provides the default download server url hosting the public open
        buildservice repositories

        :return: url path

        :rtype: str
        """
        return 'http://download.opensuse.org/repositories'

    @classmethod
    def get_s390_disk_block_size(self):
        """
        Provides the default block size for s390 storage disks

        :return: blocksize value

        :rtype: int
        """
        return '4096'

    @classmethod
    def get_s390_disk_type(self):
        """
        Provides the default disk type for s390 storage disks

        :return: type name

        :rtype: str
        """
        return 'CDL'

    @classmethod
    def get_solvable_location(self):
        """
        Provides the directory to store SAT solvables for repositories.
        The solvable files are used to perform package
        dependency and metadata resolution

        :return: directory path

        :rtype: str
        """
        return '/var/tmp/kiwi/satsolver'

    @classmethod
    def get_shared_cache_location(self):
        """
        Provides the shared cache location

        This is a directory which shares data from the image buildsystem
        host with the image root system. The location is returned as an
        absolute path stripped off by the leading '/'. This is because
        the path is transparently used on the host /<cache-dir> and
        inside of the image imageroot/<cache-dir>

        :return: directory path

        :rtype: str
        """
        from .cli import Cli
        return os.path.abspath(os.path.normpath(
            Cli().get_global_args().get('--shared-cache-dir')
        )).lstrip(os.sep)

    @classmethod
    def get_exclude_list_for_root_data_sync(self):
        """
        Provides the list of files or folders that are created
        by KIWI for its own purposes. Those files should be not
        be included in the resulting image.

        :return: list of file and directory names

        :rtype: list
        """
        exclude_list = [
            'image', '.profile', '.kconfig',
            Defaults.get_buildservice_env_name(),
            Defaults.get_shared_cache_location()
        ]
        return exclude_list

    @classmethod
    def get_failsafe_kernel_options(self):
        """
        Provides failsafe boot kernel options

        :return:
            list of kernel options

            .. code:: python

                ['option=value', 'option']

        :rtype: list
        """
        return ' '.join(
            [
                'ide=nodma',
                'apm=off',
                'noresume',
                'edd=off',
                'nomodeset',
                '3'
            ]
        )

    @classmethod
    def get_video_mode_map(self):
        """
        Provides video mode map

        Assign a tuple to each kernel vesa hex id for each of the
        supported bootloaders

        :return:
            video type map

            .. code:: python

                {'kernel_hex_mode': video_type(grub2='mode', isolinux='mode')}

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
    def get_volume_id(self):
        """
        Provides default value for ISO volume ID

        :return: name

        :rtype: str
        """
        return 'CDROM'

    @classmethod
    def get_install_volume_id(self):
        """
        Provides default value for ISO volume ID for install media

        :return: name

        :rtype: str
        """
        return 'INSTALL'

    @classmethod
    def get_snapper_config_template_file(self):
        """
        Provides the default configuration template file for snapper

        :return: file

        :rtype: str
        """
        return '/etc/snapper/config-templates/default'

    @classmethod
    def get_default_video_mode(self):
        """
        Provides 800x600 default video mode as hex value for the kernel

        :return: vesa video kernel hex value

        :rtype: str
        """
        return '0x303'

    @classmethod
    def get_grub_boot_directory_name(self, lookup_path):
        """
        Provides grub2 data directory name in boot/ directory

        Depending on the distribution the grub2 boot path could be
        either boot/grub2 or boot/grub. The method will decide for
        the correct base directory name according to the name pattern
        of the installed grub2 tools

        :return: directory basename

        :rtype: str
        """
        chroot_env = {
            'PATH': os.sep.join([lookup_path, 'usr', 'sbin'])
        }
        if Path.which(filename='grub2-install', custom_env=chroot_env):
            # the presence of grub2-install is an indicator to put all
            # grub2 data below boot/grub2
            return 'grub2'
        else:
            # in any other case the assumption is made that all grub
            # boot data should live below boot/grub
            return 'grub'

    @classmethod
    def get_grub_basic_modules(self, multiboot):
        """
        Provides list of basic grub modules

        :param bool multiboot: grub multiboot mode

        :return: list of module names

        :rtype: list
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
            'all_video',
            'xfs',
            'btrfs',
            'lvm',
            'test',
            'true'
        ]
        if multiboot:
            modules.append('multiboot')
        return modules

    @classmethod
    def get_grub_efi_modules(self, multiboot=False):
        """
        Provides list of grub efi modules

        :param bool multiboot: grub multiboot mode

        :return: list of module names

        :rtype: list
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
        Provides list of grub bios modules

        :param bool multiboot: grub multiboot mode

        :return: list of module names

        :rtype: list
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
        Provides list of grub ofw modules (ppc)

        :return: list of module names

        :rtype: list
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
        Provides grub install path

        Depending on the distribution grub could be installed below
        a grub2 or grub directory. Therefore this information needs
        to be dynamically looked up

        :param string lookup_path: path name

        :return: grub2 install directory path name

        :rtype: str
        """
        for grub_name in ['grub2', 'grub']:
            grub_path = lookup_path + '/' + grub_name
            if os.path.exists(grub_path):
                return grub_path

    @classmethod
    def get_preparer(self):
        """
        Provides ISO preparer name

        :return: name

        :rtype: str
        """
        return 'KIWI - http://suse.github.com/kiwi'

    @classmethod
    def get_publisher(self):
        """
        Provides ISO publisher name

        :return: name

        :rtype: str
        """
        return 'SUSE LINUX GmbH'

    @classmethod
    def get_shim_loader(self, root_path):
        """
        Provides shim loader file path

        Searches distribution specific locations to find shim.efi
        below the given root path

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        shim_file_patterns = [
            '/usr/lib64/efi/shim.efi',
            '/boot/efi/EFI/*/shim.efi'
        ]
        for shim_file_pattern in shim_file_patterns:
            for shim_file in glob.iglob(root_path + shim_file_pattern):
                return shim_file

    @classmethod
    def get_unsigned_grub_loader(self, root_path):
        """
        Provides unsigned grub efi loader file path

        Searches distribution specific locations to find grub.efi
        below the given root path

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        unsigned_grub_file_patterns = [
            '/usr/lib/grub*/*-efi/grub.efi'
        ]
        for unsigned_grub_file_pattern in unsigned_grub_file_patterns:
            for unsigned_grub_file in glob.iglob(
                root_path + unsigned_grub_file_pattern
            ):
                return unsigned_grub_file

    @classmethod
    def get_signed_grub_loader(self, root_path):
        """
        Provides shim signed grub loader file path

        Searches distribution specific locations to find grub.efi
        below the given root path

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        signed_grub_file_patterns = [
            '/usr/lib64/efi/grub.efi',
            '/boot/efi/EFI/*/grub*.efi'
        ]
        for signed_grub_pattern in signed_grub_file_patterns:
            for signed_grub in glob.iglob(root_path + signed_grub_pattern):
                return signed_grub

    @classmethod
    def get_shim_vendor_directory(self, root_path):
        """
        Provides shim vendor directory

        Searches distribution specific locations to find shim.efi
        below the given root path and return the directory name
        to the file found

        :param string root_path: image root path

        :return: directory path or None

        :rtype: str
        """
        shim_vendor_patterns = [
            '/boot/efi/EFI/*/shim.efi',
            '/EFI/*/shim.efi'
        ]
        for shim_vendor_pattern in shim_vendor_patterns:
            for shim_file in glob.iglob(root_path + shim_vendor_pattern):
                return os.path.dirname(shim_file)

    @classmethod
    def get_default_volume_group_name(self):
        """
        Provides default LVM volume group name

        :return: name

        :rtype: str
        """
        return 'systemVG'

    @classmethod
    def get_min_volume_mbytes(self):
        """
        Provides default minimum LVM volume size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 30

    @classmethod
    def get_lvm_overhead_mbytes(self):
        """
        Provides empiric LVM overhead size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 80

    @classmethod
    def get_default_boot_mbytes(self):
        """
        Provides default boot partition size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 300

    @classmethod
    def get_default_efi_boot_mbytes(self):
        """
        Provides default EFI partition size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 20

    @classmethod
    def get_recovery_spare_mbytes(self):
        """
        Provides spare size of recovery partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 300

    @classmethod
    def get_default_legacy_bios_mbytes(self):
        """
        Provides default size of bios_grub partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 2

    @classmethod
    def get_default_prep_mbytes(self):
        """
        Provides default size of prep partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 8

    @classmethod
    def get_disk_format_types(self):
        """
        Provides supported disk format types

        :return: disk types

        :rtype: list
        """
        return [
            'gce', 'qcow2', 'vmdk', 'ova', 'vmx', 'vhd', 'vhdx',
            'vhdfixed', 'vdi', 'vagrant.libvirt.box'
        ]

    @classmethod
    def get_firmware_types(self):
        """
        Provides supported architecture specific firmware types

        :return: firmware types per architecture

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
        Provides default firmware for specified architecture

        :param string arch: platform.machine

        :return: firmware name

        :rtype: str
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
        Provides list of EFI capable firmware names. These are
        those for which kiwi supports the creation of an EFI
        bootable disk image

        :return: firmware names

        :rtype: list
        """
        return ['efi', 'uefi']

    @classmethod
    def get_ec2_capable_firmware_names(self):
        """
        Provides list of EC2 capable firmware names. These are
        those for which kiwi supports the creation of disk images
        bootable within the Amazon EC2 public cloud

        :return: firmware names

        :rtype: list
        """
        return ['ec2']

    @classmethod
    def get_efi_module_directory_name(self, arch):
        """
        Provides architecture specific EFI directory name which
        stores the EFI binaries for the desired architecture.

        :param string arch: platform.machine

        :return: directory name

        :rtype: str
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
        Provides architecture specific EFI boot binary name

        :param string arch: platform.machine

        :return: name

        :rtype: str
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
        Provides default boot timeout in seconds

        :return: seconds

        :rtype: int
        """
        return 10

    @classmethod
    def get_default_disk_start_sector(self):
        """
        Provides the default initial disk sector for the first disk
        partition.

        :return: sector value

        :rtype: int
        """
        return Defaults().defaults['kiwi_startsector']

    @classmethod
    def get_default_efi_partition_table_type(self):
        """
        Provides the default partition table type for efi firmwares.

        :return: partition table type name

        :rtype: str
        """
        return 'gpt'

    @classmethod
    def get_default_inode_size(self):
        """
        Provides default size of inodes in bytes. This is only
        relevant for inode based filesystems

        :return: bytesize value

        :rtype: int
        """
        return Defaults().defaults['kiwi_inode_size']

    @classmethod
    def get_archive_image_types(self):
        """
        Provides list of supported archive image types

        :return: archive names

        :rtype: list
        """
        return ['tbz']

    @classmethod
    def get_container_image_types(self):
        """
        Provides list of supported container image types

        :return: container names

        :rtype: list
        """
        return ['docker', 'oci']

    @classmethod
    def get_filesystem_image_types(self):
        """
        Provides list of supported filesystem image types

        :return: filesystem names

        :rtype: list
        """
        return [
            'ext2', 'ext3', 'ext4', 'btrfs', 'squashfs',
            'xfs', 'fat16', 'fat32'
        ]

    @classmethod
    def get_default_live_iso_type(self):
        """
        Provides default live iso union type

        :return: live iso type

        :rtype: str
        """
        return 'overlay'

    @classmethod
    def get_default_uri_type(self):
        """
        Provides default URI type

        Absolute path specifications used in the context of an URI
        will apply the specified default mime type

        :return: URI mime type

        :rtype: str
        """
        return 'dir:/'

    @classmethod
    def get_dracut_conf_name(self):
        """
        Provides file path of dracut config file to be used with KIWI

        :return: file path name

        :rtype: str
        """
        return '/etc/dracut.conf.d/02-kiwi.conf'

    @classmethod
    def get_live_dracut_module_from_flag(self, flag_name):
        """
        Provides flag_name to dracut module name map

        Depending on the value of the flag attribute in the KIWI image
        description a specific dracut module needs to be selected

        :return: dracut module name

        :rtype: str
        """
        live_modules = {
            'overlay': 'kiwi-live',
            'dmsquash': 'dmsquash-live livenet'
        }
        if flag_name in live_modules:
            return live_modules[flag_name]
        else:
            return 'kiwi-live'

    @classmethod
    def get_default_live_iso_root_filesystem(self):
        """
        Provides default live iso root filesystem type

        :return: filesystem name

        :rtype: str
        """
        return 'ext4'

    @classmethod
    def get_live_iso_persistent_boot_options(self, persistent_filesystem=None):
        """
        Provides list of boot options passed to the dracut
        kiwi-live module to setup persistent writing

        :return: list of boot options

        :rtype: list
        """
        live_iso_persistent_boot_options = [
            'rd.live.overlay.persistent'
        ]
        if persistent_filesystem:
            live_iso_persistent_boot_options.append(
                'rd.live.overlay.cowfs={0}'.format(persistent_filesystem)
            )
        return live_iso_persistent_boot_options

    @classmethod
    def get_disk_image_types(self):
        """
        Provides supported disk image types

        :return: disk image type names

        :rtype: list
        """
        return ['oem', 'vmx']

    @classmethod
    def get_live_image_types(self):
        """
        Provides supported live image types

        :return: live image type names

        :rtype: list
        """
        return ['iso']

    @classmethod
    def get_network_image_types(self):
        """
        Provides supported pxe image types

        :return: pxe image type names

        :rtype: list
        """
        return ['pxe']

    @classmethod
    def get_boot_image_description_path(self):
        """
        Provides the path to find custom kiwi boot descriptions

        :return: directory path

        :rtype: str
        """
        return '/usr/share/kiwi/custom_boot'

    @classmethod
    def get_boot_image_strip_file(self):
        """
        Provides the file path to bootloader strip metadata.
        This file contains information about the files and directories
        automatically striped out from the kiwi initrd

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('config/strip.xml')

    @classmethod
    def get_schema_file(self):
        """
        Provides file path to kiwi RelaxNG schema

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('schema/kiwi.rng')

    @classmethod
    def get_common_functions_file(self):
        """
        Provides the file path to config functions metadata.

        This file contains bash functions used for system
        configuration or in the boot code from the kiwi initrd

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('config/functions.sh')

    @classmethod
    def get_xsl_stylesheet_file(self):
        """
        Provides the file path to the KIWI XSLT style sheets

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('xsl/master.xsl')

    @classmethod
    def project_file(self, filename):
        """
        Provides the python module base directory search path

        The method uses the resource_filename method to identify
        files and directories from the application

        :param string filename: relative project file

        :return: absolute file path name

        :rtype: str
        """
        return resource_filename('kiwi', filename)

    @classmethod
    def get_imported_root_image(self, root_dir):
        """
        Provides the path to an imported root system image

        If the image description specified a derived_from attribute
        the file from this attribute is copied into the root_dir
        using the name as provided by this method

        :param string root_dir: image root directory

        :return: file path name

        :rtype: str
        """
        return os.sep.join([root_dir, 'image', 'imported_root'])

    @classmethod
    def get_iso_boot_path(self):
        """
        Provides arch specific relative path to boot files
        on kiwi iso filesystems

        :return: relative path name

        :rtype: str
        """
        arch = platform.machine()
        if arch == 'i686' or arch == 'i586':
            arch = 'ix86'
        return os.sep.join(['boot', arch])

    @classmethod
    def get_iso_tool_category(self):
        """
        Provides default iso tool category

        :return: name

        :rtype: str
        """
        return 'xorriso'

    @classmethod
    def get_container_compression(self):
        """
        Provides default container compression algorithm

        :return: name

        :rtype: str
        """
        return 'xz'

    @classmethod
    def get_default_container_name(self):
        """
        Provides the default container name.

        :return: name

        :rtype: str
        """
        return 'kiwi-container'

    @classmethod
    def get_default_container_tag(self):
        """
        Provides the default container tag.

        :return: tag

        :rtype: str
        """
        return 'latest'

    @classmethod
    def set_python_default_encoding_to_utf8(self):
        """
        Set python default encoding to utf-8 if not already done

        This is not a safe operation since sys.setdefaultencoding()
        was removed from sys on purpose when Python starts. Reenabling
        it and changing the default encoding can break code that relies
        on ascii being the default. Within the scope of kiwi the
        operation is safe because all data is expected to be utf-8
        everywhere and considered a bug if this is not the case
        """
        if sys.version_info.major < 3:
            reload_module(sys)  # Reload required to get setdefaultencoding back
            sys.setdefaultencoding('utf-8')

    @classmethod
    def get_default_packager_tool(self, package_manager):
        """
        Provides the packager tool according to the package manager

        :param string package_manager: package manger name

        :return: packager tool binary name

        :rtype: str
        """
        rpm_based = ['zypper', 'yum', 'dnf']
        deb_based = ['apt-get']
        if package_manager in rpm_based:
            return 'rpm'
        elif package_manager in deb_based:
            return 'dpkg'

    @classmethod
    def get_default_rpmdb_path(self):
        """
        Returns the default path of the rpm database.

        :return: rpmdb default path

        :rtype: str
        """
        return '/var/lib/rpm'

    def get(self, key):
        """
        Implements get method for profile elements

        :param string key: profile keyname

        :return: key value

        :rtype: str
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
            # Do not apply default values to any variable that was
            # already defined in the profile instance.
            if (key not in profile.dot_profile or
                    profile.dot_profile[key] is None):
                profile.add(key, self.get(key))
