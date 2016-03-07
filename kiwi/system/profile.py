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
import collections
from tempfile import NamedTemporaryFile

# project
from .shell import Shell
from ..defaults import Defaults


class Profile(object):
    """
        create bash readable .profile environment from the XML
        description. The information is used by the kiwi first
        boot code.
    """
    def __init__(self, xml_state):
        self.xml_state = xml_state
        self.dot_profile = {}

        self.__image_names_to_profile()
        self.__profile_names_to_profile()
        self.__packages_marked_for_deletion_to_profile()
        self.__type_to_profile()
        self.__preferences_to_profile()
        self.__systemdisk_to_profile()
        self.__strip_to_profile()
        self.__machine_to_profile()
        self.__oemconfig_to_profile()
        self.__drivers_to_profile()

    def add(self, key, value):
        self.dot_profile[key] = value

    def create(self):
        sorted_profile = collections.OrderedDict(
            sorted(self.dot_profile.items())
        )
        temp_profile = NamedTemporaryFile()
        with open(temp_profile.name, 'w') as profile:
            for key, value in list(sorted_profile.items()):
                if value:
                    profile.write(
                        format(key) + '=' + self.__format(value) + '\n'
                    )
        return Shell.quote_key_value_file(temp_profile.name)

    def __oemconfig_to_profile(self):
        # kiwi_oemataraid_scan
        # kiwi_oemvmcp_parmfile
        # kiwi_oemmultipath_scan
        # kiwi_oemswapMB
        # kiwi_oemrootMB
        # kiwi_oemswap
        # kiwi_oempartition_install
        # kiwi_oemdevicefilter
        # kiwi_oemtitle
        # kiwi_oemkboot
        # kiwi_oemreboot
        # kiwi_oemrebootinteractive
        # kiwi_oemshutdown
        # kiwi_oemshutdowninteractive
        # kiwi_oemsilentboot
        # kiwi_oemsilentinstall
        # kiwi_oemsilentverify
        # kiwi_oemskipverify
        # kiwi_oembootwait
        # kiwi_oemunattended
        # kiwi_oemunattended_id
        # kiwi_oemrecovery
        # kiwi_oemrecoveryID
        # kiwi_oemrecoveryPartSize
        # kiwi_oemrecoveryInPlace
        oemconfig = self.xml_state.get_build_type_oemconfig_section()
        if oemconfig:
            self.dot_profile['kiwi_oemataraid_scan'] = \
                self.__text(oemconfig.get_oem_ataraid_scan())
            self.dot_profile['kiwi_oemvmcp_parmfile'] = \
                self.__text(oemconfig.get_oem_vmcp_parmfile())
            self.dot_profile['kiwi_oemmultipath_scan'] = \
                self.__text(oemconfig.get_oem_multipath_scan())
            self.dot_profile['kiwi_oemswapMB'] = \
                self.__text(oemconfig.get_oem_swapsize())
            self.dot_profile['kiwi_oemrootMB'] = \
                self.__text(oemconfig.get_oem_systemsize())
            self.dot_profile['kiwi_oemswap'] = \
                self.__text(oemconfig.get_oem_swap())
            self.dot_profile['kiwi_oempartition_install'] = \
                self.__text(oemconfig.get_oem_partition_install())
            self.dot_profile['kiwi_oemdevicefilter'] = \
                self.__text(oemconfig.get_oem_device_filter())
            self.dot_profile['kiwi_oemtitle'] = \
                self.__text(oemconfig.get_oem_boot_title())
            self.dot_profile['kiwi_oemkboot'] = \
                self.__text(oemconfig.get_oem_kiwi_initrd())
            self.dot_profile['kiwi_oemreboot'] = \
                self.__text(oemconfig.get_oem_reboot())
            self.dot_profile['kiwi_oemrebootinteractive'] = \
                self.__text(oemconfig.get_oem_reboot_interactive())
            self.dot_profile['kiwi_oemshutdown'] = \
                self.__text(oemconfig.get_oem_shutdown())
            self.dot_profile['kiwi_oemshutdowninteractive'] = \
                self.__text(oemconfig.get_oem_shutdown_interactive())
            self.dot_profile['kiwi_oemsilentboot'] = \
                self.__text(oemconfig.get_oem_silent_boot())
            self.dot_profile['kiwi_oemsilentinstall'] = \
                self.__text(oemconfig.get_oem_silent_install())
            self.dot_profile['kiwi_oemsilentverify'] = \
                self.__text(oemconfig.get_oem_silent_verify())
            self.dot_profile['kiwi_oemskipverify'] = \
                self.__text(oemconfig.get_oem_skip_verify())
            self.dot_profile['kiwi_oembootwait'] = \
                self.__text(oemconfig.get_oem_bootwait())
            self.dot_profile['kiwi_oemunattended'] = \
                self.__text(oemconfig.get_oem_unattended())
            self.dot_profile['kiwi_oemunattended_id'] = \
                self.__text(oemconfig.get_oem_unattended_id())
            self.dot_profile['kiwi_oemrecovery'] = \
                self.__text(oemconfig.get_oem_recovery())
            self.dot_profile['kiwi_oemrecoveryID'] = \
                self.__text(oemconfig.get_oem_recoveryID())
            self.dot_profile['kiwi_oemrecoveryPartSize'] = \
                self.__text(oemconfig.get_oem_recovery_part_size())
            self.dot_profile['kiwi_oemrecoveryInPlace'] = \
                self.__text(oemconfig.get_oem_inplace_recovery())

    def __drivers_to_profile(self):
        # kiwi_drivers
        self.dot_profile['kiwi_drivers'] = ','.join(
            self.xml_state.get_drivers_list()
        )

    def __machine_to_profile(self):
        # kiwi_xendomain
        machine = self.xml_state.get_build_type_machine_section()
        if machine:
            self.dot_profile['kiwi_xendomain'] = machine.get_domain()

    def __strip_to_profile(self):
        # kiwi_strip_delete
        # kiwi_strip_tools
        # kiwi_strip_libs
        self.dot_profile['kiwi_strip_delete'] = ' '.join(
            self.xml_state.get_strip_files_to_delete()
        )
        self.dot_profile['kiwi_strip_tools'] = ' '.join(
            self.xml_state.get_strip_tools_to_keep()
        )
        self.dot_profile['kiwi_strip_libs'] = ' '.join(
            self.xml_state.get_strip_libraries_to_keep()
        )

    def __systemdisk_to_profile(self):
        # kiwi_lvmgroup
        # kiwi_lvm
        # kiwi_LVM_LVRoot
        # kiwi_allFreeVolume_X
        # kiwi_LVM_X
        systemdisk = self.xml_state.get_build_type_system_disk_section()
        if systemdisk:
            self.dot_profile['kiwi_lvmgroup'] = systemdisk.get_name()
            if not self.dot_profile['kiwi_lvmgroup']:
                self.dot_profile['kiwi_lvmgroup'] = \
                    Defaults.get_default_volume_group_name()
            if self.xml_state.get_volume_management():
                self.dot_profile['kiwi_lvm'] = 'true'
            for volume in self.xml_state.get_volumes():
                if volume.name == 'LVRoot':
                    if not volume.fullsize:
                        self.dot_profile['kiwi_LVM_LVRoot'] = volume.size
                elif volume.fullsize:
                    if volume.mountpoint:
                        self.dot_profile['kiwi_allFreeVolume_' + volume.name] =\
                            'size:all:' + volume.mountpoint
                    else:
                        self.dot_profile['kiwi_allFreeVolume_' + volume.name] =\
                            'size:all'
                else:
                    if volume.mountpoint:
                        self.dot_profile['kiwi_LVM_' + volume.name] = \
                            volume.size + ':' + volume.mountpoint
                    else:
                        self.dot_profile['kiwi_LVM_' + volume.name] = \
                            volume.size

    def __preferences_to_profile(self):
        # kiwi_iversion
        # kiwi_showlicense
        # kiwi_keytable
        # kiwi_timezone
        # kiwi_hwclock
        # kiwi_language
        # kiwi_splash_theme
        # kiwi_loader_theme
        for preferences in self.xml_state.get_preferences_sections():
            if 'kiwi_iversion' not in self.dot_profile:
                self.dot_profile['kiwi_iversion'] = \
                    self.__text(preferences.get_version())
            if 'kiwi_showlicense' not in self.dot_profile:
                self.dot_profile['kiwi_showlicense'] = \
                    self.__text(preferences.get_showlicense())
            if 'kiwi_keytable' not in self.dot_profile:
                self.dot_profile['kiwi_keytable'] = \
                    self.__text(preferences.get_keytable())
            if 'kiwi_timezone' not in self.dot_profile:
                self.dot_profile['kiwi_timezone'] = \
                    self.__text(preferences.get_timezone())
            if 'kiwi_hwclock' not in self.dot_profile:
                self.dot_profile['kiwi_hwclock'] = \
                    self.__text(preferences.get_hwclock())
            if 'kiwi_language' not in self.dot_profile:
                self.dot_profile['kiwi_language'] = \
                    self.__text(preferences.get_locale())
            if 'kiwi_splash_theme' not in self.dot_profile:
                self.dot_profile['kiwi_splash_theme'] = \
                    self.__text(preferences.get_bootsplash_theme())
            if 'kiwi_loader_theme' not in self.dot_profile:
                self.dot_profile['kiwi_loader_theme'] = \
                    self.__text(preferences.get_bootloader_theme())

    def __type_to_profile(self):
        # kiwi_type
        # kiwi_compressed
        # kiwi_boot_timeout
        # kiwi_wwid_wait_timeout
        # kiwi_hybrid
        # kiwi_hybridpersistent
        # kiwi_hybridpersistent_filesystem
        # kiwi_ramonly
        # kiwi_target_blocksize
        # kiwi_cmdline
        # kiwi_firmware
        # kiwi_bootloader
        # kiwi_devicepersistency
        # kiwi_installboot
        # kiwi_bootkernel
        # kiwi_fsmountoptions
        # kiwi_bootprofile
        # kiwi_vga
        # kiwi_btrfs_root_is_snapshot
        type_section = self.xml_state.build_type
        self.dot_profile['kiwi_type'] = \
            type_section.get_image()
        self.dot_profile['kiwi_compressed'] = \
            type_section.get_compressed()
        self.dot_profile['kiwi_boot_timeout'] = \
            type_section.get_boottimeout()
        self.dot_profile['kiwi_wwid_wait_timeout'] = \
            type_section.get_wwid_wait_timeout()
        self.dot_profile['kiwi_hybrid'] = \
            type_section.get_hybrid()
        self.dot_profile['kiwi_hybridpersistent'] = \
            type_section.get_hybridpersistent()
        self.dot_profile['kiwi_hybridpersistent_filesystem'] = \
            type_section.get_hybridpersistent_filesystem()
        self.dot_profile['kiwi_ramonly'] = \
            type_section.get_ramonly()
        self.dot_profile['kiwi_target_blocksize'] = \
            type_section.get_target_blocksize()
        self.dot_profile['kiwi_cmdline'] = \
            type_section.get_kernelcmdline()
        self.dot_profile['kiwi_firmware'] = \
            type_section.get_firmware()
        self.dot_profile['kiwi_bootloader'] = \
            type_section.get_bootloader()
        self.dot_profile['kiwi_btrfs_root_is_snapshot'] = \
            type_section.get_btrfs_root_is_snapshot()
        self.dot_profile['kiwi_devicepersistency'] = \
            type_section.get_devicepersistency()
        self.dot_profile['kiwi_installboot'] = \
            type_section.get_installboot()
        self.dot_profile['kiwi_bootkernel'] = \
            type_section.get_bootkernel()
        self.dot_profile['kiwi_fsmountoptions'] = \
            type_section.get_fsmountoptions()
        self.dot_profile['kiwi_bootprofile'] = \
            type_section.get_bootprofile()
        self.dot_profile['kiwi_vga'] = \
            type_section.get_vga()

    def __profile_names_to_profile(self):
        # kiwi_profiles
        self.dot_profile['kiwi_profiles'] = ','.join(
            self.xml_state.profiles
        )

    def __packages_marked_for_deletion_to_profile(self):
        # kiwi_delete
        self.dot_profile['kiwi_delete'] = ' '.join(
            self.xml_state.get_to_become_deleted_packages()
        )

    def __image_names_to_profile(self):
        # kiwi_displayname
        # kiwi_cpio_name
        # kiwi_iname
        self.dot_profile['kiwi_iname'] = \
            self.xml_state.xml_data.get_name()

        self.dot_profile['kiwi_displayname'] = \
            self.xml_state.xml_data.get_displayname()
        if not self.dot_profile['kiwi_displayname']:
            self.dot_profile['kiwi_displayname'] = \
                self.dot_profile['kiwi_iname']

        if self.xml_state.get_build_type_name() == 'cpio':
            self.dot_profile['kiwi_cpio_name'] = self.dot_profile['kiwi_iname']

    def __text(self, section_content):
        """
            helper method to return the text for XML elements of the
            following structure: <section>text</section>. The data
            structure builder will return the text as a list
        """
        if section_content:
            content = section_content[0]
            if content == 'false':
                return False
            else:
                return content

    def __format(self, value):
        """
            helper method to format bool profile values in the way
            the boot code expects them
        """
        if value is True:
            return 'true'
        else:
            return format(value)
