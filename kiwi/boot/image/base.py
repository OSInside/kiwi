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
import re
import os
import logging
import glob
from typing import (
    Optional, List, Dict, NamedTuple
)

# project
from kiwi.defaults import Defaults
from kiwi.system.setup import SystemSetup
from kiwi.system.identifier import SystemIdentifier
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.path import Path
from kiwi.system.kernel import Kernel

from kiwi.exceptions import (
    KiwiTargetDirectoryNotFound,
    KiwiConfigFileNotFound,
    KiwiDiskBootImageError
)

boot_names_type = NamedTuple(
    'boot_names_type', [
        ('kernel_name', str),
        ('initrd_name', str),
        ('kernel_version', str),
        ('kernel_filename', str)
    ]
)

log = logging.getLogger('kiwi')


class BootImageBase:
    """
    **Base class for boot image(initrd) task**
    """
    def __init__(
        self, xml_state: XMLState, target_dir: str,
        root_dir: Optional[str] = None,
        signing_keys: Optional[List[str]] = None,
        target_arch: Optional[str] = None
    ) -> None:
        """
        Create a base class instance of a BootImage

        The base class instance only support the common operations
        for boot images. The actual preparation and creation of an
        initrd is specific to the used initrd creation toolchain

        :param XMLState xml_state: Instance of :class:`XMLState`
        :param str target_dir: target dir to store the initrd
        :param str root_dir: system image root directory
        :param List[str] signing_keys: list of package signing keys
        :param str target_arch: target architecture
        """
        self.xml_state = xml_state
        self.target_dir = target_dir
        self.initrd_filename = ''
        self.boot_xml_state: Optional[XMLState] = None
        self.setup: Optional[SystemSetup] = None
        self.signing_keys = signing_keys
        self.target_arch = target_arch
        self.boot_root_directory = root_dir or ''

        if not os.path.exists(target_dir):
            raise KiwiTargetDirectoryNotFound(
                'target directory %s not found' % target_dir
            )

        self.initrd_base_name = ''.join(
            [
                self.xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + self.xml_state.get_image_version(),
                '.initrd'
            ]
        )
        self.post_init()

    def post_init(self) -> None:
        """
        Post initialization method

        Implementation in specialized boot image class
        """
        pass

    @staticmethod
    def has_initrd_support() -> bool:
        """
        Indicates if this instance supports actual creation of an initrd

        The method needs to be overwritten by the subclass
        implementing preparation and creation of an initrd
        """
        return False

    def include_file(self, filename: str, install_media: bool = False) -> None:
        """
        Include file to boot image

        For kiwi boot images this is done by adding package or
        archive definitions with the bootinclude attribute. Thus
        for kiwi boot images the method is a noop

        :param str filename: file path name

        :param bool install_media: include also for installation media initrd
        """
        pass

    def include_module(self, module: str, install_media: bool = False) -> None:
        """
        Include module to boot image

        For kiwi boot no modules configuration is required. Thus in
        such a case this method is a noop.

        :param str module: module to include
        :param bool install_media: include the module for install initrds
        """
        pass

    def omit_module(self, module: str, install_media: bool = False) -> None:
        """
        Omit module to boot image

        For kiwi boot no modules configuration is required. Thus in
        such a case this method is a noop.

        :param str module: module to omit
        :param bool install_media: omit the module for install initrds
        """
        pass

    def set_static_modules(
        self, modules: List[str], install_media: bool = False
    ) -> None:
        """
        Set static modules list for boot image

        For kiwi boot no modules configuration is required. Thus in
        such a case this method is a noop.

        :param list modules: list of modules to include
        :param bool install_media: lists the modules for install initrds
        """
        pass

    def write_system_config_file(
        self, config: Dict, config_file: Optional[str] = None
    ) -> None:
        """
        Writes relevant boot image configuration into configuration file
        that will be part of the system image.

        This is used to configure any further boot image rebuilds after
        deployment. For instance, initrds recreated on kernel update.

        For kiwi boot no specific configuration is required for initrds
        recreation, thus this method is a noop in that case.

        :param dict config: dictonary including configuration parameters
        :param str config_file: configuration file to write
        """
        pass

    def get_boot_names(self) -> boot_names_type:
        """
        Provides kernel and initrd names for the boot image

        :return:
            Contains boot_names_type tuple

            .. code:: python

                boot_names_type(
                    kernel_name='INSTALLED_KERNEL',
                    initrd_name='DRACUT_OUTPUT_NAME',
                    kernel_version='KERNEL_VERSION',
                    kernel_filename='KERNEL_FILE_NAME'
                )

        :rtype: boot_names_type
        """
        kernel = Kernel(
            self.boot_root_directory
        )
        kernel_info = kernel.get_kernel()
        if not kernel_info:
            if self.xml_state.get_initrd_system() == 'none':
                return boot_names_type(
                    kernel_name='none', initrd_name='none',
                    kernel_version='none', kernel_filename='none'
                )
            raise KiwiDiskBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_root_directory
            )
        dracut_output_format = self._get_boot_image_output_file_format(
            kernel_info.version
        )
        return boot_names_type(
            kernel_version=kernel_info.version,
            kernel_name=kernel_info.name,
            initrd_name=dracut_output_format.format(
                kernel_version=kernel_info.version
            ),
            kernel_filename=kernel_info.filename
        )

    def prepare(self) -> None:
        """
        Prepare new root system to create initrd from. Implementation
        is only needed if there is no other root system available

        Implementation in specialized boot image class
        """
        raise NotImplementedError

    def create_initrd(
        self, mbrid: Optional[SystemIdentifier] = None,
        basename: Optional[str] = None, install_initrd: bool = False
    ) -> None:
        """
        Implements creation of the initrd

        :param SystemIdentifier mbrid: instance of SystemIdentifier
        :param str basename: base initrd file name
        :param bool install_initrd: installation media initrd

        Implementation in specialized boot image class
        """
        raise NotImplementedError

    def is_prepared(self) -> bool:
        """
        Check if initrd system is prepared.

        :return: True or False

        :rtype: bool
        """
        return bool(os.listdir(self.boot_root_directory))

    def load_boot_xml_description(self) -> None:
        """
        Load the boot image description referenced by the system image
        description boot attribute
        """
        log.info('Loading Boot XML description')
        boot_description_directory = self.get_boot_description_directory()
        if not boot_description_directory:
            raise KiwiConfigFileNotFound(
                'no boot reference specified in XML description'
            )
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

    def import_system_description_elements(self) -> None:
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
        self.xml_state.copy_strip_sections(
            self.boot_xml_state
        )
        preferences_subsection_names = [
            'bootloader_theme',
            'bootsplash_theme',
            'locale',
            'packagemanager',
            'rpm_check_signatures',
            'rpm_excludedocs',
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
            'bootprofile',
            'btrfs_root_is_snapper_snapshot',
            'gpt_hybrid_mbr',
            'devicepersistency',
            'filesystem',
            'firmware',
            'fsmountoptions',
            'hybridpersistent',
            'hybridpersistent_filesystem',
            'initrd_system',
            'installboot',
            'installprovidefailsafe',
            'kernelcmdline',
            'ramonly',
            'target_removable',
            'vga',
            'wwid_wait_timeout'
        ]
        self.xml_state.copy_build_type_attributes(
            type_attributes, self.boot_xml_state
        )
        self.xml_state.copy_bootloader_section(
            self.boot_xml_state
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

    def get_boot_description_directory(self) -> Optional[str]:
        """
        Provide path to the boot image XML description

        :return: path name

        :rtype: str
        """
        boot_description = self.xml_state.build_type.get_boot()
        if boot_description:
            if not boot_description[0] == '/':
                boot_description = \
                    Defaults.get_boot_image_description_path() + '/' + \
                    boot_description
        return boot_description

    def cleanup(self) -> None:
        """
        Cleanup temporary boot image data if any
        """
        pass

    def _get_boot_image_output_file_format(self, kernel_version: str) -> str:
        """
        The initrd output file format varies between
        the different Linux distributions. Tools like lsinitrd, and also
        grub2 rely on the initrd output file to be in that format. Thus
        kiwi should use the same file format to stay compatible
        with the distributions. The format is determined in three
        stages:

        a) check for an existing initrd file and use this naming schema
        b) if no initrd file is found check the dracut binary for its
           default output file name schema
        c) if no output file schema could be detected from the dracut
           binary return a default output file format which is
           initramfs-{kernel_version}.img

        Let's hope all this mess can be deleted once all distros just
        can agree on one initrd file name schema
        """
        if self.xml_state.get_initrd_system() == 'kiwi':
            # The custom kiwi initrd system is used only on SUSE systems.
            # The initrd environment does not provide dracut and thus the
            # outfile format cannot be determined. on SUSE systems the
            # initrd format is different than on upstream and therefore
            # it can be explicitly specified. Note that the custom initrd
            # system will become obsolete in the future.
            default_outfile_format = 'initrd-{kernel_version}'
        else:
            default_outfile_format = 'initramfs-{kernel_version}.img'

        outfile_format = \
            self._get_boot_image_output_file_format_from_existing_file(
                kernel_version
            )
        if not outfile_format:
            outfile_format = \
                self._get_boot_image_output_file_format_from_dracut_code()

        if outfile_format:
            return outfile_format
        else:
            log.warning('Could not detect dracut output file format')
            log.warning(
                'Using default initrd file name format {0}'.format(
                    default_outfile_format
                )
            )
            return default_outfile_format

    def _get_boot_image_output_file_format_from_dracut_code(
        self
    ) -> Optional[str]:
        dracut_tool = Path.which(
            'dracut', root_dir=self.boot_root_directory, access_mode=os.X_OK
        )
        if dracut_tool:
            outfile_expression = r'outfile=".*/boot/(init.*kernel.*)"'
            with open(dracut_tool) as dracut:
                matches = re.findall(outfile_expression, dracut.read())
                if matches:
                    return matches[0].replace(
                        '$kernel', '{kernel_version}'
                    ).replace(
                        '${kernel}', '{kernel_version}'
                    )
        return None

    def _get_boot_image_output_file_format_from_existing_file(
        self, kernel_version: str
    ) -> Optional[str]:
        for initrd_file in glob.iglob(self.boot_root_directory + '/boot/init*'):
            if not os.path.islink(initrd_file):
                return os.path.basename(initrd_file).replace(
                    kernel_version, '{kernel_version}'
                )
        return None
