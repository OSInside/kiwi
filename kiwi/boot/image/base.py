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
import platform
from tempfile import mkdtemp

# project
from ...defaults import Defaults
from ...xml_description import XMLDescription
from ...xml_state import XMLState
from ...logger import log
from ...path import Path

from ...exceptions import (
    KiwiTargetDirectoryNotFound,
    KiwiConfigFileNotFound
)


class BootImageBase(object):
    """
    Base class for boot image(initrd) task

    Attributes

    * :attr:`xml_state`
        Instance of XMLState of the system image description

    * :attr:`target_dir`
        target dir to store the initrd

    * :attr:`initrd_filename`
        initrd file name

    * :attr:`temp_boot_root_directory`
        temporary directory to create the initrd system

    * :attr:`boot_xml_state`
        Instance of XMLState of the boot image description

    """
    def __init__(self, xml_state, target_dir, root_dir=None):
        self.xml_state = xml_state
        self.target_dir = target_dir
        self.initrd_filename = None
        self.boot_xml_state = None
        self.temp_directories = []

        self.boot_root_directory = root_dir
        if not self.boot_root_directory:
            self.boot_root_directory = mkdtemp(
                prefix='kiwi_boot_root.', dir=self.target_dir
            )
            self.temp_directories.append(
                self.boot_root_directory
            )

        if not os.path.exists(target_dir):
            raise KiwiTargetDirectoryNotFound(
                'target directory %s not found' % target_dir
            )

        self.initrd_file_name = ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + self.xml_state.get_image_version(),
                '.initrd'
            ]
        )

    def prepare(self):
        """
        Prepare new root system to create initrd from. Implementation
        is only needed if there is no other root system available
        """
        raise NotImplementedError

    def create_initrd(self):
        """
        Implements creation of the initrd
        """
        raise NotImplementedError

    def is_prepared(self):
        """
        Check if initrd system is prepared

        :return: initrd system preparation status
        :rtype: bool
        """
        return os.listdir(self.boot_root_directory)

    def load_boot_xml_description(self):
        """
        Load the boot image description referenced by the system image
        description boot attribute
        """
        log.info('Loading Boot XML description')
        boot_description_directory = self.get_boot_description_directory()
        boot_config_file = boot_description_directory + '/config.xml'
        if not os.path.exists(boot_config_file):
            raise KiwiConfigFileNotFound(
                'no Boot XML description found in %s' %
                boot_description_directory
            )
        boot_description = XMLDescription(
            description=boot_config_file,
            derived_from=self.xml_state.xml_data.description_dir
        )

        boot_image_profile = self.xml_state.build_type.get_bootprofile()
        if not boot_image_profile:
            boot_image_profile = 'default'
        boot_kernel_profile = self.xml_state.build_type.get_bootkernel()
        if not boot_kernel_profile:
            boot_kernel_profile = 'std'

        self.boot_xml_state = XMLState(
            boot_description.load(), [boot_image_profile, boot_kernel_profile]
        )
        log.info('--> loaded %s', boot_config_file)
        if self.boot_xml_state.build_type:
            log.info(
                '--> Selected build type: %s',
                self.boot_xml_state.get_build_type_name()
            )
        if self.boot_xml_state.profiles:
            log.info(
                '--> Selected boot profiles: image: %s, kernel: %s',
                boot_image_profile, boot_kernel_profile
            )

    def import_system_description_elements(self):
        """
        Copy information from the system image relevant to create the
        boot image to the boot image state XML description
        """
        self.xml_state.copy_displayname(
            self.boot_xml_state
        )
        self.xml_state.copy_name(
            self.boot_xml_state
        )
        self.xml_state.copy_repository_sections(
            target_state=self.boot_xml_state,
            wipe=True
        )
        self.xml_state.copy_drivers_sections(
            self.boot_xml_state
        )
        strip_description = XMLDescription(
            Defaults.get_boot_image_strip_file()
        )
        strip_xml_state = XMLState(strip_description.load())
        strip_xml_state.copy_strip_sections(
            self.boot_xml_state
        )
        preferences_subsection_names = [
            'bootloader_theme',
            'bootsplash_theme',
            'locale',
            'packagemanager',
            'rpm_check_signatures',
            'showlicense'
        ]
        self.xml_state.copy_preferences_subsections(
            preferences_subsection_names, self.boot_xml_state
        )
        self.xml_state.copy_bootincluded_packages(
            self.boot_xml_state
        )
        self.xml_state.copy_bootincluded_archives(
            self.boot_xml_state
        )
        self.xml_state.copy_bootdelete_packages(
            self.boot_xml_state
        )
        type_attributes = [
            'bootkernel',
            'bootloader',
            'bootprofile',
            'boottimeout',
            'btrfs_root_is_snapshot',
            'gpt_hybrid_mbr',
            'devicepersistency',
            'filesystem',
            'firmware',
            'fsmountoptions',
            'hybrid',
            'hybridpersistent',
            'hybridpersistent_filesystem',
            'installboot',
            'installprovidefailsafe',
            'kernelcmdline',
            'ramonly',
            'vga',
            'wwid_wait_timeout'
        ]
        self.xml_state.copy_build_type_attributes(
            type_attributes, self.boot_xml_state
        )
        self.xml_state.copy_systemdisk_section(
            self.boot_xml_state
        )
        self.xml_state.copy_machine_section(
            self.boot_xml_state
        )
        self.xml_state.copy_oemconfig_section(
            self.boot_xml_state
        )

    def get_boot_description_directory(self):
        """
        Provide path to the boot image XML description

        :return: path name
        :rtype: string
        """
        boot_description = self.xml_state.build_type.get_boot()
        if boot_description:
            if not boot_description[0] == '/':
                boot_description = \
                    Defaults.get_boot_image_description_path() + '/' + \
                    boot_description
            return boot_description

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        for directory in self.temp_directories:
            if directory and os.path.exists(directory):
                Path.wipe(directory)
