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

# project
from ...logger import log
from ...storage.setup import DiskSetup
from ...path import Path
from ...defaults import Defaults

from ...exceptions import (
    KiwiBootLoaderTargetError
)


class BootLoaderConfigBase(object):
    """
    Base class for bootloader configuration

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`xml_state`
        Instance of XMLState of the system image description

    * :attr:`custom_args`
        List of custom bootloader arguments
    """
    def __init__(self, xml_state, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.xml_state = xml_state

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom arguments by default

        :param list custom_args: custom bootloader arguments
        """
        self.custom_args = custom_args

    def write(self):
        """
        Write config data to config file.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_disk_image_config(
        self, uuid, hypervisor, kernel, initrd
    ):
        """
        Create boot config file to boot from disk.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_install_image_config(
        self, mbrid, hypervisor, kernel, initrd
    ):
        """
        Create boot config file to boot from install media in EFI mode.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_live_image_config(
        self, mbrid, hypervisor, kernel, initrd
    ):
        """
        Create boot config file to boot live ISO image in EFI mode.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
        Create bootloader images for disk boot

        Some bootloaders requires to build a boot image the bootloader
        can load from a specific offset address or from a standardized
        path on a filesystem.

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        """
        Create bootloader images for ISO boot an install media

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Create bootloader images for ISO boot a live ISO image

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def create_efi_path(self, in_sub_dir='boot/efi'):
        """
        Create standard EFI boot directory structure

        :param string in_sub_dir: toplevel directory

        :return: Full qualified EFI boot path
        :rtype: string
        """
        efi_boot_path = self.root_dir + '/' + in_sub_dir + '/EFI/BOOT'
        Path.create(efi_boot_path)
        return efi_boot_path

    def get_boot_theme(self):
        """
        Bootloader Theme name

        :return: theme name
        :rtype: string
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
        timeout_seconds = self.xml_state.build_type.get_boottimeout()
        if not timeout_seconds:
            timeout_seconds = Defaults.get_default_boot_timeout_seconds()
        return timeout_seconds

    def failsafe_boot_entry_requested(self):
        """
        Check if a failsafe boot entry is requested

        :rtype: bool
        """
        if self.xml_state.build_type.get_installprovidefailsafe() is False:
            return False
        return True

    def get_hypervisor_domain(self):
        """
        Hypervisor domain name

        :return: domain name
        :rtype: string
        """
        machine = self.xml_state.get_build_type_machine_section()
        if machine:
            return machine.get_domain()

    def get_boot_cmdline(self, uuid=None):
        """
        Boot commandline arguments passed to the kernel

        :return: kernel boot arguments
        :rtype: string
        """
        cmdline = ''
        custom_cmdline = self.xml_state.build_type.get_kernelcmdline()
        if custom_cmdline:
            cmdline += ' ' + custom_cmdline
        custom_root = self._get_root_cmdline_parameter(uuid)
        if custom_root:
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

        :return: menu name or id
        :rtype: string
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

        :return: path name
        :rtype: string
        """
        if target != 'disk' and target != 'iso':
            raise KiwiBootLoaderTargetError(
                'Invalid boot loader target %s' % target
            )
        bootpath = '/boot'
        need_boot_partition = False
        if target == 'disk':
            disk_setup = DiskSetup(self.xml_state, self.root_dir)
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
                    root_is_snapshot = \
                        self.xml_state.build_type.get_btrfs_root_is_snapshot()
                    boot_is_on_volume = False
                    for volume in volumes:
                        if volume.name == 'boot' or volume.name == 'boot/grub2':
                            boot_is_on_volume = True
                            break
                    # if we directly boot a btrfs filesystem with a subvolume
                    # setup and no extra boot partition we have to care for
                    # the layout of the system which places all volumes below
                    # a topleve volume or snapshot
                    if not boot_is_on_volume and root_is_snapshot:
                        bootpath = '/@/.snapshots/1/snapshot' + bootpath
                    else:
                        bootpath = '/@' + bootpath

        return bootpath

    def quote_title(self, name):
        """
        Quote special characters in the title name

        Not all characters can be displayed correctly in the bootloader
        environment. Therefore a quoting is required

        :return: quoted text
        :rtype: string
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

        :return: title text
        :rtype: string
        """
        title = self.xml_state.xml_data.get_displayname()
        if not title:
            title = self.xml_state.xml_data.get_name()
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
        :rtype: string
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
        :rtype: string
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

    def _get_root_cmdline_parameter(self, uuid):
        firmware = self.xml_state.build_type.get_firmware()
        initrd_system = self.xml_state.build_type.get_initrd_system()
        cmdline = self.xml_state.build_type.get_kernelcmdline()
        if cmdline and 'root=' in cmdline:
            log.info(
                'Kernel root device explicitly set via kernelcmdline'
            )
            return None

        want_root_cmdline_parameter = False
        if firmware and 'ec2' in firmware:
            # EC2 requires to specifiy the root device in the bootloader
            # configuration. This is because the used pvgrub or hvmloader
            # reads this information and passes it to the guest configuration
            # which has an impact on the devices attached to the guest.
            want_root_cmdline_parameter = True

        if initrd_system and 'dracut' in initrd_system:
            # When using a dracut initrd we have to specify the location
            # of the root device
            want_root_cmdline_parameter = True

        if want_root_cmdline_parameter:
            if uuid:
                return 'root=UUID=%s rw' % format(uuid)
            else:
                log.warning(
                    'root=UUID=<uuid> setup requested, but uuid is not provided'
                )
