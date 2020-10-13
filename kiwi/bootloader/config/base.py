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
import re
import logging
from collections import namedtuple

# project
from kiwi.mount_manager import MountManager
from kiwi.storage.setup import DiskSetup
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiBootLoaderTargetError
)

log = logging.getLogger('kiwi')


class BootLoaderConfigBase:
    """
    **Base class for bootloader configuration**

    :param object xml_state: instance of :class:`XMLState`
    :param string root_dir: root directory path name
    :param dict custom_args: custom bootloader arguments dictionary
    """
    def __init__(self, xml_state, root_dir, boot_dir=None, custom_args=None):
        self.root_dir = root_dir
        self.boot_dir = boot_dir or root_dir
        self.xml_state = xml_state
        self.arch = Defaults.get_platform_name()

        self.volumes_mount = []
        self.root_mount = None
        self.boot_mount = None
        self.efi_mount = None
        self.device_mount = None
        self.proc_mount = None
        self.tmp_mount = None

        self.root_filesystem_is_overlay = xml_state.build_type.get_overlayroot()
        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom arguments by default

        :param dict custom_args: custom bootloader arguments
        """
        self.custom_args = custom_args

    def write(self):
        """
        Write config data to config file.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def write_meta_data(self, root_uuid=None, boot_options=''):
        """
        Write bootloader setup meta data files

        :param string root_uuid: root device UUID
        :param string boot_options: kernel options as string

        Implementation in specialized bootloader class optional
        """
        pass

    def setup_disk_image_config(
        self, boot_uuid, root_uuid, hypervisor, kernel, initrd, boot_options={}
    ):
        """
        Create boot config file to boot from disk.

        :param string boot_uuid: boot device UUID
        :param string root_uuid: root device UUID
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        :param dict boot_options:
            custom options dictionary required to setup the bootloader.
            The scope of the options covers all information needed
            to setup and configure the bootloader and gets effective
            in the individual implementation. boot_options should
            not be mixed up with commandline options used at boot time.
            This information is provided from the get_*_cmdline
            methods. The contents of the dictionary can vary between
            bootloaders or even not be needed

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_install_image_config(
        self, mbrid, hypervisor, kernel, initrd
    ):
        """
        Create boot config file to boot from install media in EFI mode.

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_live_image_config(
        self, mbrid, hypervisor, kernel, initrd
    ):
        """
        Create boot config file to boot live ISO image in EFI mode.

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
        Create bootloader images for disk boot

        Some bootloaders requires to build a boot image the bootloader
        can load from a specific offset address or from a standardized
        path on a filesystem.

        :param string boot_uuid: boot device UUID
        :param string lookup_path: custom module lookup path

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        """
        Create bootloader images for ISO boot an install media

        :param string mbrid: mbrid file name on boot device
        :param string lookup_path: custom module lookup path

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Create bootloader images for ISO boot a live ISO image

        :param string mbrid: mbrid file name on boot device
        :param string lookup_path: custom module lookup path

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_sysconfig_bootloader(self):
        """
        Create or update etc/sysconfig/bootloader by parameters
        required according to the bootloader setup

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def create_efi_path(self, in_sub_dir='boot/efi'):
        """
        Create standard EFI boot directory structure

        :param string in_sub_dir: toplevel directory

        :return: Full qualified EFI boot path

        :rtype: str
        """
        efi_boot_path = os.path.normpath(
            os.sep.join([self.boot_dir, in_sub_dir, 'EFI/BOOT'])
        )
        Path.create(efi_boot_path)
        return efi_boot_path

    def get_boot_theme(self):
        """
        Bootloader Theme name

        :return: theme name

        :rtype: str
        """
        theme = None
        for preferences in self.xml_state.get_preferences_sections():
            section_content = preferences.get_bootloader_theme()
            if section_content:
                theme = section_content[0]
        return theme

    def get_boot_timeout_seconds(self):
        """
        Bootloader timeout in seconds

        If no timeout is specified the default timeout applies

        :return: timeout seconds

        :rtype: int
        """
        timeout_seconds = self.xml_state.get_build_type_bootloader_timeout()
        if timeout_seconds is None:
            timeout_seconds = Defaults.get_default_boot_timeout_seconds()
        return timeout_seconds

    def get_continue_on_timeout(self):
        """
        Check if the boot should continue after boot timeout or not

        :return: True or False

        :rtype: bool
        """
        continue_on_timeout = \
            self.xml_state.build_type.get_install_continue_on_timeout()
        if continue_on_timeout is None:
            continue_on_timeout = True
        return continue_on_timeout

    def failsafe_boot_entry_requested(self):
        """
        Check if a failsafe boot entry is requested

        :return: True or False

        :rtype: bool
        """
        if self.xml_state.build_type.get_installprovidefailsafe() is False:
            return False
        return True

    def get_boot_cmdline(self, uuid=None):
        """
        Boot commandline arguments passed to the kernel

        :param string uuid: boot device UUID

        :return: kernel boot arguments

        :rtype: str
        """
        cmdline = ''
        custom_cmdline = self.xml_state.build_type.get_kernelcmdline()
        if custom_cmdline:
            cmdline += ' ' + custom_cmdline
        custom_root = self._get_root_cmdline_parameter(uuid)
        if custom_root and custom_root not in cmdline:
            cmdline += ' ' + custom_root
        return cmdline.strip()

    def get_install_image_boot_default(self, loader=None):
        """
        Provide the default boot menu entry identifier for install images

        The install image can be configured to provide more than
        one boot menu entry. Menu entries configured are:

        * [0] Boot From Hard Disk
        * [1] Install
        * [2] Failsafe Install

        The installboot attribute controlls which of these are used
        by default. If not specified the boot from hard disk entry
        will be the default. Depending on the specified loader type
        either an entry number or name will be returned.

        :param string loader: bootloader name

        :return: menu name or id

        :rtype: str
        """
        menu_entry_title = self.get_menu_entry_title(plain=True)
        menu_type = namedtuple(
            'menu_type', ['name', 'menu_id']
        )
        menu_list = [
            menu_type(
                name='Boot_from_Hard_Disk', menu_id='0'
            ),
            menu_type(
                name='Install_' + menu_entry_title, menu_id='1'
            ),
            menu_type(
                name='Failsafe_--_Install_' + menu_entry_title, menu_id='2'
            )
        ]
        boot_id = 0
        install_boot_name = self.xml_state.build_type.get_installboot()
        if install_boot_name == 'failsafe-install':
            boot_id = 2
        elif install_boot_name == 'install':
            boot_id = 1

        if not self.failsafe_boot_entry_requested() and boot_id == 2:
            log.warning(
                'Failsafe install requested but failsafe menu entry is disabled'
            )
            log.warning('Switching to standard install')
            boot_id = 1

        if loader and loader == 'isolinux':
            return menu_list[boot_id].name
        else:
            return menu_list[boot_id].menu_id

    def get_boot_path(self, target='disk'):
        """
        Bootloader lookup path on boot device

        If the bootloader reads the data it needs to boot, it does
        that from the configured boot device. Depending if that
        device is an extra boot partition or the root partition or
        or based on a non standard filesystem like a btrfs snapshot,
        the path name varies

        :param string target: target name: disk|iso

        :return: path name

        :rtype: str
        """
        if target != 'disk' and target != 'iso':
            raise KiwiBootLoaderTargetError(
                'Invalid boot loader target %s' % target
            )
        bootpath = '/boot'
        need_boot_partition = False
        if target == 'disk':
            disk_setup = DiskSetup(self.xml_state, self.boot_dir)
            need_boot_partition = disk_setup.need_boot_partition()
            if need_boot_partition:
                # if an extra boot partition is used we will find the
                # data directly in the root of this partition and not
                # below the boot/ directory
                bootpath = '/'

        if target == 'disk':
            if not need_boot_partition:
                filesystem = self.xml_state.build_type.get_filesystem()
                volumes = self.xml_state.get_volumes()
                if filesystem == 'btrfs' and volumes:
                    # grub boot data paths must not be in a subvolume
                    # otherwise grub won't be able to find its config file
                    grub2_boot_data_paths = ['boot', 'boot/grub', 'boot/grub2']
                    for volume in volumes:
                        if volume.name in grub2_boot_data_paths:
                            raise KiwiBootLoaderTargetError(
                                '{0} must not be a subvolume'.format(
                                    volume.name
                                )
                            )

        if target == 'iso':
            bootpath = '/boot/' + self.arch + '/loader'

        return bootpath

    def quote_title(self, name):
        """
        Quote special characters in the title name

        Not all characters can be displayed correctly in the bootloader
        environment. Therefore a quoting is required

        :param string name: title name

        :return: quoted text

        :rtype: str
        """
        name = name.replace(' ', '_')
        name = name.replace('[', '(')
        name = name.replace(']', ')')
        return name

    def get_menu_entry_title(self, plain=False):
        """
        Prefixed menu entry title

        If no displayname is specified in the image description,
        the menu title is constructed from the image name and
        build type

        :param bool plain: indicate to add built type into title text

        :return: title text

        :rtype: str
        """
        title = self.xml_state.xml_data.get_displayname()
        if not title:
            title = self.xml_state.xml_data.get_name()
        else:
            # if the title is set via the displayname attribute no custom
            # kiwi prefix or other style changes to that text should
            # be made
            plain = True
        type_name = self.xml_state.build_type.get_image()
        if plain:
            return title
        return title + ' [ ' + type_name.upper() + ' ]'

    def get_menu_entry_install_title(self):
        """
        Prefixed menu entry title for install images

        If no displayname is specified in the image description,
        the menu title is constructed from the image name

        :return: title text

        :rtype: str
        """
        title = self.xml_state.xml_data.get_displayname()
        if not title:
            title = self.xml_state.xml_data.get_name()
        return title

    def get_gfxmode(self, target):
        """
        Graphics mode according to bootloader target

        Bootloaders which support a graphics mode can be configured
        to run graphics in a specific resolution and colors. There
        is no standard for this setup which causes kiwi to create
        a mapping from the kernel vesa mode number to the corresponding
        bootloader graphics mode setup

        :param string target: bootloader name

        :return: boot graphics mode

        :rtype: str
        """
        gfxmode_map = Defaults.get_video_mode_map()

        default_mode = Defaults.get_default_video_mode()
        requested_gfxmode = self.xml_state.build_type.get_vga()

        if requested_gfxmode in gfxmode_map:
            gfxmode = requested_gfxmode
        else:
            gfxmode = default_mode

        if target == 'grub2':
            return gfxmode_map[gfxmode].grub2
        elif target == 'isolinux':
            return gfxmode_map[gfxmode].isolinux
        else:
            return gfxmode

    def _mount_system(
        self, root_device, boot_device, efi_device=None, volumes=None
    ):
        self.root_mount = MountManager(
            device=root_device
        )
        if 's390' in self.arch:
            self.boot_mount = MountManager(
                device=boot_device,
                mountpoint=self.root_mount.mountpoint + '/boot/zipl'
            )
        else:
            self.boot_mount = MountManager(
                device=boot_device,
                mountpoint=self.root_mount.mountpoint + '/boot'
            )
        if efi_device:
            self.efi_mount = MountManager(
                device=efi_device,
                mountpoint=self.root_mount.mountpoint + '/boot/efi'
            )

        self.root_mount.mount()

        if not self.root_mount.device == self.boot_mount.device:
            self.boot_mount.mount()

        if efi_device:
            self.efi_mount.mount()

        if volumes:
            for volume_path in Path.sort_by_hierarchy(
                sorted(volumes.keys())
            ):
                volume_mount = MountManager(
                    device=volumes[volume_path]['volume_device'],
                    mountpoint=self.root_mount.mountpoint + '/' + volume_path
                )
                self.volumes_mount.append(volume_mount)
                volume_mount.mount(
                    options=[volumes[volume_path]['volume_options']]
                )

        if self.root_filesystem_is_overlay:
            # In case of an overlay root system all parts of the rootfs
            # are read-only by squashfs except for the extra boot partition.
            # However tools like grub's mkconfig creates temporary files
            # at call time and therefore /tmp needs to be writable during
            # the call time of the tools
            self.tmp_mount = MountManager(
                device='/tmp',
                mountpoint=self.root_mount.mountpoint + '/tmp'
            )
            self.tmp_mount.bind_mount()

        self.device_mount = MountManager(
            device='/dev',
            mountpoint=self.root_mount.mountpoint + '/dev'
        )
        self.proc_mount = MountManager(
            device='/proc',
            mountpoint=self.root_mount.mountpoint + '/proc'
        )
        self.device_mount.bind_mount()
        self.proc_mount.bind_mount()

    def _get_root_cmdline_parameter(self, uuid):
        cmdline = self.xml_state.build_type.get_kernelcmdline()
        if cmdline and 'root=' in cmdline:
            log.info(
                'Kernel root device explicitly set via kernelcmdline'
            )
            root_search = re.search(r'(root=(.*)[ ]+|root=(.*)$)', cmdline)
            if root_search:
                return root_search.group(1)

        if uuid and self.xml_state.build_type.get_overlayroot():
            return 'root=overlay:UUID={0}'.format(uuid)
        elif uuid:
            return 'root=UUID={0} rw'.format(uuid)
        else:
            log.warning(
                'root=UUID=<uuid> setup requested, but uuid is not provided'
            )

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        for volume_mount in reversed(self.volumes_mount):
            volume_mount.umount()
        if self.device_mount:
            self.device_mount.umount()
        if self.proc_mount:
            self.proc_mount.umount()
        if self.efi_mount:
            self.efi_mount.umount()
        if self.tmp_mount:
            self.tmp_mount.umount()
        if self.boot_mount:
            self.boot_mount.umount()
        if self.root_mount:
            self.root_mount.umount()
