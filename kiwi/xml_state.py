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
import copy
import platform
from collections import namedtuple
from textwrap import dedent

# project
from . import xml_parse
from .logger import log
from .system.uri import Uri
from .defaults import Defaults
from .utils.size import StringToSize

from .exceptions import (
    KiwiProfileNotFound,
    KiwiTypeNotFound,
    KiwiDistributionNameError
)


class XMLState(object):
    """
    **Implements methods to get stateful information from the XML data**

    :param object xml_data: instance of XMLDescription
    :param list profiles: list of used profiles
    :param object build_type: build <type> section reference
    """
    def __init__(self, xml_data, profiles=None, build_type=None):
        self.host_architecture = platform.machine()
        self.xml_data = xml_data
        self.profiles = self._used_profiles(profiles)
        self.build_type = self._build_type_section(
            build_type
        )

    def get_preferences_sections(self):
        """
        All preferences sections for the selected profiles

        :return: list of <preferences> section reference(s)

        :rtype: list
        """
        return self._profiled(
            self.xml_data.get_preferences()
        )

    def get_users_sections(self):
        """
        All users sections for the selected profiles

        :return: list of <users> section reference(s)

        :rtype: list
        """
        return self._profiled(
            self.xml_data.get_users()
        )

    def get_build_type_name(self):
        """
        Default build type name

        :return: Content of image attribute from build type

        :rtype: str
        """
        return self.build_type.get_image()

    def get_image_version(self):
        """
        Image version from preferences section.

        Multiple occurences of version in preferences sections are not
        forbidden, however only the first version found defines the
        final image version

        :return: Content of <version> section

        :rtype: str
        """
        for preferences in self.get_preferences_sections():
            version = preferences.get_version()
            if version:
                return version[0]

    def get_initrd_system(self):
        """
        Name of initrd system to use

        Depending on the image type a specific initrd system is
        either pre selected or free of choice according to the
        XML type setup

        :return: dracut, kiwi or None

        :rtype: str
        """
        if self.get_build_type_name() in ['vmx', 'iso']:
            # vmx and iso image types always use dracut as initrd system
            initrd_system = 'dracut'
        elif self.get_build_type_name() in ['oem', 'pxe']:
            # pxe and oem image types default to kiwi if unset
            initrd_system = self.build_type.get_initrd_system() or 'kiwi'
        else:
            initrd_system = self.build_type.get_initrd_system()
        return initrd_system

    def get_rpm_excludedocs(self):
        """
        Gets the rpm-excludedocs configuration flag. Returns
        False if not present.

        :return: True or False

        :rtype: bool
        """
        for preferences in self.get_preferences_sections():
            exclude_docs = preferences.get_rpm_excludedocs()
            if exclude_docs:
                return exclude_docs[0]
        return False

    def get_rpm_check_signatures(self):
        """
        Gets the rpm-check-signatures configuration flag. Returns
        False if not present.

        :return: True or False

        :rtype: bool
        """
        for preferences in self.get_preferences_sections():
            check_signatures = preferences.get_rpm_check_signatures()
            if check_signatures:
                return check_signatures[0]
        return False

    def get_package_manager(self):
        """
        Get configured package manager from selected preferences section

        :return: Content of the <packagemanager> section

        :rtype: str
        """
        for preferences in self.get_preferences_sections():
            package_manager = preferences.get_packagemanager()
            if package_manager:
                return package_manager[0]

    def get_packages_sections(self, section_types):
        """
        List of packages sections matching given section type(s)

        :param list section_types: type name(s) from packages sections

        :return: list of <packages> section reference(s)

        :rtype: list
        """
        result = []
        packages_sections = self._profiled(
            self.xml_data.get_packages()
        )
        for packages in packages_sections:
            packages_type = packages.get_type()
            if packages_type in section_types:
                result.append(packages)
        return result

    def package_matches_host_architecture(self, package):
        """
        Tests if the given package section is applicable for the current host
        architecture. If no architecture is specified within the section
        it is considered as a match returning True.

        Note: The XML section pointer must provide an arch attribute

        :param section: XML section object

        :return: True or False

        :rtype: bool
        """
        return self._section_matches_host_architecture(package)

    def profile_matches_host_architecture(self, profile):
        """
        Tests if the given profile section is applicable for the current host
        architecture. If no architecture is specified within the section
        it is considered as a match returning True.

        Note: The XML section pointer must provide an arch attribute

        :param section: XML section object

        :return: True or False

        :rtype: bool
        """
        return self._section_matches_host_architecture(profile)

    def get_package_sections(self, packages_sections):
        """
        List of package sections from the given packages sections.
        Each list element contains a tuple with the <package> section
        reference and the <packages> section this package belongs to

        If a package entry specfies an architecture, it is only taken if
        the host architecture matches the configured architecture

        :param list packages_sections: <packages>

        :return:
            Contains list of package_type tuples

            .. code:: python

                [package_type(packages_section=object, package_section=object)]

        :rtype: list
        """
        package_type = namedtuple(
            'package_type', ['packages_section', 'package_section']
        )
        result = []
        if packages_sections:
            for packages_section in packages_sections:
                package_list = packages_section.get_package()
                if package_list:
                    for package in package_list:
                        if self.package_matches_host_architecture(package):
                            result.append(
                                package_type(
                                    packages_section=packages_section,
                                    package_section=package
                                )
                            )
        return result

    def get_to_become_deleted_packages(self, force=True):
        """
        List of package names from the type="delete" or type="uninstall"
        packages section(s)

        :param bool force: return "delete" type if True, "uninstall" type
            otherwise

        :return: package names

        :rtype: list
        """
        result = []
        to_become_deleted_packages_sections = self.get_packages_sections(
            ['delete' if force else 'uninstall']
        )
        package_list = self.get_package_sections(
            to_become_deleted_packages_sections
        )
        if package_list:
            for package in package_list:
                result.append(package.package_section.get_name())
        return sorted(list(set(result)))

    def get_bootstrap_packages_sections(self):
        """
        List of packages sections matching type="bootstrap"

        :return: list of <packages> section reference(s)

        :rtype: list
        """
        return self.get_packages_sections(['bootstrap'])

    def get_image_packages_sections(self):
        """
        List of packages sections matching type="image"

        :return: list of <packages> section reference(s)

        :rtype: list
        """
        return self.get_packages_sections(['image'])

    def get_bootstrap_packages(self):
        """
        List of package names from the type="bootstrap" packages section(s)

        The list gets the selected package manager appended
        if there is a request to install packages inside of
        the image via a chroot operation

        :return: package names

        :rtype: list
        """
        result = []
        bootstrap_packages_sections = self.get_bootstrap_packages_sections()
        package_list = self.get_package_sections(
            bootstrap_packages_sections
        )
        if package_list:
            for package in package_list:
                result.append(package.package_section.get_name())
            if self.get_system_packages():
                result.append(self.get_package_manager())
        return sorted(list(set(result)))

    def get_system_packages(self):
        """
        List of package names from the packages sections matching
        type="image" and type=build_type

        :return: package names

        :rtype: list
        """
        result = []
        image_packages_sections = self.get_packages_sections(
            ['image', self.get_build_type_name()]
        )
        package_list = self.get_package_sections(
            image_packages_sections
        )
        if package_list:
            for package in package_list:
                result.append(package.package_section.get_name())
        return sorted(list(set(result)))

    def get_bootstrap_archives(self):
        """
        List of archive names from the type="bootstrap" packages section(s)

        :return: archive names

        :rtype: list
        """
        result = []
        bootstrap_packages_sections = self.get_bootstrap_packages_sections()
        if bootstrap_packages_sections:
            for bootstrap_packages_section in bootstrap_packages_sections:
                archive_list = bootstrap_packages_section.get_archive()
                if archive_list:
                    for archive in archive_list:
                        result.append(archive.get_name())
        return sorted(result)

    def get_system_archives(self):
        """
        List of archive names from the packages sections matching
        type="image" and type=build_type

        :return: archive names

        :rtype: list
        """
        result = []
        image_packages_sections = self.get_packages_sections(
            ['image', self.get_build_type_name()]
        )
        for packages in image_packages_sections:
            for archive in packages.get_archive():
                result.append(archive.get_name())
        return sorted(result)

    def get_system_ignore_packages(self):
        """
        List of ignore package names from the packages sections matching
        type="image" and type=build_type

        :return: package names

        :rtype: list
        """
        result = []
        image_packages_sections = self.get_packages_sections(
            ['image', self.get_build_type_name()]
        )
        for packages in image_packages_sections:
            for package in packages.get_ignore():
                if self.package_matches_host_architecture(package):
                    result.append(package.get_name())
        return sorted(result)

    def get_collection_type(self, section_type='image'):
        """
        Collection type from packages sections matching given section
        type.

        If no collection type is specified the default collection
        type is set to: onlyRequired

        :param string section_type: type name from packages section

        :return: collection type name

        :rtype: str
        """
        typed_packages_sections = self.get_packages_sections(
            [section_type, self.get_build_type_name()]
        )
        collection_type = 'onlyRequired'
        for packages in typed_packages_sections:
            packages_collection_type = packages.get_patternType()
            if packages_collection_type:
                collection_type = packages_collection_type
                break
        return collection_type

    def get_bootstrap_collection_type(self):
        """
        Collection type for packages sections matching type="bootstrap"

        :return: collection type name

        :rtype: str
        """
        return self.get_collection_type('bootstrap')

    def get_system_collection_type(self):
        """
        Collection type for packages sections matching type="image"

        :return: collection type name

        :rtype: str
        """
        return self.get_collection_type('image')

    def get_collections(self, section_type='image'):
        """
        List of collection names from the packages sections matching
        type=section_type and type=build_type

        :return: collection names

        :rtype: list
        """
        result = []
        typed_packages_sections = self.get_packages_sections(
            [section_type, self.get_build_type_name()]
        )
        for packages in typed_packages_sections:
            for collection in packages.get_namedCollection():
                result.append(collection.get_name())
        return list(set(result))

    def get_bootstrap_collections(self):
        """
        List of collection names from the packages sections
        matching type="bootstrap"

        :return: collection names

        :rtype: list
        """
        return self.get_collections('bootstrap')

    def get_system_collections(self):
        """
        List of collection names from the packages sections
        matching type="image"

        :return: collection names

        :rtype: list
        """
        return self.get_collections('image')

    def get_products(self, section_type='image'):
        """
        List of product names from the packages sections matching
        type=section_type and type=build_type

        :param string section_type: type name from packages section

        :return: product names

        :rtype: list
        """
        result = []
        typed_packages_sections = self.get_packages_sections(
            [section_type, self.get_build_type_name()]
        )
        for packages in typed_packages_sections:
            for product in packages.get_product():
                result.append(product.get_name())
        return list(set(result))

    def get_bootstrap_products(self):
        """
        List of product names from the packages sections
        matching type="bootstrap"

        :return: product names

        :rtype: list
        """
        return self.get_products('bootstrap')

    def get_system_products(self):
        """
        List of product names from the packages sections
        matching type="image"

        :return: product names

        :rtype: list
        """
        return self.get_products('image')

    def is_xen_server(self):
        """
        Check if build type domain setup specifies a Xen Server (dom0)

        :return: True or False

        :rtype: bool
        """
        return self.build_type.get_xen_server()

    def is_xen_guest(self):
        """
        Check if build type setup specifies a Xen Guest (domX)
        The check is based on the firmware and xen_loader configuration
        values:

        * Firmware pointing to ec2 means the image is targeted to run
          in Amazon EC2 which is a Xen guest

        * Machine setup with a xen_loader attribute also indicates a
          Xen guest target

        :return: True or False

        :rtype: bool
        """
        firmware = self.build_type.get_firmware()
        machine_section = self.get_build_type_machine_section()
        if firmware and firmware in Defaults.get_ec2_capable_firmware_names():
            # the image is targeted to run in Amazon EC2 which is a Xen system
            return True
        elif machine_section and machine_section.get_xen_loader():
            # the image provides a machine section with a guest loader setup
            return True

    def get_build_type_system_disk_section(self):
        """
        First system disk section from the build type section

        :return: <systemdisk> section reference

        :rtype: xml_parse::systemdisk
        """
        systemdisk_sections = self.build_type.get_systemdisk()
        if systemdisk_sections:
            return systemdisk_sections[0]

    def get_build_type_pxedeploy_section(self):
        """
        First pxedeploy section from the build type section

        :return: <pxedeploy> section reference

        :rtype: xml_parse::pxedeploy
        """
        pxedeploy_sections = self.build_type.get_pxedeploy()
        if pxedeploy_sections:
            return pxedeploy_sections[0]

    def get_build_type_machine_section(self):
        """
        First machine section from the build type section

        :return: <machine> section reference

        :rtype: xml_parse::machine
        """
        machine_sections = self.build_type.get_machine()
        if machine_sections:
            return machine_sections[0]

    def get_build_type_vagrant_config_section(self):
        """
        First vagrantconfig section from the build type section

        :return: <vagrantconfig> section reference

        :rtype: xml_parse::vagrantconfig
        """
        vagrant_config_sections = self.build_type.get_vagrantconfig()
        if vagrant_config_sections:
            return vagrant_config_sections[0]

    def get_build_type_vmdisk_section(self):
        """
        First vmdisk section from the first machine section in the
        build type section

        :return: <vmdisk> section reference

        :rtype: xml_parse::vmdisk
        """
        machine_section = self.get_build_type_machine_section()
        if machine_section:
            vmdisk_sections = machine_section.get_vmdisk()
            if vmdisk_sections:
                return vmdisk_sections[0]

    def get_build_type_vmnic_entries(self):
        """
        vmnic section(s) from the first machine section in the
        build type section

        :return: list of <vmnic> section reference(s)

        :rtype: list
        """
        machine_section = self.get_build_type_machine_section()
        if machine_section:
            return machine_section.get_vmnic()
        else:
            return []

    def get_build_type_vmdvd_section(self):
        """
        First vmdvd section from the first machine section in the
        build type section

        :return: <vmdvd> section reference

        :rtype: xml_parse::vmdvd
        """
        machine_section = self.get_build_type_machine_section()
        if machine_section:
            vmdvd_sections = machine_section.get_vmdvd()
            if vmdvd_sections:
                return vmdvd_sections[0]

    def get_build_type_vmconfig_entries(self):
        """
        List of vmconfig-entry section values from the first
        machine section in the build type section

        :return: <vmconfig_entry> section reference(s)

        :rtype: list
        """
        machine_section = self.get_build_type_machine_section()
        if machine_section:
            vmconfig_entries = machine_section.get_vmconfig_entry()
            if vmconfig_entries:
                return vmconfig_entries

        return []

    def get_build_type_oemconfig_section(self):
        """
        First oemconfig section from the build type section

        :return: <oemconfig> section reference

        :rtype: xml_parse::oemconfig
        """
        oemconfig_sections = self.build_type.get_oemconfig()
        if oemconfig_sections:
            return oemconfig_sections[0]

    def get_oemconfig_oem_multipath_scan(self):
        """
        State value to activate multipath maps. Returns a boolean
        value if specified or None

        :return: Content of <oem-multipath-scan> section value

        :rtype: bool
        """
        oemconfig = self.get_build_type_oemconfig_section()
        if oemconfig and oemconfig.get_oem_multipath_scan():
            return oemconfig.get_oem_multipath_scan()[0]

    def get_build_type_containerconfig_section(self):
        """
        First containerconfig section from the build type section

        :return: <containerconfig> section reference

        :rtype: xml_parse::containerconfig
        """
        container_config_sections = self.build_type.get_containerconfig()
        if container_config_sections:
            return container_config_sections[0]

    def get_build_type_size(self, include_unpartitioned=False):
        """
        Size information from the build type section.
        If no unit is set the value is treated as mbytes

        :param bool include_unpartitioned: sets if the unpartitioned area
            should be included in the computed size or not

        :return: mbytes

        :rtype: int
        """
        size_section = self.build_type.get_size()
        if size_section:
            unit = size_section[0].get_unit()
            additive = size_section[0].get_additive()
            unpartitioned = size_section[0].get_unpartitioned()
            value = int(size_section[0].get_valueOf_())
            if not include_unpartitioned and unpartitioned is not None:
                value -= unpartitioned
            if unit == 'G':
                value *= 1024
            size_type = namedtuple(
                'size_type', ['mbytes', 'additive']
            )
            return size_type(
                mbytes=value, additive=additive
            )

    def get_build_type_unpartitioned_bytes(self):
        """
        Size of the unpartitioned area for image in megabytes

        :return: mbytes

        :rtype: int
        """
        size_section = self.build_type.get_size()
        if size_section:
            unit = size_section[0].get_unit() or 'M'
            unpartitioned = size_section[0].get_unpartitioned() or 0
            return StringToSize.to_bytes('{0}{1}'.format(unpartitioned, unit))
        return 0

    def get_disk_start_sector(self):
        """
        First disk sector number to be used by the first disk partition.

        :return: number

        :rtype: int
        """
        disk_start_sector = self.build_type.get_disk_start_sector()
        if disk_start_sector is None:
            disk_start_sector = Defaults.get_default_disk_start_sector()
        return disk_start_sector

    def get_build_type_spare_part_size(self):
        """
        Size information for the spare_part size from the build
        type. If no unit is set the value is treated as mbytes

        :return: mbytes

        :rtype: int
        """
        spare_part_size = self.build_type.get_spare_part()
        if spare_part_size:
            return self._to_mega_byte(spare_part_size)

    def get_build_type_format_options(self):
        """
        Disk format options returned as a dictionary

        :return: format options

        :rtype: dict
        """
        result = {}
        format_options = self.build_type.get_formatoptions()
        if format_options:
            for option in format_options.split(','):
                key_value_list = option.split('=')
                if len(key_value_list) == 2:
                    result[key_value_list[0]] = key_value_list[1]
                else:
                    result[key_value_list[0]] = None
        return result

    def get_volume_group_name(self):
        """
        Volume group name from selected <systemdisk> section

        :return: volume group name

        :rtype: str
        """
        systemdisk_section = self.get_build_type_system_disk_section()
        volume_group_name = None
        if systemdisk_section:
            volume_group_name = systemdisk_section.get_name()
        if not volume_group_name:
            volume_group_name = Defaults.get_default_volume_group_name()
        return volume_group_name

    def get_users(self):
        """
        List of configured users.

        Each entry in the list is a single xml_parse::user instance.

        :return: list of <user> section reference(s)

        :rtype: list
        """
        users_list = []
        users_names_added = []
        for users_section in self.get_users_sections():
            for user in users_section.get_user():
                if user.get_name() not in users_names_added:
                    users_list.append(user)
                    users_names_added.append(user.get_name())

        return users_list

    def get_user_groups(self, user_name):
        """
        List of group names matching specified user

        Each entry in the list is the name of a group that the specified
        user belongs to. The first item in the list is the login or primary
        group. The list will be empty if no groups are specified in the
        description file.

        :return: groups data for the given user

        :rtype: list
        """
        groups_list = []
        for users_section in self.get_users_sections():
            for user in users_section.get_user():
                if user.get_name() == user_name:
                    user_groups = user.get_groups()
                    if user_groups:
                        groups_list += user.get_groups().split(',')

        # order of list items matter, thus we don't use set() here
        # better faster, nicer solutions welcome :)
        result_group_list = []
        for item in groups_list:
            if item not in result_group_list:
                result_group_list.append(item)

        return result_group_list

    def get_container_config(self):
        """
        Dictionary of containerconfig information

        Takes attributes and subsection data from the selected
        <containerconfig> section and stores it in a dictionary
        """
        container_config = self._match_docker_base_data()
        container_config.update(
            self._match_docker_entrypoint()
        )
        container_config.update(
            self._match_docker_subcommand()
        )
        container_config.update(
            self._match_docker_expose_ports()
        )
        container_config.update(
            self._match_docker_volumes()
        )
        container_config.update(
            self._match_docker_environment()
        )
        container_config.update(
            self._match_docker_labels()
        )
        return container_config

    def set_container_config_tag(self, tag):
        """
        Set new tag name in containerconfig section

        In order to set a new tag value an existing containerconfig and
        tag setup is required

        :param string tag: tag name
        """
        container_config_section = self.get_build_type_containerconfig_section()
        if container_config_section and container_config_section.get_tag():
            container_config_section.set_tag(tag)
        else:
            message = dedent('''\n
                No <containerconfig> section and/or tag attribute configured

                In order to set the tag {0} as new container tag,
                an initial containerconfig section including a tag
                setup is required
            ''')
            log.warning(message.format(tag))

    def add_container_config_label(self, label_name, value):
        """
        Adds a new label in the containerconfig section, if a label with the
        same name is already defined in containerconfig it gets overwritten by
        this method.

        :param str label_name: the string representing the label name
        :param str value: the value of the label
        """
        if self.get_build_type_name() not in ['docker', 'oci']:
            message = dedent('''\n
                Labels can only be configured for container image types
                docker and oci.
            ''')
            log.warning(message)
            return

        container_config_section = self.get_build_type_containerconfig_section()
        if not container_config_section:
            container_config_section = xml_parse.containerconfig(
                name=Defaults.get_default_container_name(),
                tag=Defaults.get_default_container_tag()
            )
            self.build_type.set_containerconfig([container_config_section])

        labels = container_config_section.get_labels()
        if not labels:
            labels = [xml_parse.labels()]

        label_names = []
        for label in labels[0].get_label():
            label_names.append(label.get_name())

        if label_name in label_names:
            labels[0].replace_label_at(
                label_names.index(label_name),
                xml_parse.label(label_name, value)
            )
        else:
            labels[0].add_label(xml_parse.label(label_name, value))

        container_config_section.set_labels(labels)

    def get_volumes(self):
        """
        List of configured systemdisk volumes.

        Each entry in the list is a tuple with the following information

        * name: name of the volume
        * size: size of the volume
        * realpath: system path to lookup volume data. If no mountpoint
          is set the volume name is used as data path.
        * mountpoint: volume mount point and volume data path
        * fullsize: takes all space True|False
        * attributes: list of volume attributes handled via chattr

        :return:
            Contains list of volume_type tuples

            .. code:: python

                [
                    volume_type(
                        name=volume_name,
                        size=volume_size,
                        realpath=path,
                        mountpoint=path,
                        fullsize=True,
                        label=volume_label,
                        attributes=['no-copy-on-write']
                    )
                ]

        :rtype: list
        """
        volume_type_list = []
        systemdisk_section = self.get_build_type_system_disk_section()
        if not systemdisk_section:
            return volume_type_list

        volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes'
            ]
        )

        volumes = systemdisk_section.get_volume()
        have_root_volume_setup = False
        have_full_size_volume = False
        if volumes:
            for volume in volumes:
                # volume setup for a full qualified volume with name and
                # mountpoint information. See below for exceptions
                name = volume.get_name()
                mountpoint = volume.get_mountpoint()
                realpath = mountpoint
                size = volume.get_size()
                freespace = volume.get_freespace()
                fullsize = False
                label = volume.get_label()
                attributes = []

                if volume.get_copy_on_write() is False:
                    # by default copy-on-write is switched on for any
                    # filesystem. Thus only if no copy on write is requested
                    # the attribute is handled
                    attributes.append('no-copy-on-write')

                if '@root' in name:
                    # setup root volume, it takes a fixed volume name and
                    # has no specific mountpoint
                    mountpoint = None
                    realpath = '/'
                    name = 'LVRoot'
                    have_root_volume_setup = True
                elif not mountpoint:
                    # setup volume without mountpoint. In this case the name
                    # attribute is used as mountpoint path and a name for the
                    # volume is created from that path information
                    mountpoint = name
                    realpath = mountpoint
                    name = self._to_volume_name(name)

                if size:
                    size = 'size:' + format(
                        self._to_mega_byte(size)
                    )
                elif freespace:
                    size = 'freespace:' + format(
                        self._to_mega_byte(freespace)
                    )
                else:
                    size = 'freespace:' + format(
                        Defaults.get_min_volume_mbytes()
                    )

                if ':all' in size:
                    size = None
                    fullsize = True
                    have_full_size_volume = True

                volume_type_list.append(
                    volume_type(
                        name=name,
                        size=size,
                        fullsize=fullsize,
                        mountpoint=mountpoint,
                        realpath=realpath,
                        label=label,
                        attributes=attributes
                    )
                )

        if not have_root_volume_setup:
            # There must always be a root volume setup. It will be the
            # full size volume if no other volume has this setup
            if have_full_size_volume:
                size = 'freespace:' + format(
                    Defaults.get_min_volume_mbytes()
                )
                fullsize = False
            else:
                size = None
                fullsize = True
            volume_type_list.append(
                volume_type(
                    name='LVRoot',
                    size=size,
                    fullsize=fullsize,
                    mountpoint=None,
                    realpath='/',
                    label=None,
                    attributes=[]
                )
            )

        return volume_type_list

    def get_volume_management(self):
        """
        Provides information which volume management system is used

        :return: name of volume manager

        :rtype: str
        """
        volume_filesystems = ['btrfs']
        selected_filesystem = self.build_type.get_filesystem()
        selected_system_disk = self.get_build_type_system_disk_section()
        volume_management = None
        if selected_system_disk and selected_system_disk.get_preferlvm():
            # LVM volume management is preferred, use it
            volume_management = 'lvm'
        elif selected_filesystem in volume_filesystems:
            # specified filesystem has its own volume management system
            volume_management = selected_filesystem
        elif selected_system_disk:
            # systemdisk section is specified with non volume capable
            # filesystem and no volume management preference. So let's
            # use LVM by default
            volume_management = 'lvm'
        return volume_management

    def get_drivers_list(self):
        """
        List of driver names from all drivers sections matching
        configured profiles

        :return: driver names

        :rtype: list
        """
        drivers_sections = self._profiled(
            self.xml_data.get_drivers()
        )
        result = []
        if drivers_sections:
            for driver in drivers_sections:
                for file_section in driver.get_file():
                    result.append(file_section.get_name())
        return result

    def get_strip_list(self, section_type):
        """
        List of strip names matching the given section type
        and profiles

        :param string section_type: type name from packages section

        :return: strip names

        :rtype: list
        """
        strip_sections = self._profiled(
            self.xml_data.get_strip()
        )
        result = []
        if strip_sections:
            for strip in strip_sections:
                if strip.get_type() == section_type:
                    for file_section in strip.get_file():
                        result.append(file_section.get_name())
        return result

    def get_strip_files_to_delete(self):
        """
        Items to delete from strip section

        :return: item names

        :rtype: list
        """
        return self.get_strip_list('delete')

    def get_strip_tools_to_keep(self):
        """
        Tools to keep from strip section

        :return: tool names

        :rtype: list
        """
        return self.get_strip_list('tools')

    def get_strip_libraries_to_keep(self):
        """
        Libraries to keep from strip section

        :return: librarie names

        :rtype: list
        """
        return self.get_strip_list('libs')

    def get_repository_sections(self):
        """
        List of all repository sections matching configured profiles

        :return: <repository> section reference(s)

        :rtype: list
        """
        return self._profiled(
            self.xml_data.get_repository()
        )

    def get_repository_sections_used_for_build(self):
        """
        List of all repositorys sections used to build the image and
        matching configured profiles.

        :return: <repository> section reference(s)

        :rtype: list
        """
        repos = self.get_repository_sections()
        return list(
            repo for repo in repos if not repo.get_imageonly()
        )

    def get_repository_sections_used_in_image(self):
        """
        List of all repositorys sections to be configured in the resulting
        image matching configured profiles.

        :return: <repository> section reference(s)

        :rtype: list
        """
        repos = self.get_repository_sections()
        return list(
            repo for repo in repos if repo.get_imageinclude() or
            repo.get_imageonly()
        )

    def delete_repository_sections(self):
        """
        Delete all repository sections matching configured profiles
        """
        self.xml_data.set_repository([])

    def delete_repository_sections_used_for_build(self):
        """
        Delete all repository sections used to build the image matching
        configured profiles
        """
        used_for_build = self.get_repository_sections_used_for_build()
        all_repos = self.get_repository_sections()
        self.xml_data.set_repository([
            repo for repo in all_repos if repo not in used_for_build
        ])

    def set_repository(
        self, repo_source, repo_type, repo_alias, repo_prio,
        repo_imageinclude=False, repo_package_gpgcheck=None
    ):
        """
        Overwrite repository data of the first repository

        :param string repo_source: repository URI
        :param string repo_type: type name defined by schema
        :param string repo_alias: alias name
        :param string repo_prio: priority number, package manager specific
        :param boolean repo_imageinclude: setup repository inside of the image
        :param boolean repo_package_gpgcheck: enable/disable package gpg checks
        """
        repository_sections = self.get_repository_sections()
        if repository_sections:
            repository = repository_sections[0]
            if repo_alias:
                repository.set_alias(repo_alias)
            if repo_type:
                repository.set_type(repo_type)
            if repo_source:
                repository.get_source().set_path(repo_source)
            if repo_prio:
                repository.set_priority(int(repo_prio))
            if repo_imageinclude:
                repository.set_imageinclude(repo_imageinclude)
            if repo_package_gpgcheck is not None:
                repository.set_package_gpgcheck(repo_package_gpgcheck)

    def add_repository(
        self, repo_source, repo_type, repo_alias, repo_prio,
        repo_imageinclude=False, repo_package_gpgcheck=None
    ):
        """
        Add a new repository section at the end of the list

        :param string repo_source: repository URI
        :param string repo_type: type name defined by schema
        :param string repo_alias: alias name
        :param string repo_prio: priority number, package manager specific
        :param boolean repo_imageinclude: setup repository inside of the image
        :param boolean repo_package_gpgcheck: enable/disable package gpg checks
        """
        try:
            repo_prio = int(repo_prio)
        except Exception:
            repo_prio = None
        self.xml_data.add_repository(
            xml_parse.repository(
                type_=repo_type,
                alias=repo_alias,
                priority=repo_prio,
                source=xml_parse.source(path=repo_source),
                imageinclude=repo_imageinclude,
                package_gpgcheck=repo_package_gpgcheck
            )
        )

    def copy_displayname(self, target_state):
        """
        Copy image displayname from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        displayname = self.xml_data.get_displayname()
        if displayname:
            target_state.xml_data.set_displayname(displayname)

    def copy_name(self, target_state):
        """
        Copy image name from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        target_state.xml_data.set_name(
            self.xml_data.get_name()
        )

    def copy_drivers_sections(self, target_state):
        """
        Copy drivers sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        drivers_sections = self._profiled(
            self.xml_data.get_drivers()
        )
        if drivers_sections:
            for drivers_section in drivers_sections:
                target_state.xml_data.add_drivers(drivers_section)

    def copy_systemdisk_section(self, target_state):
        """
        Copy systemdisk sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        systemdisk_section = self.get_build_type_system_disk_section()
        if systemdisk_section:
            target_state.build_type.set_systemdisk(
                [systemdisk_section]
            )

    def copy_strip_sections(self, target_state):
        """
        Copy strip sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        strip_sections = self._profiled(
            self.xml_data.get_strip()
        )
        if strip_sections:
            for strip_section in strip_sections:
                target_state.xml_data.add_strip(strip_section)

    def copy_machine_section(self, target_state):
        """
        Copy machine sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        machine_section = self.get_build_type_machine_section()
        if machine_section:
            target_state.build_type.set_machine(
                [machine_section]
            )

    def copy_oemconfig_section(self, target_state):
        """
        Copy oemconfig sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        """
        oemconfig_section = self.get_build_type_oemconfig_section()
        if oemconfig_section:
            target_state.build_type.set_oemconfig(
                [oemconfig_section]
            )

    def copy_repository_sections(self, target_state, wipe=False):
        """
        Copy repository sections from this xml state to the target xml state

        :param object target_state: XMLState instance
        :param bool wipe: delete all repos in target prior to copy
        """
        repository_sections = self._profiled(
            self.xml_data.get_repository()
        )
        if repository_sections:
            if wipe:
                target_state.xml_data.set_repository([])
            for repository_section in repository_sections:
                repository_copy = copy.deepcopy(repository_section)
                # profiles are not copied because they might not exist
                # in the target description
                repository_copy.set_profiles(None)
                target_state.xml_data.add_repository(repository_copy)

    def copy_preferences_subsections(self, section_names, target_state):
        """
        Copy subsections of the preferences sections, matching given
        section names, from this xml state to the target xml state

        :param list section_names: preferences subsection names
        :param object target_state: XMLState instance
        """
        target_preferences_sections = target_state.get_preferences_sections()
        if target_preferences_sections:
            target_preferences_section = target_preferences_sections[0]
            for preferences_section in self.get_preferences_sections():
                for section_name in section_names:
                    get_section_method = getattr(
                        preferences_section, 'get_' + section_name
                    )
                    section = get_section_method()
                    if section:
                        set_section_method = getattr(
                            target_preferences_section, 'set_' + section_name
                        )
                        set_section_method(section)

    def copy_build_type_attributes(self, attribute_names, target_state):
        """
        Copy specified attributes from this build type section to the
        target xml state build type section

        :param list attribute_names: type section attributes
        :param object target_state: XMLState instance
        """
        for attribute in attribute_names:
            get_type_method = getattr(
                self.build_type, 'get_' + attribute
            )
            attribute_value = get_type_method()
            if attribute_value:
                set_type_method = getattr(
                    target_state.build_type, 'set_' + attribute
                )
                set_type_method(attribute_value)

    def copy_bootincluded_packages(self, target_state):
        """
        Copy packages marked as bootinclude to the packages type=image
        (or type=bootstrap if no type=image was found) section in the
        target xml state. The package will also be removed from the
        packages type=delete section in the target xml state if
        present there

        :param object target_state: XMLState instance
        """
        target_packages_sections = \
            target_state.get_image_packages_sections()
        if not target_packages_sections:
            # no packages type=image section was found, add to bootstrap
            target_packages_sections = \
                target_state.get_bootstrap_packages_sections()
        if target_packages_sections:
            target_packages_section = \
                target_packages_sections[0]
            package_names_added = []
            packages_sections = self.get_packages_sections(
                ['image', 'bootstrap', self.get_build_type_name()]
            )
            package_list = self.get_package_sections(
                packages_sections
            )
            if package_list:
                for package in package_list:
                    if package.package_section.get_bootinclude():
                        target_packages_section.add_package(
                            xml_parse.package(
                                name=package.package_section.get_name()
                            )
                        )
                        package_names_added.append(
                            package.package_section.get_name()
                        )
            delete_packages_sections = target_state.get_packages_sections(
                ['delete']
            )
            package_list = self.get_package_sections(
                delete_packages_sections
            )
            if package_list:
                for package in package_list:
                    package_name = package.package_section.get_name()
                    if package_name in package_names_added:
                        package.packages_section.package.remove(
                            package.package_section
                        )

    def copy_bootincluded_archives(self, target_state):
        """
        Copy archives marked as bootinclude to the packages type=bootstrap
        section in the target xml state

        :param object target_state: XMLState instance
        """
        target_bootstrap_packages_sections = \
            target_state.get_bootstrap_packages_sections()
        if target_bootstrap_packages_sections:
            target_bootstrap_packages_section = \
                target_bootstrap_packages_sections[0]
            packages_sections = self.get_packages_sections(
                ['image', 'bootstrap', self.get_build_type_name()]
            )
            for packages_section in packages_sections:
                archive_list = packages_section.get_archive()
                if archive_list:
                    for archive in archive_list:
                        if archive.get_bootinclude():
                            target_bootstrap_packages_section.add_archive(
                                xml_parse.archive(
                                    name=archive.get_name()
                                )
                            )

    def copy_bootdelete_packages(self, target_state):
        """
        Copy packages marked as bootdelete to the packages type=delete
        section in the target xml state

        :param object target_state: XMLState instance
        """
        target_delete_packages_sections = target_state.get_packages_sections(
            ['delete']
        )
        if not target_delete_packages_sections:
            target_delete_packages_sections = [
                xml_parse.packages(type_='delete')
            ]
            target_state.xml_data.add_packages(
                target_delete_packages_sections[0]
            )

        target_delete_packages_section = \
            target_delete_packages_sections[0]
        packages_sections = self.get_packages_sections(
            ['image', 'bootstrap', self.get_build_type_name()]
        )
        package_list = self.get_package_sections(
            packages_sections
        )
        if package_list:
            for package in package_list:
                if package.package_section.get_bootdelete():
                    target_delete_packages_section.add_package(
                        xml_parse.package(
                            name=package.package_section.get_name()
                        )
                    )

    def get_distribution_name_from_boot_attribute(self):
        """
        Extract the distribution name from the boot attribute of the
        build type section.

        If no boot attribute is configured or the contents does not
        match the kiwi defined naming schema for boot image descriptions,
        an exception is thrown

        :return: lowercase distribution name

        :rtype: str
        """
        boot_attribute = self.build_type.get_boot()
        if not boot_attribute:
            raise KiwiDistributionNameError(
                'No boot attribute to extract distribution name from found'
            )
        boot_attribute_format = '^.*-(.*)$'
        boot_attribute_expression = re.match(
            boot_attribute_format, boot_attribute
        )
        if not boot_attribute_expression:
            raise KiwiDistributionNameError(
                'Boot attribute "%s" does not match expected format %s' %
                (boot_attribute, boot_attribute_format)
            )
        return boot_attribute_expression.group(1).lower()

    def get_fs_mount_option_list(self):
        """
        List of root filesystem mount options

        The list contains one element with the information from the
        fsmountoptions attribute. The value there is passed along to
        the -o mount option

        :return: max one element list with mount option string

        :rtype: list
        """
        option_list = []
        mount_options = self.build_type.get_fsmountoptions()
        if mount_options:
            option_list = [mount_options]

        return option_list

    def get_derived_from_image_uri(self):
        """
        Uri object of derived image if configured

        Specific image types can be based on a master image.
        This method returns the location of this image when
        configured in the XML description

        :return: Instance of Uri

        :rtype: object
        """
        derived_image = self.build_type.get_derived_from()
        if derived_image:
            return Uri(derived_image, repo_type='container')

    def set_derived_from_image_uri(self, uri):
        """
        Set derived_from attribute to a new value

        In order to set a new value the derived_from attribute
        must be already present in the image configuration

        :param string uri: URI
        """
        if self.build_type.get_derived_from():
            self.build_type.set_derived_from(uri)
        else:
            message = dedent('''\n
                No derived_from attribute configured in image <type>

                In order to set the uri {0} as base container reference
                an initial derived_from attribute must be set in the
                type section
            ''')
            log.warning(message.format(uri))

    def _used_profiles(self, profiles=None):
        """
        return list of profiles to use. The method looks up the
        profiles section in the XML description and searches for
        profiles matching the architecture. If no arch specifier
        is set the profile is considered to be valid for any arch

        If the profiles argument is not set only profiles
        marked with the attribute import=true will be selected.
        Profiles specified in the argument will take the highest
        priority and causes to skip the lookup of import profiles
        in the XML description

        :param list profiles: selected profile names
        """
        available_profiles = dict()
        import_profiles = []
        profiles_section = self.xml_data.get_profiles()
        if profiles_section:
            for profile in profiles_section[0].get_profile():
                if self.profile_matches_host_architecture(profile):
                    name = profile.get_name()
                    available_profiles[name] = profile
                    if profile.get_import():
                        import_profiles.append(name)
        if not profiles:
            return import_profiles
        else:
            resolved_profiles = []
            for profile in profiles:
                resolved_profiles += self._solve_profile_dependencies(
                    profile, available_profiles, resolved_profiles
                )
            return resolved_profiles

    def _section_matches_host_architecture(self, section):
        architectures = section.get_arch()
        if architectures:
            if self.host_architecture not in architectures.split(','):
                return False
        return True

    def _match_docker_base_data(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_base = {}
        if container_config_section:
            name = container_config_section.get_name()
            tag = container_config_section.get_tag()
            maintainer = container_config_section.get_maintainer()
            user = container_config_section.get_user()
            workingdir = container_config_section.get_workingdir()
            additional_tags = container_config_section.get_additionaltags()
            if name:
                container_base['container_name'] = name

            if tag:
                container_base['container_tag'] = tag

            if additional_tags:
                container_base['additional_tags'] = additional_tags.split(',')

            if maintainer:
                container_base['maintainer'] = [
                    ''.join(
                        ['--author=', maintainer]
                    )
                ]

            if user:
                container_base['user'] = [
                    ''.join(
                        ['--config.user=', user]
                    )
                ]

            if workingdir:
                container_base['workingdir'] = [
                    ''.join(
                        ['--config.workingdir=', workingdir]
                    )
                ]
        return container_base

    def _match_docker_entrypoint(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_entry = {}
        if container_config_section:
            entrypoint = container_config_section.get_entrypoint()
            if entrypoint and entrypoint[0].get_execute():
                container_entry['entry_command'] = [
                    ''.join(
                        [
                            '--config.entrypoint=',
                            entrypoint[0].get_execute()
                        ]
                    )
                ]
                argument_list = entrypoint[0].get_argument()
                if argument_list:
                    for argument in argument_list:
                        container_entry['entry_command'].append(
                            ''.join(
                                [
                                    '--config.entrypoint=',
                                    argument.get_name()
                                ]
                            )
                        )
            elif entrypoint and entrypoint[0].get_clear():
                container_entry['entry_command'] = [
                    ''.join(
                        [
                            '--clear=config.entrypoint'
                        ]
                    )
                ]
        return container_entry

    def _match_docker_subcommand(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_subcommand = {}
        if container_config_section:
            subcommand = container_config_section.get_subcommand()
            if subcommand and subcommand[0].get_execute():
                container_subcommand['entry_subcommand'] = [
                    ''.join(
                        [
                            '--config.cmd=',
                            subcommand[0].get_execute()
                        ]
                    )
                ]
                argument_list = subcommand[0].get_argument()
                if argument_list:
                    for argument in argument_list:
                        container_subcommand['entry_subcommand'].append(
                            ''.join(
                                [
                                    '--config.cmd=',
                                    argument.get_name()
                                ]
                            )
                        )
            elif subcommand and subcommand[0].get_clear():
                container_subcommand['entry_subcommand'] = [
                    ''.join(
                        [
                            '--clear=config.cmd',
                        ]
                    )
                ]
        return container_subcommand

    def _match_docker_expose_ports(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_expose = {}
        if container_config_section:
            expose = container_config_section.get_expose()
            if expose and expose[0].get_port():
                container_expose['expose_ports'] = []
                for port in expose[0].get_port():
                    container_expose['expose_ports'].append(
                        ''.join(
                            [
                                '--config.exposedports=',
                                format(port.get_number())
                            ]
                        )
                    )
        return container_expose

    def _match_docker_volumes(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_volumes = {}
        if container_config_section:
            volumes = container_config_section.get_volumes()
            if volumes and volumes[0].get_volume():
                container_volumes['volumes'] = []
                for volume in volumes[0].get_volume():
                    container_volumes['volumes'].append(
                        ''.join(
                            [
                                '--config.volume=',
                                volume.get_name()
                            ]
                        )
                    )
        return container_volumes

    def _match_docker_environment(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_env = {}
        if container_config_section:
            environment = container_config_section.get_environment()
            if environment and environment[0].get_env():
                container_env['environment'] = []
                for env in environment[0].get_env():
                    container_env['environment'].append(
                        ''.join(
                            [
                                '--config.env=',
                                env.get_name(), '=', env.get_value()
                            ]
                        )
                    )
        return container_env

    def _match_docker_labels(self):
        container_config_section = self.get_build_type_containerconfig_section()
        container_labels = {}
        if container_config_section:
            labels = container_config_section.get_labels()
            if labels and labels[0].get_label():
                container_labels['labels'] = []
                for label in labels[0].get_label():
                    container_labels['labels'].append(
                        ''.join(
                            [
                                '--config.label=',
                                label.get_name(), '=', label.get_value()
                            ]
                        )
                    )
        return container_labels

    def _solve_profile_dependencies(
        self, profile, available_profiles, current_profiles
    ):
        if profile not in available_profiles:
            raise KiwiProfileNotFound(
                'profile {0} not found for host arch {1}'.format(
                    profile, self.host_architecture
                )
            )
        profiles_to_add = []
        if profile not in current_profiles:
            profiles_to_add.append(profile)
            for required in available_profiles[profile].get_requires():
                if required.get_profile() not in current_profiles:
                    profiles_to_add += self._solve_profile_dependencies(
                        required.get_profile(), available_profiles,
                        current_profiles + profiles_to_add
                    )
        return profiles_to_add

    def _build_type_section(self, build_type=None):
        """
        find type section matching build type and profiles or default
        """
        # lookup all preferences sections for selected profiles
        image_type_sections = []
        for preferences in self.get_preferences_sections():
            image_type_sections += preferences.get_type()

        # lookup if build type matches provided type
        if build_type:
            for image_type in image_type_sections:
                if build_type == image_type.get_image():
                    return image_type
            raise KiwiTypeNotFound(
                'build type %s not found' % build_type
            )

        # lookup if build type matches primary type
        for image_type in image_type_sections:
            if image_type.get_primary():
                return image_type

        # build type is first type section in XML sequence
        if image_type_sections:
            return image_type_sections[0]
        raise KiwiTypeNotFound(
            'No build type defined. At least one type section is mandatory'
        )

    def _profiled(self, xml_abstract):
        """
        return only those sections matching the instance stored
        profile list from the given XML abstract. Sections without
        a profile are wildcard sections and will be used in any
        case
        """
        result = []
        for section in xml_abstract:
            profiles = section.get_profiles()
            if profiles:
                for profile in profiles.split(','):
                    if self.profiles and profile in self.profiles:
                        result.append(section)
                        break
            else:
                result.append(section)
        return result

    def _to_volume_name(self, name):
        name = name.strip()
        name = re.sub(r'^\/+', r'', name)
        name = name.replace('/', '_')
        return name

    def _to_mega_byte(self, size):
        value = re.search('(\d+)([MG]*)', format(size))
        if value:
            number = value.group(1)
            unit = value.group(2)
            if unit == 'G':
                return int(number) * 1024
            else:
                return int(number)
        else:
            return size
