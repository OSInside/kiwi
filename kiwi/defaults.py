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
import logging
import os
import glob
import importlib
from importlib.resources import as_file
from importlib.util import find_spec
from importlib.machinery import ModuleSpec
from collections import namedtuple
import platform
import yaml
from typing import (
    List, NamedTuple, Optional, Dict
)

# project
from kiwi.path import Path
from kiwi.version import (
    __githash__,
    __version__
)

from kiwi.exceptions import KiwiBootLoaderGrubDataError

shim_loader_type = NamedTuple(
    'shim_loader_type', [
        ('filename', str),
        ('binaryname', str)
    ]
)

grub_loader_type = NamedTuple(
    'grub_loader_type', [
        ('filename', str),
        ('binaryname', str)
    ]
)

unit_type = NamedTuple(
    'unit_type', [
        ('byte', str),
        ('kb', str),
        ('mb', str),
        ('gb', str)
    ]
)


# Default module variables
DM_METADATA_FORMAT_VERSION = '1'
DM_METADATA_OFFSET = 4096  # 4kb
VERITY_DATA_BLOCKSIZE = 4096  # 4kb
VERITY_HASH_BLOCKSIZE = 4096  # 4kb
INTEGRITY_SECTOR_SIZE = 512

INTEGRITY_ALGORITHM = 'sha256'
INTEGRITY_KEY_ALGORITHM = 'hmac-sha256'

UNIT = unit_type(byte='b', kb='k', mb='m', gb='g')
POST_DISK_SYNC_SCRIPT = 'disk.sh'
PRE_DISK_SYNC_SCRIPT = 'pre_disk_sync.sh'
POST_BOOTSTRAP_SCRIPT = 'post_bootstrap.sh'
POST_PREPARE_SCRIPT = 'config.sh'
POST_PREPARE_OVERLAY_SCRIPT = 'config-overlay.sh'
POST_HOST_PREPARE_OVERLAY_SCRIPT = 'config-host-overlay.sh'
PRE_CREATE_SCRIPT = 'images.sh'
EDIT_BOOT_CONFIG_SCRIPT = 'edit_boot_config.sh'
EDIT_BOOT_INSTALL_SCRIPT = 'edit_boot_install.sh'
IMAGE_METADATA_DIR = 'image'
ROOT_VOLUME_NAME = 'LVRoot'
SHARED_CACHE_DIR = '/var/cache/kiwi'
MODULE_SPEC: Optional[ModuleSpec] = find_spec('kiwi')
RUNTIME_CHECKER_METADATA = '{}/runtime_checker_metadata.yml'.format(
    os.path.dirname(MODULE_SPEC.origin or 'unknown')
) if MODULE_SPEC else 'unknown'

TEMP_DIR = '/var/tmp'
LOCAL_CONTAINERS = '/var/tmp/kiwi_containers'
CUSTOM_RUNTIME_CONFIG_FILE = None
PLATFORM_MACHINE = platform.machine()
EFI_FAT_IMAGE_SIZE = 20

# optional package manager environment variables
PACKAGE_MANAGER_ENV_VARS = '/.kiwi.package_manager.env'

log = logging.getLogger('kiwi')


class Defaults:
    """
    **Implements default values**

    Provides static methods for default values and state information
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

    @staticmethod
    def get_luks_key_length():
        """
        Provides key length to use for random luks keys
        """
        return 256

    @staticmethod
    def get_swapsize_mbytes():
        """
        Provides swapsize in MB
        """
        return 128

    @staticmethod
    def get_xz_compression_options():
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

    @staticmethod
    def get_platform_name():
        """
        Provides the machine architecture name as used by KIWI

        This is the architecture name as it is returned by 'uname -m'
        with one exception for the 32bit x86 architecture which is
        handled as 'ix86' in general

        :return: architecture name

        :rtype: str
        """
        arch = PLATFORM_MACHINE
        if arch == 'i686' or arch == 'i586':
            arch = 'ix86'
        return arch

    @staticmethod
    def set_platform_name(name: str):
        """
        Sets the platform architecture once

        :param str name: an architecture name
        """
        global PLATFORM_MACHINE
        PLATFORM_MACHINE = name

    @staticmethod
    def is_x86_arch(arch):
        """
        Checks if machine architecture is x86 based

        Any arch that matches 32bit and 64bit x86 architecture
        causes the method to return True. Anything else will
        cause the method to return False

        :rtype: bool
        """
        x86_arch_names = [
            'x86_64', 'i686', 'i586', 'ix86'
        ]
        if arch in x86_arch_names:
            return True
        return False

    @staticmethod
    def is_ppc64_arch(arch):
        """
        Checks if machine architecture is ppc64 based

        Any arch that matches little endian or big endian ppc64 architecture
        causes the method to return True. Anything else will
        cause the method to return False

        :rtype: bool
        """
        ppc64_arch_names = [
            'ppc64', 'ppc64le'
        ]
        if arch in ppc64_arch_names:
            return True
        return False

    @staticmethod
    def is_buildservice_worker():
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

    @staticmethod
    def get_buildservice_env_name():
        """
        Provides the base name of the environment file in a
        buildservice worker

        :return: file basename

        :rtype: str
        """
        return '.buildenv'

    @staticmethod
    def get_obs_download_server_url():
        """
        Provides the default download server url hosting the public open
        buildservice repositories

        :return: url path

        :rtype: str
        """
        return 'http://download.opensuse.org/repositories'

    @staticmethod
    def get_obs_api_server_url():
        """
        Provides the default API server url to access the
        public open buildservice API

        :return: url path

        :rtype: str
        """
        return 'https://api.opensuse.org'

    @staticmethod
    def get_solvable_location():
        """
        Provides the directory to store SAT solvables for repositories.
        The solvable files are used to perform package
        dependency and metadata resolution

        :return: directory path

        :rtype: str
        """
        return '/var/tmp/kiwi/satsolver'

    @staticmethod
    def set_runtime_checker_metadata(filename):
        """
        Sets the runtime checker metadata filename

        :param str filename: a file path name
        """
        global RUNTIME_CHECKER_METADATA
        RUNTIME_CHECKER_METADATA = filename

    @staticmethod
    def set_shared_cache_location(location):
        """
        Sets the shared cache location once

        :param str location: a location path
        """
        global SHARED_CACHE_DIR
        SHARED_CACHE_DIR = location

    @staticmethod
    def set_custom_runtime_config_file(filename):
        """
        Sets the runtime config file once

        :param str filename: a file path name
        """
        global CUSTOM_RUNTIME_CONFIG_FILE
        CUSTOM_RUNTIME_CONFIG_FILE = filename

    @staticmethod
    def set_temp_location(location):
        """
        Sets the temp directory location once

        :param str location: a location path
        """
        global TEMP_DIR
        TEMP_DIR = location

    @staticmethod
    def get_shared_cache_location():
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
        return os.path.abspath(os.path.normpath(
            SHARED_CACHE_DIR
        )).lstrip(os.sep)

    @staticmethod
    def get_temp_location():
        """
        Provides the base temp directory location

        This is the directory used to store any temporary files
        and directories created by kiwi during runtime

        :return: directory path

        :rtype: str
        """
        return os.path.abspath(
            os.path.normpath(TEMP_DIR)
        )

    @staticmethod
    def get_sync_options():
        """
        Provides list of default data sync options

        :return: list of rsync options

        :rtype: list
        """
        return [
            '--archive', '--hard-links', '--xattrs', '--acls',
            '--one-file-system', '--inplace'
        ]

    @staticmethod
    def get_removed_files_name():
        """
        Provides base file name to store removed files
        in a delta root build
        """
        return 'removed'

    @staticmethod
    def get_system_files_name():
        """
        Provides base file name to store system files
        in a container build
        """
        return 'systemfiles'

    @staticmethod
    def get_exclude_list_for_removed_files_detection() -> List[str]:
        """
        Provides list of files/dirs to exclude from the removed
        files detection in a delta root build
        """
        return [
            'etc/hosts.kiwi',
            'etc/hosts.sha',
            'etc/resolv.conf.kiwi',
            'etc/resolv.conf.sha',
            'etc/sysconfig/proxy.kiwi',
            'etc/sysconfig/proxy.sha',
            'usr/lib/sysimage/rpm'
        ]

    @staticmethod
    def get_exclude_list_for_root_data_sync(no_tmpdirs: bool = True):
        """
        Provides the list of files or folders that are created
        by KIWI for its own purposes. Those files should be not
        be included in the resulting image.

        :return: list of file and directory names

        :rtype: list
        """
        exclude_list = [
            'image', '.kconfig'
        ]
        if no_tmpdirs:
            exclude_list += ['run/*', 'tmp/*']
        exclude_list += [
            Defaults.get_buildservice_env_name(),
            Defaults.get_shared_cache_location()
        ]
        return exclude_list

    @staticmethod
    def get_runtime_checker_metadata() -> Dict:
        with open(RUNTIME_CHECKER_METADATA) as meta:
            return yaml.safe_load(meta)

    @staticmethod
    def get_exclude_list_from_custom_exclude_files(root_dir: str) -> List:
        """
        Provides the list of folders that are excluded by the
        optional metadata file image/exclude_files.yaml

        :return: list of file and directory names

        :param string root_dir: image root directory

        :rtype: list
        """
        exclude_file = os.sep.join(
            [root_dir, 'image', 'exclude_files.yaml']
        )
        exclude_list = []
        if os.path.isfile(exclude_file):
            with open(exclude_file) as exclude:
                exclude_dict = yaml.safe_load(exclude)
                exclude_data = exclude_dict.get('exclude')
                if exclude_data and isinstance(exclude_data, list):
                    for exclude_file in exclude_data:
                        exclude_list.append(
                            exclude_file.lstrip(os.sep)
                        )
                else:
                    log.warning(
                        f'invalid yaml structure in {exclude_file}, ignored'
                    )
        return exclude_list

    @staticmethod
    def get_exclude_list_for_non_physical_devices():
        """
        Provides the list of folders that are not associated
        with a physical device. KIWI returns the basename of
        the folders typically used as mountpoint for those
        devices.

        :return: list of file and directory names

        :rtype: list
        """
        exclude_list = [
            'proc', 'sys', 'dev'
        ]
        return exclude_list

    @staticmethod
    def get_failsafe_kernel_options():
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

    @staticmethod
    def get_video_mode_map():
        """
        Provides video mode map

        Assign a tuple to each kernel vesa hex id for each of the
        supported bootloaders

        :return:
            video type map

            .. code:: python

                {'kernel_hex_mode': video_type(grub2='mode')}

        :rtype: dict
        """
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
            'auto': video_type(grub2='auto')
        }

    @staticmethod
    def get_volume_id():
        """
        Provides default value for ISO volume ID

        :return: name

        :rtype: str
        """
        return 'CDROM'

    @staticmethod
    def get_install_volume_id():
        """
        Provides default value for ISO volume ID for install media

        :return: name

        :rtype: str
        """
        return 'INSTALL'

    @staticmethod
    def get_snapper_config_template_file(root: str) -> str:
        """
        Provides the default configuration template file for snapper.
        The location in etc/ are preferred over files in usr/

        :return: file path

        :rtype: str
        """
        snapper_templates = [
            'etc/snapper/config-templates/default',
            'usr/share/snapper/config-templates/default'
        ]
        snapper_default_conf = ''
        for snapper_template in snapper_templates:
            template_config = os.path.join(root, snapper_template)
            if os.path.exists(template_config):
                snapper_default_conf = template_config
                break
        return snapper_default_conf

    @staticmethod
    def get_default_video_mode():
        """
        Uses auto mode for default video. See get_video_mode_map
        for details on the value depending which bootloader is
        used

        :return: auto

        :rtype: str
        """
        return 'auto'

    @staticmethod
    def get_default_bootloader():
        """
        Return default bootloader name which is grub2

        :return: bootloader name

        :rtype: str
        """
        return 'grub2'

    @staticmethod
    def get_grub_custom_arguments(root_dir: str) -> Dict[str, str]:
        return {
            'grub_directory_name':
                Defaults.get_grub_boot_directory_name(root_dir),
            'grub_load_command':
                'configfile'
        }

    @staticmethod
    def get_grub_boot_directory_name(lookup_path):
        """
        Provides grub2 data directory name in boot/ directory

        Depending on the distribution the grub2 boot path could be
        either boot/grub2 or boot/grub. The method will decide for
        the correct base directory name according to the name pattern
        of the installed grub2 tools

        :return: directory basename

        :rtype: str
        """
        if Path.which(filename='grub2-install', root_dir=lookup_path):
            # the presence of grub2-install is an indicator to put all
            # grub2 data below boot/grub2
            return 'grub2'
        else:
            # in any other case the assumption is made that all grub
            # boot data should live below boot/grub
            return 'grub'

    @staticmethod
    def get_grub_basic_modules(multiboot):
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
            'squash4',
            'lvm',
            'luks',
            'gcry_rijndael',
            'gcry_sha256',
            'gcry_sha512',
            'crypto',
            'cryptodisk',
            'test',
            'true',
            'loadenv'
        ]
        if multiboot:
            modules.append('multiboot')
        return modules

    @staticmethod
    def get_grub_efi_modules(multiboot=False):
        """
        Provides list of grub efi modules

        :param bool multiboot: grub multiboot mode

        :return: list of module names

        :rtype: list
        """
        host_architecture = Defaults.get_platform_name()
        modules = Defaults.get_grub_basic_modules(multiboot) + [
            'part_gpt',
            'part_msdos',
            'efi_gop'
        ]
        if host_architecture == 'x86_64':
            modules += [
                'efi_uga'
            ]
        return modules

    @staticmethod
    def get_grub_bios_modules(multiboot=False):
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

    @staticmethod
    def get_grub_ofw_modules():
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

    @staticmethod
    def get_grub_s390_modules():
        """
        Provides list of grub ofw modules (s390)

        :return: list of module names

        :rtype: list
        """
        modules = Defaults.get_grub_basic_modules(multiboot=False) + [
            'part_gpt',
            'part_msdos',
            'boot'
        ]
        return modules

    @staticmethod
    def get_grub_path(root_path, filename, raise_on_error=True):
        """
        Provides grub path to given search file

        Depending on the distribution grub could be installed below
        a grub2 or grub directory. grub could also reside in /usr/lib
        as well as in /usr/share. Therefore this information needs
        to be dynamically looked up

        :param string root_path: root path to start the lookup from
        :param string filename: filename to search
        :param bool raise_on_error: raise on not found, defaults to True

        The method returns the path to the given grub search file.
        By default it raises a KiwiBootLoaderGrubDataError exception
        if the file could not be found in any of the search locations.
        If raise_on_error is set to False and no file could be found
        the function returns None

        :return: filepath

        :rtype: str
        """
        log.debug(f'Searching grub file: {filename}')
        install_dirs = [
            'usr/share', 'usr/lib'
        ]
        lookup_list = []
        for grub_name in ['grub2', 'grub']:
            for install_dir in install_dirs:
                grub_path = os.path.join(
                    root_path, install_dir, grub_name, filename
                )
                log.debug(f'--> {grub_path}')
                if os.path.exists(grub_path):
                    log.debug(f'--> Found in: {grub_path}')
                    return grub_path
                lookup_list.append(grub_path)
        if raise_on_error:
            raise KiwiBootLoaderGrubDataError(
                'grub path {0} not found in {1}'.format(filename, lookup_list)
            )

    @staticmethod
    def get_preparer():
        """
        Provides ISO preparer name

        :return: name

        :rtype: str
        """
        return 'KIWI - https://github.com/OSInside/kiwi'

    @staticmethod
    def get_publisher():
        """
        Provides ISO publisher name

        :return: name

        :rtype: str
        """
        return 'SUSE LINUX GmbH'

    @staticmethod
    def get_shim_loader(root_path: str) -> Optional[shim_loader_type]:
        """
        Provides shim loader file path

        Searches distribution specific locations to find shim.efi
        below the given root path

        :param string root_path: image root path

        :return: shim_loader_type | None

        :rtype: NamedTuple
        """

        shim_pattern_type = namedtuple(
            'shim_pattern_type', ['pattern', 'binaryname']
        )

        shim_file_patterns = [
            shim_pattern_type('/usr/lib/shim/shim*.efi.signed.latest', 'shimx64.efi'),
            shim_pattern_type('/usr/lib/shim/shim*.efi.signed', 'shimx64.efi'),
            shim_pattern_type('/usr/lib/grub/*-efi-signed', 'shimx64.efi'),
            shim_pattern_type('/usr/share/efi/*/shim.efi', None),
            shim_pattern_type('/usr/lib64/efi/shim.efi', None),
            shim_pattern_type('/boot/efi/EFI/*/shim[a-z]*.efi', None),
            shim_pattern_type('/boot/efi/EFI/*/shim.efi', None),
            shim_pattern_type('/usr/lib/shim/shim*.efi', None)
        ]
        for shim_file_pattern in shim_file_patterns:
            for shim_file in sorted(glob.iglob(root_path + shim_file_pattern.pattern), key=len):
                if not shim_file_pattern.binaryname:
                    binaryname = os.path.basename(shim_file)
                else:
                    binaryname = shim_file_pattern.binaryname
                return shim_loader_type(
                    shim_file, binaryname
                )

        return None

    @staticmethod
    def get_mok_manager(root_path: str) -> Optional[str]:
        """
        Provides Mok Manager file path

        Searches distribution specific locations to find
        the Mok Manager EFI binary

        :param str root_path: image root path

        :return: file path or None

        :rtype: str
        """
        mok_manager_file_patterns = [
            '/usr/share/efi/*/MokManager.efi',
            '/usr/lib64/efi/MokManager.efi',
            '/boot/efi/EFI/*/mm*.efi',
            '/usr/lib/shim/mm*.efi'
        ]
        for mok_manager_file_pattern in mok_manager_file_patterns:
            for mm_file in glob.iglob(root_path + mok_manager_file_pattern):
                return mm_file
        return None

    @staticmethod
    def get_grub_efi_font_directory(root_path):
        """
        Provides distribution specific EFI font directory used with grub.

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        font_dir_patterns = [
            '/boot/efi/EFI/*/fonts'
        ]
        for font_dir_pattern in font_dir_patterns:
            for font_dir in glob.iglob(root_path + font_dir_pattern):
                return font_dir

    @staticmethod
    def get_unsigned_grub_loader(
        root_path: str, target_type: str = 'disk'
    ) -> Optional[str]:
        """
        Provides unsigned grub efi loader file path

        Searches distribution specific locations to find a distro
        grub EFI binary within the given root path

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        unsigned_grub_file = None
        unsigned_grub_file_patterns = {
            'disk': [
                '/usr/share/grub*/*-efi/grub.efi',
                '/usr/lib/grub*/*-efi/grub.efi',
                '/boot/efi/EFI/*/grubx64.efi',
                '/boot/efi/EFI/*/grubaa64.efi'
            ],
            'iso': [
                '/boot/efi/EFI/*/gcdx64.efi',
                '/usr/share/grub*/*-efi/grub.efi',
                '/usr/lib/grub*/*-efi/grub.efi',
                '/boot/efi/EFI/*/grubx64.efi',
                '/boot/efi/EFI/*/grubaa64.efi'
            ]
        }
        for unsigned_grub_file_pattern in unsigned_grub_file_patterns[target_type]:
            for unsigned_grub_file in glob.iglob(
                root_path + unsigned_grub_file_pattern
            ):
                return unsigned_grub_file
        return None

    @staticmethod
    def get_grub_bios_core_loader(root_path):
        """
        Provides grub bios image

        Searches distribution specific locations to find the
        core bios image below the given root path

        :param string root_path: image root path

        :return: file path or None

        :rtype: str
        """
        bios_grub_core_patterns = [
            '/usr/share/grub*/{0}/{1}'.format(
                Defaults.get_bios_module_directory_name(), Defaults.get_bios_image_name()
            ),
            '/usr/lib/grub*/{0}/{1}'.format(
                Defaults.get_bios_module_directory_name(), Defaults.get_bios_image_name()
            )
        ]
        for bios_grub_core_pattern in bios_grub_core_patterns:
            for bios_grub_core in glob.iglob(
                root_path + bios_grub_core_pattern
            ):
                return bios_grub_core

    @staticmethod
    def get_iso_grub_loader():
        """
        Return name of eltorito grub image used as ISO loader

        :return: file base name

        :rtype: str
        """
        return 'eltorito.img'

    @staticmethod
    def get_iso_grub_mbr():
        """
        Return name of hybrid MBR image used as ISO boot record

        :return: file base name

        :rtype: str
        """
        return 'boot_hybrid.img'

    @staticmethod
    def get_signed_grub_loader(
        root_path: str, target_type: str = 'disk'
    ) -> Optional[grub_loader_type]:
        """
        Provides shim signed grub loader file path

        Searches distribution specific locations to find a grub
        EFI binary within the given root path

        :param str root_path: image root path

        :return: grub_loader_type | None

        :rtype: NamedTuple
        """
        grub_pattern_type = namedtuple(
            'grub_pattern_type', ['pattern', 'binaryname']
        )
        signed_grub_file_patterns = {
            'disk': [
                grub_pattern_type(
                    '/usr/share/efi/*/grub.efi', None
                ),
                grub_pattern_type(
                    '/usr/lib64/efi/grub.efi', None
                ),
                grub_pattern_type(
                    '/boot/efi/EFI/*/grub*.efi', None
                ),
                grub_pattern_type(
                    '/usr/share/grub*/*-efi/grub.efi', None
                ),
                grub_pattern_type(
                    '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed',
                    'grubx64.efi'
                )
            ],
            'iso': [
                grub_pattern_type(
                    '/boot/efi/EFI/*/gcdx64.efi',
                    'grubx64.efi'
                ),
                grub_pattern_type(
                    '/boot/efi/EFI/*/gcdaa64.efi',
                    'grubaa64.efi'
                ),
                grub_pattern_type(
                    '/usr/share/efi/*/grub.efi', None
                ),
                grub_pattern_type(
                    '/usr/lib64/efi/grub.efi', None
                ),
                grub_pattern_type(
                    '/boot/efi/EFI/*/grub*.efi', None
                ),
                grub_pattern_type(
                    '/usr/share/grub*/*-efi/grub.efi', None
                ),
                grub_pattern_type(
                    '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed',
                    'grubx64.efi'
                )

            ]
        }
        for signed_grub in signed_grub_file_patterns[target_type]:
            for signed_grub_file in glob.iglob(root_path + signed_grub.pattern):
                if not signed_grub.binaryname:
                    binaryname = os.path.basename(signed_grub_file)
                else:
                    binaryname = signed_grub.binaryname
                return grub_loader_type(
                    signed_grub_file, binaryname
                )
        return None

    @staticmethod
    def get_efi_vendor_directory(efi_path):
        """
        Provides EFI vendor directory if present

        Looks up distribution specific EFI vendor directory

        :param string root_path: path to efi mountpoint

        :return: directory path or None

        :rtype: str
        """
        efi_vendor_directories = [
            'EFI/fedora',
            'EFI/redhat',
            'EFI/centos',
            'EFI/opensuse',
            'EFI/ubuntu',
            'EFI/debian'
        ]
        for efi_vendor_directory in efi_vendor_directories:
            efi_vendor_directory = os.sep.join([efi_path, efi_vendor_directory])
            if os.path.exists(efi_vendor_directory):
                return efi_vendor_directory

    @staticmethod
    def get_vendor_grubenv(efi_path):
        efi_vendor_directory = Defaults.get_efi_vendor_directory(efi_path)
        if efi_vendor_directory:
            grubenv = os.sep.join([efi_vendor_directory, 'grubenv'])
            if os.path.exists(grubenv):
                return grubenv

    @staticmethod
    def get_shim_vendor_directory(root_path):
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
            '/boot/efi/EFI/*/shim*.efi',
            '/EFI/*/shim*.efi'
        ]
        for shim_vendor_pattern in shim_vendor_patterns:
            for shim_file in glob.iglob(root_path + shim_vendor_pattern):
                return os.path.dirname(shim_file)

    @staticmethod
    def get_default_volume_group_name():
        """
        Provides default LVM volume group name

        :return: name

        :rtype: str
        """
        return 'systemVG'

    @staticmethod
    def get_min_partition_mbytes():
        """
        Provides default minimum partition size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 10

    @staticmethod
    def get_min_volume_mbytes(filesystem: str):
        """
        Provides default minimum LVM volume size in mbytes
        per filesystem

        :return: mbsize value

        :rtype: int
        """
        if filesystem == 'btrfs':
            return 120
        elif filesystem == 'xfs':
            return 300
        else:
            return 30

    @staticmethod
    def get_lvm_overhead_mbytes():
        """
        Provides empiric LVM overhead size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 80

    @staticmethod
    def get_default_boot_mbytes():
        """
        Provides default boot partition size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 300

    @staticmethod
    def get_default_efi_boot_mbytes():
        """
        Provides default EFI partition size in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 20

    @staticmethod
    def get_recovery_spare_mbytes():
        """
        Provides spare size of recovery partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 300

    @staticmethod
    def get_default_legacy_bios_mbytes():
        """
        Provides default size of bios_grub partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 2

    @staticmethod
    def get_default_prep_mbytes():
        """
        Provides default size of prep partition in mbytes

        :return: mbsize value

        :rtype: int
        """
        return 8

    @staticmethod
    def get_disk_format_types():
        """
        Provides supported disk format types

        :return: disk types

        :rtype: list
        """
        return [
            'gce', 'qcow2', 'vmdk', 'ova', 'vmx', 'vhd', 'vhdx',
            'vhdfixed', 'vdi', 'vagrant.libvirt.box', 'vagrant.virtualbox.box'
        ]

    @staticmethod
    def get_vagrant_config_virtualbox_guest_additions():
        """
        Provides the default value for
        ``vagrantconfig.virtualbox_guest_additions_present``

        :return: whether guest additions are expected to be present in the
            vagrant box

        :rtype: bool
        """
        return False

    @staticmethod
    def get_firmware_types():
        """
        Provides supported architecture specific firmware types

        :return: firmware types per architecture

        :rtype: dict
        """
        return {
            'x86_64': ['efi', 'uefi', 'bios', 'ec2'],
            'i586': ['bios'],
            'i686': ['bios'],
            'ix86': ['bios'],
            'aarch64': ['efi', 'uefi'],
            'arm64': ['efi', 'uefi'],
            'armv5el': ['efi', 'uefi'],
            'armv5tel': ['efi', 'uefi'],
            'armv6hl': ['efi', 'uefi'],
            'armv6l': ['efi', 'uefi'],
            'armv7hl': ['efi', 'uefi'],
            'armv7l': ['efi', 'uefi'],
            'armv8l': ['efi', 'uefi'],
            'ppc': ['ofw'],
            'ppc64': ['ofw', 'opal'],
            'ppc64le': ['ofw', 'opal'],
            'riscv64': ['efi', 'uefi'],
            's390': [],
            's390x': []
        }

    @staticmethod
    def get_default_firmware(arch):
        """
        Provides default firmware for specified architecture

        :param string arch: machine architecture name

        :return: firmware name

        :rtype: str
        """
        default_firmware = {
            'x86_64': 'bios',
            'i586': 'bios',
            'i686': 'bios',
            'ix86': 'bios',
            'ppc': 'ofw',
            'ppc64': 'ofw',
            'ppc64le': 'ofw',
            'arm64': 'efi',
            'aarch64': 'efi',
            'armv5el': 'efi',
            'armv5tel': 'efi',
            'armv6hl': 'efi',
            'armv6l': 'efi',
            'armv7hl': 'efi',
            'armv7l': 'efi',
            'armv8l': 'efi',
            'riscv64': 'efi'
        }
        if arch in default_firmware:
            return default_firmware[arch]

    @staticmethod
    def get_efi_capable_firmware_names():
        """
        Provides list of EFI capable firmware names. These are
        those for which kiwi supports the creation of an EFI
        bootable disk image

        :return: firmware names

        :rtype: list
        """
        return ['efi', 'uefi']

    @staticmethod
    def get_ec2_capable_firmware_names():
        """
        Provides list of EC2 capable firmware names. These are
        those for which kiwi supports the creation of disk images
        bootable within the Amazon EC2 public cloud

        :return: firmware names

        :rtype: list
        """
        return ['ec2']

    @staticmethod
    def get_efi_module_directory_name(arch):
        """
        Provides architecture specific EFI directory name which
        stores the EFI binaries for the desired architecture.

        :param string arch: machine architecture name

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
            'armv7l': 'arm-efi',
            'armv8l': 'arm-efi',
            'riscv64': 'riscv64-efi'
        }
        if arch in default_module_directory_names:
            return default_module_directory_names[arch]

    @staticmethod
    def get_bios_module_directory_name():
        """
        Provides BIOS directory name which stores the pc binaries

        :return: directory name

        :rtype: str
        """
        return 'powerpc-ieee1275' if Defaults.is_ppc64_arch(Defaults.get_platform_name()) else 'i386-pc'

    @staticmethod
    def get_efi_image_name(arch):
        """
        Provides architecture specific EFI boot binary name

        :param string arch: machine architecture name

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
            'armv7l': 'bootarm.efi',
            'armv8l': 'bootarm.efi',
            'riscv64': 'bootriscv64.efi'
        }
        if arch in default_efi_image_names:
            return default_efi_image_names[arch]

    @staticmethod
    def get_bios_image_name():
        """
        Provides bios core boot binary name

        :return: name

        :rtype: str
        """
        return 'grub.elf' if Defaults.is_ppc64_arch(Defaults.get_platform_name()) else 'core.img'

    @staticmethod
    def get_default_boot_timeout_seconds():
        """
        Provides default boot timeout in seconds

        :return: seconds

        :rtype: int
        """
        return 10

    @staticmethod
    def get_default_disk_start_sector():
        """
        Provides the default initial disk sector for the first disk
        partition.

        :return: sector value

        :rtype: int
        """
        return Defaults().defaults['kiwi_startsector']

    @staticmethod
    def get_default_efi_partition_table_type():
        """
        Provides the default partition table type for efi firmwares.

        :return: partition table type name

        :rtype: str
        """
        return 'gpt'

    @staticmethod
    def get_default_inode_size():
        """
        Provides default size of inodes in bytes. This is only
        relevant for inode based filesystems

        :return: bytesize value

        :rtype: int
        """
        return Defaults().defaults['kiwi_inode_size']

    @staticmethod
    def get_archive_image_types():
        """
        Provides list of supported archive image types

        :return: archive names

        :rtype: list
        """
        return ['tbz', 'cpio']

    @staticmethod
    def get_container_image_types():
        """
        Provides list of supported container image types

        :return: container names

        :rtype: list
        """
        return ['docker', 'oci', 'appx']

    @staticmethod
    def get_filesystem_image_types():
        """
        Provides list of supported filesystem image types

        :return: filesystem names

        :rtype: list
        """
        return [
            'ext2', 'ext3', 'ext4', 'btrfs', 'squashfs',
            'xfs', 'fat16', 'fat32', 'erofs'
        ]

    @staticmethod
    def get_default_live_iso_type():
        """
        Provides default live iso union type

        :return: live iso type

        :rtype: str
        """
        return 'overlay'

    @staticmethod
    def get_default_uri_type():
        """
        Provides default URI type

        Absolute path specifications used in the context of an URI
        will apply the specified default mime type

        :return: URI mime type

        :rtype: str
        """
        return 'dir:/'

    @staticmethod
    def get_dracut_conf_name():
        """
        Provides file path of dracut config file to be used with KIWI

        :return: file path name

        :rtype: str
        """
        return '/etc/dracut.conf.d/02-kiwi.conf'

    @staticmethod
    def get_live_dracut_modules_from_flag(flag_name):
        """
        Provides flag_name to dracut modules name map

        Depending on the value of the flag attribute in the KIWI image
        description specific dracut modules need to be selected

        :return: dracut module names as list

        :rtype: list
        """
        live_modules = {
            'overlay': ['kiwi-live'],
            'dmsquash': ['dmsquash-live', 'livenet']
        }
        if flag_name in live_modules:
            return live_modules[flag_name]
        else:
            return ['kiwi-live']

    @staticmethod
    def get_default_live_iso_root_filesystem():
        """
        Provides default live iso root filesystem type

        :return: filesystem name

        :rtype: str
        """
        return 'ext4'

    @staticmethod
    def get_live_iso_persistent_boot_options(persistent_filesystem=None):
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

    @staticmethod
    def get_disk_image_types():
        """
        Provides supported disk image types

        :return: disk image type names

        :rtype: list
        """
        return ['oem']

    @staticmethod
    def get_live_image_types():
        """
        Provides supported live image types

        :return: live image type names

        :rtype: list
        """
        return ['iso']

    @staticmethod
    def get_kis_image_types():
        """
        Provides supported kis image types

        :return: kis image type names

        :rtype: list
        """
        return ['kis', 'pxe']

    @staticmethod
    def get_enclaves_image_types():
        """
        Provides supported enclave(initrd-only) image types

        :return: enclave image type names

        :rtype: list
        """
        return ['enclave']

    @staticmethod
    def get_boot_image_description_path():
        """
        Provides the path to find custom kiwi boot descriptions

        :return: directory path

        :rtype: str
        """
        return '/usr/share/kiwi/custom_boot'

    @staticmethod
    def get_boot_image_strip_file():
        """
        Provides the file path to bootloader strip metadata.
        This file contains information about the files and directories
        automatically striped out from the kiwi initrd

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('config/strip.xml')

    @staticmethod
    def get_schema_file():
        """
        Provides file path to kiwi RelaxNG schema

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('schema/kiwi.rng')

    @staticmethod
    def get_common_functions_file():
        """
        Provides the file path to config functions metadata.

        This file contains bash functions used for system
        configuration or in the boot code from the kiwi initrd

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('config/functions.sh')

    @staticmethod
    def get_xsl_stylesheet_file():
        """
        Provides the file path to the KIWI XSLT style sheets

        :return: file path

        :rtype: str
        """
        return Defaults.project_file('xsl/master.xsl')

    @staticmethod
    def get_schematron_module_name():
        """
        Provides module name for XML SchemaTron validations

        :return: python module name

        :rtype: str
        """
        return 'lxml.isoschematron'

    @staticmethod
    def project_file(filename):
        """
        Provides the python module base directory search path

        The method uses the importlib.resources.path method to identify
        files and directories from the application

        :param string filename: relative project file

        :return: absolute file path name

        :rtype: str
        """
        with as_file(importlib.resources.files('kiwi')) as path:
            return f'{path}/{filename}'

    @staticmethod
    def get_imported_root_image(root_dir):
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

    @staticmethod
    def get_iso_boot_path():
        """
        Provides arch specific relative path to boot files
        on kiwi iso filesystems

        :return: relative path name

        :rtype: str
        """
        return os.sep.join(
            ['boot', Defaults.get_platform_name()]
        )

    @staticmethod
    def get_iso_tool_category():
        """
        Provides default iso tool category

        :return: name

        :rtype: str
        """
        return 'xorriso'

    @staticmethod
    def get_iso_media_tag_tool():
        """
        Provides default iso media tag tool

        :return: name

        :rtype: str
        """
        return 'checkmedia'

    @staticmethod
    def get_container_compression():
        """
        Provides default container compression

        :return: True

        :rtype: bool
        """
        return True

    @staticmethod
    def get_default_container_name():
        """
        Provides the default container name.

        :return: name

        :rtype: str
        """
        return 'kiwi-container'

    @staticmethod
    def get_container_base_image_tag():
        """
        Provides the tag used to identify base layers during the build
        of derived images.

        :return: tag

        :rtype: str
        """
        return 'base_layer'

    @staticmethod
    def get_oci_archive_tool():
        """
        Provides the default OCI archive tool name.

        :return: name

        :rtype: str
        """
        return 'umoci'

    @staticmethod
    def get_part_mapper_tool():
        """
        Provides the default partition mapper tool name.

        :return: name

        :rtype: str
        """
        host_architecture = Defaults.get_platform_name()
        if 's390' in host_architecture:
            return 'kpartx'
        return 'partx'

    @staticmethod
    def get_default_container_tag():
        """
        Provides the default container tag.

        :return: tag

        :rtype: str
        """
        return 'latest'

    @staticmethod
    def get_default_container_subcommand():
        """
        Provides the default container subcommand.

        :return: command as a list of arguments

        :rtype: list
        """
        return ['/bin/bash']

    @staticmethod
    def get_default_container_created_by():
        """
        Provides the default 'created by' history entry for containers.

        :return: the specific kiwi version used for the build

        :rtype: str
        """
        return 'KIWI {0}'.format(__version__)

    @staticmethod
    def get_custom_rpm_macros_path():
        """
        Returns the custom macros directory for the rpm database.

        :return: path name

        :rtype: str
        """
        return 'usr/lib/rpm/macros.d'

    @staticmethod
    def get_custom_rpm_bootstrap_macro_name():
        """
        Returns the rpm bootstrap macro file name created
        in the custom rpm macros path

        :return: filename

        :rtype: str
        """
        return 'macros.kiwi-bootstrap-config'

    @staticmethod
    def get_custom_rpm_image_macro_name():
        """
        Returns the rpm image macro file name created
        in the custom rpm macros path

        :return: filename

        :rtype: str
        """
        return 'macros.kiwi-image-config'

    @staticmethod
    def get_default_package_manager() -> str:
        """
        Returns the default package manager name if none
        is configured in the image description

        :return: package manager name

        :rtype: str
        """
        return 'dnf4'

    @staticmethod
    def get_default_packager_tool(package_manager):
        """
        Provides the packager tool according to the package manager

        :param string package_manager: package manger name

        :return: packager tool binary name

        :rtype: str
        """
        rpm_based = ['zypper', 'dnf4', 'dnf5', 'microdnf']
        deb_based = ['apt']
        if package_manager in rpm_based:
            return 'rpm'
        elif package_manager in deb_based:
            return 'dpkg'
        elif package_manager == 'pacman':
            return 'pacman'

    @staticmethod
    def get_discoverable_partition_ids() -> Dict[str, str]:
        """
        Provides arch specific partition UUIDs as defined
        by the UAPI group

        :return: partition UUIDs

        :rtype: dict
        """
        arch = Defaults.get_platform_name()
        part_uuids_archs = {
            'x86_64': {
                'root':
                    '4f68bce3e8cd4db196e7fbcaf984b709',
                'usr':
                    '8484680c952148c69c11b0720656f69e',
                'usr-verity':
                    '77ff5f63e7b64633acf41565b864c0e6'
            },
            'ix86': {
                'root':
                    '44479540f29741b29af7d131d5f0458a',
                'usr':
                    '75250d768cc6458ebd66bd47cc81a812',
                'usr-verity':
                    '8f461b0d14ee4e819aa9049b6fb97abd'
            },
            'aarch64': {
                'root':
                    'b921b0451df041c3af444c6f280d3fae',
                'usr':
                    'b0e01050ee5f4390949a9101b17104e9',
                'usr-verity':
                    '6e11a4e7fbca4dedb9e9e1a512bb664e'
            },
            'riscv64': {
                'root':
                    '72ec70a6cf7440e6bd494bda08e8f224',
                'usr':
                    'beaec34b8442439ba40b984381ed097d',
                'usr-verity':
                    '8f1056be9b0547c481d6be53128e5b54'
            }
        }
        part_uuids_arch = part_uuids_archs.get(arch) or {}
        return {
            'root':
                part_uuids_arch.get('root') or '',
            'usr':
                part_uuids_arch.get('usr') or '',
            'usr-verity':
                part_uuids_arch.get('usr-verity') or '',
            'usr-secondary':
                '75250d768cc6458ebd66bd47cc81a812',
            'usr-secondary-verity':
                '8f461b0d14ee4e819aa9049b6fb97abd',
            'esp':
                'c12a7328f81f11d2ba4b00a0c93ec93b',
            'xbootldr':
                'bc13c2ff59e64262a352b275fd6f7172',
            'swap':
                '0657fd6da4ab43c484e50933c84b4f4f',
            'home':
                '933ac7e12eb44f13b8440e14e2aef915',
            'srv':
                '3b8f842520e04f3b907f1a25a76f98e8',
            'var':
                '4d21b016b53445c2a9fb5c16e091fd2d',
            'tmp':
                '7ec6f5573bc54acab29316ef5df639d1',
            'user-home':
                '773f91ef66d449b5bd83d683bf40ad16',
            'linux-generic':
                '0fc63daf848347728e793d69d8477de4'
        }

    @staticmethod
    def get_bls_loader_entries_dir() -> str:
        """
        Provide default loader entries directory for BLS loaders

        :return: directory name

        :rtype: str
        """
        return '/boot/loader/entries'

    def get(self, key):
        """
        Implements get method for profile elements

        :param string key: profile keyname

        :return: key value

        :rtype: str
        """
        if key in self.defaults:
            return self.defaults[key]

    @staticmethod
    def get_profile_file(root_dir):
        """
        Return name of profile file for given root directory
        """
        return root_dir + '/.profile'

    def to_profile(self, profile):
        """
        Implements method to add list of profile keys and their values
        to the specified instance of a Profile class

        :param object profile: Profile instance
        """
        for key in sorted(self.profile_key_list):
            # Do not apply default values to any variable that was
            # already defined in the profile instance.
            cur_profile = profile.dot_profile
            if key not in cur_profile or cur_profile[key] is None:
                profile.add(key, self.get(key))
