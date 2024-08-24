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
import json
import re
import logging
from textwrap import dedent
from typing import (
    NamedTuple, Dict, List, Any
)

# project
from kiwi.version import __version__
from io import StringIO
from kiwi.xml_description import XMLDescription
from kiwi.firmware import FirmWare
from kiwi.xml_state import XMLState
from kiwi.system.uri import Uri
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import (
    KiwiRuntimeError
)

import kiwi.defaults as defaults

dracut_module_type = NamedTuple(
    'dracut_module_type', [
        ('package', str),
        ('min_version', str)
    ]
)

log = logging.getLogger('kiwi')


class RuntimeChecker:
    """
    **Implements build consistency checks at runtime**
    """
    def __init__(self, xml_state: XMLState) -> None:
        """
        The schema of an image description covers structure and syntax of
        the provided data. The RuntimeChecker provides methods to perform
        further semantic checks which allows to recognize potential build
        or boot problems early.

        :param object xml_state: Instance of XMLState
        """
        self.xml_state = xml_state

    def check_repositories_configured(self) -> None:
        """
        Verify that there are repositories configured
        """
        if not self.xml_state.get_repository_sections():
            raise KiwiRuntimeError(
                'No repositories configured'
            )

    def check_include_references_unresolvable(self) -> None:
        """
        Raise for still included <include> statements as not resolvable.
        The KIWI XSLT processing replaces the specified include
        directive(s) with the given file reference(s). If this action
        did not happen for example on nested includes, it can happen
        that they stay in the document as sort of waste.
        """
        message = dedent('''\n
            One ore more <include> statements are unresolvable

            The following include references could not be resolved.
            Please verify the specified location(s) and/or delete
            the broken include directive(s) from the description.
            Please also note, nested includes from other include
            files are not supported:

            {0}
        ''')
        include_files = \
            self.xml_state.get_include_section_reference_file_names()
        if include_files:
            raise KiwiRuntimeError(
                message.format(json.dumps(include_files, indent=4))
            )

    def check_image_include_repos_publicly_resolvable(self) -> None:
        """
        Verify that all repos marked with the imageinclude attribute
        can be resolved into a http based web URL
        """
        message = dedent('''\n
            The use of imageinclude="true" in the repository definition
            for the Repository: {0}
            requires the repository to by publicly available. The source
            locator of the repository however indicates it is private to
            your local system. Therefore it can't be included into the
            system image repository configuration. Please define a publicly
            available repository in your image XML description.
        ''')

        repository_sections = self.xml_state.get_repository_sections()
        for xml_repo in repository_sections:
            repo_marked_for_image_include = xml_repo.get_imageinclude()

            if repo_marked_for_image_include:
                repo_source = xml_repo.get_source().get_path()
                repo_type = xml_repo.get_type()
                uri = Uri(repo_source, repo_type)
                if not uri.is_public():
                    raise KiwiRuntimeError(
                        message.format(repo_source)
                    )

    @staticmethod
    def check_target_directory_not_in_shared_cache(target_dir: str) -> None:
        """
        The target directory must be outside of the kiwi shared cache
        directory in order to avoid busy mounts because kiwi bind mounts
        the cache directory into the image root tree to access host
        caching information

        :param string target_dir: path name
        """
        message = dedent('''\n
            Target directory %s conflicts with kiwi's shared cache
            directory %s. This is going to create a busy loop mount.
            Please choose another target directory.
        ''')

        shared_cache_location = Defaults.get_shared_cache_location()

        target_dir_stack = os.path.abspath(
            os.path.normpath(target_dir)
        ).replace(os.sep + os.sep, os.sep).split(os.sep)
        if target_dir_stack[1:4] == shared_cache_location.split(os.sep):
            raise KiwiRuntimeError(
                message % (target_dir, shared_cache_location)
            )

    def check_volume_label_used_with_lvm(self) -> None:
        """
        The optional volume label in a systemdisk setup is only
        effective if the LVM, logical volume manager system is
        used. In any other case where the filesystem itself offers
        volume management capabilities there are no extra filesystem
        labels which can be applied per volume
        """
        message = dedent('''\n
            Custom volume label setup used without LVM

            The optional volume label in a systemdisk setup is only
            effective if the LVM, logical volume manager system is
            used. Your setup uses the {0} filesystem which itself
            offers volume management capabilities. Extra filesystem
            labels cannot be applied in this case.

            If you want to force LVM over the {0} volume management
            system you can do so by specifying the following in
            your KIWI XML description:

            <systemdisk ... preferlvm="true">
                <volume .../>
            </systemdisk>
        ''')
        volume_management = self.xml_state.get_volume_management()
        if volume_management != 'lvm':
            for volume in self.xml_state.get_volumes():
                if volume.label and volume.label != 'SWAP':
                    raise KiwiRuntimeError(
                        message.format(volume_management)
                    )

    def check_partuuid_persistency_type_used_with_mbr(self) -> None:
        """
        The devicepersistency setting by-partuuid can only be
        used in combination with a partition table type that
        supports UUIDs. In any other case Linux creates artificial
        values for PTUUID and PARTUUID from the disk signature
        which can change without touching the actual partition
        table. We consider this unsafe and only allow the use
        of by-partuuid in combination with partition tables that
        actually supports it properly.
        """
        message = dedent('''\n
            devicepersistency={0!r} used with non UUID capable partition table

            PTUUID and PARTUUID exists in the GUID (GPT) partition table.
            According to the firmware setting: {1!r}, the selected partition
            table type is: {2!r}. This table type does not natively support
            UUIDs. In such a case Linux creates artificial values for PTUUID
            and PARTUUID from the disk signature which can change without
            touching the actual partition table. This is considered unsafe
            and KIWI only allows the use of by-partuuid in combination with
            partition tables that actually supports UUIDs properly.

            Please make sure to use one of the following firmware settings
            which leads to an image using an UUID capable partition table
            and therefore supporting consistent by-partuuid device names:

            <type ... firmware="efi|uefi">
        ''')
        persistency_type = self.xml_state.build_type.get_devicepersistency()
        if persistency_type and persistency_type == 'by-partuuid':
            supported_table_types = ['gpt']
            firmware = FirmWare(self.xml_state)
            table_type = firmware.get_partition_table_type()
            if table_type not in supported_table_types:
                raise KiwiRuntimeError(
                    message.format(
                        persistency_type, firmware.firmware, table_type
                    )
                )

    def check_swap_name_used_with_lvm(self) -> None:
        """
        The optional oem-swapname is only effective if used together
        with the LVM volume manager. A name for the swap space can
        only be set if it is created as a LVM volume. In any other
        case the name does not apply to the system
        """
        message = dedent('''\n
             Specified swap space name: {0} will not be used

             The specified oem-swapname is used without the LVM volume
             manager. This means the swap space will be created as simple
             partition for which no name assignment can take place.
             The name specified in oem-swapname is used to give the
             LVM swap volume a name. Outside of LVM the setting is
             meaningless and should be removed.

             Please delete the following setting from your image
             description:

             <oem-swapname>{0}</oem-swapname>
        ''')
        volume_management = self.xml_state.get_volume_management()
        if volume_management != 'lvm':
            oemconfig = self.xml_state.get_build_type_oemconfig_section()
            if oemconfig and oemconfig.get_oem_swapname():
                raise KiwiRuntimeError(
                    message.format(oemconfig.get_oem_swapname()[0])
                )

    def check_volume_setup_defines_reserved_labels(self) -> None:
        message = dedent('''\n
            Reserved label name used in LVM volume setup

            The label setup for volume {0} uses the reserved label {1}.
            Reserved labels used by KIWI internally are {2}. Please
            choose another label name for this volume.
        ''')
        reserved_labels = [
            self.xml_state.build_type.get_rootfs_label() or 'ROOT',
            'SWAP', 'SPARE'
        ]
        volume_management = self.xml_state.get_volume_management()
        if volume_management == 'lvm':
            for volume in self.xml_state.get_volumes():
                # A swap volume is created implicitly if oem-swap is
                # requested. This volume detected via realpath set to
                # swap is skipped from the reserved label check as it
                # intentionally uses the reserved label named SWAP
                if volume.realpath != 'swap':
                    if volume.label and volume.label in reserved_labels:
                        raise KiwiRuntimeError(
                            message.format(
                                volume.name, volume.label, reserved_labels
                            )
                        )

    def check_volume_setup_defines_multiple_fullsize_volumes(self) -> None:
        """
        The volume size specification 'all' makes this volume to
        take the rest space available on the system. It's only
        allowed to specify one all size volume
        """
        message = dedent('''\n
            Multiple all size volumes found but only one is allowed

            The volume size specification 'all' makes this volume to
            take the rest space available on the system. It's only
            allowed to specify one all size volume
        ''')
        systemdisk_section = self.xml_state.get_build_type_system_disk_section()
        if systemdisk_section:
            all_size_volume_count = 0
            volumes = systemdisk_section.get_volume() or []
            for volume in volumes:
                size = volume.get_size() or volume.get_freespace()
                if size and 'all' in size:
                    all_size_volume_count += 1
            if all_size_volume_count > 1:
                raise KiwiRuntimeError(message)

    def check_volume_setup_has_no_root_definition(self) -> None:
        """
        The root volume in a systemdisk setup is handled in a special
        way. It is not allowed to setup a custom name or mountpoint for
        the root volume. Therefore the size of the root volume can be
        setup via the @root volume name. This check looks up the volume
        setup and searches if there is a configuration for the '/'
        mountpoint which would cause the image build to fail
        """
        message = dedent('''\n
            Volume setup for "/" found. The size of the root volume
            must be specified via the @root volume name like the
            following example shows:

            <volume name="@root" size="42G"/>

            A custom name or mountpoint for the root volume is not
            allowed.
        ''')
        for volume in self.xml_state.get_volumes():
            if volume.mountpoint == '/':
                raise KiwiRuntimeError(message)

    def check_container_tool_chain_installed(self) -> None:
        """
        When creating container images the specific tools are used in order
        to import and export OCI or Docker compatible images. This check
        searches for those tools to be installed in the build system and
        fails if it can't find them
        """
        message_tool_not_found = dedent('''\n
            Required tool {name} not found in caller environment

            Creation of OCI or Docker images requires the tools {name} and
            skopeo to be installed on the build system. For SUSE based systems
            you can find the tools at:

            http://download.opensuse.org/repositories/Virtualization:/containers
        ''')
        message_version_unsupported = dedent('''\n
            {name} tool found with unknown version
        ''')
        message_unknown_tool = dedent('''\n
            Unknown tool: {0}.

            Please configure KIWI with an appropriate value (umoci or buildah).
            Consider this runtime configuration file syntax (/etc/kiwi.yml):

            oci:
                - archive_tool: umoci | buildah
        ''')

        expected_version = (0, 1, 0)

        if self.xml_state.get_build_type_name() in ['docker', 'oci']:
            runtime_config = RuntimeConfig()
            tool_name = runtime_config.get_oci_archive_tool()
            if tool_name == 'buildah':
                oci_tools = ['buildah', 'skopeo']
            elif tool_name == 'umoci':
                oci_tools = ['umoci', 'skopeo']
            else:
                raise KiwiRuntimeError(message_unknown_tool.format(tool_name))
            for tool in oci_tools:
                if not Path.which(filename=tool, access_mode=os.X_OK):
                    raise KiwiRuntimeError(
                        message_tool_not_found.format(name=tool)
                    )
                elif not CommandCapabilities.check_version(
                    tool, expected_version, raise_on_error=False
                ):
                    raise KiwiRuntimeError(
                        message_version_unsupported.format(name=tool)
                    )
            self._check_multitag_support()

    def _check_multitag_support(self) -> None:
        message = dedent('''\n
            Using additionaltags attribute requires skopeo tool to be
            capable to handle it, it must include the '--additional-tag'
            option for copy subcommand (check it running 'skopeo copy
            --help').\n
            It is known to be present since v0.1.30
        ''')
        if 'additional_names' in self.xml_state.get_container_config():
            if not CommandCapabilities.has_option_in_help(
                'skopeo', '--additional-tag', ['copy', '--help'],
                raise_on_error=False
            ):
                raise KiwiRuntimeError(message)

    def check_luksformat_options_valid(self) -> None:
        """
        Options set via the luksformat element are passed along
        to the cryptsetup tool. Only options that are known to
        the tool should be allowed. Thus this runtime check looks
        up the provided option names if they exist in the cryptsetup
        version used on the build host
        """
        message = dedent('''\n
            Option {0!r} not found in cryptsetup

            The Option {0!r} could not be found in the help output
            of the cryptsetup tool.
        ''')
        luksformat = self.xml_state.build_type.get_luksformat()
        if luksformat:
            for option in luksformat[0].get_option():
                argument = option.get_name()
                if not CommandCapabilities.has_option_in_help(
                    'cryptsetup', argument, ['--help'],
                    raise_on_error=False
                ):
                    raise KiwiRuntimeError(message.format(argument))

    def check_appx_naming_conventions_valid(self) -> None:
        """
        When building wsl images there are some naming conventions that
        must be fulfilled to run the container on Microsoft Windows
        """
        launcher_pattern = r'[^\\]+(\.[Ee][Xx][Ee])$'
        message_container_launcher_invalid = dedent('''\n
            Invalid WSL launcher name: {0}

            WSL launcher name must match the pattern: {1}
        ''')
        id_pattern = r'^[a-zA-Z0-9]+$'
        message_container_id_invalid = dedent('''\n
            Invalid WSL container application id: {0}

            WSL container id must match the pattern: {1}
        ''')
        build_type = self.xml_state.get_build_type_name()
        container_config = self.xml_state.get_container_config()
        container_history = container_config.get('history') or {}
        if build_type == 'appx' and container_config:
            launcher = container_history.get('launcher')
            if launcher and not re.match(launcher_pattern, launcher):
                raise KiwiRuntimeError(
                    message_container_launcher_invalid.format(
                        launcher, launcher_pattern
                    )
                )
            application_id = container_history.get('application_id')
            if application_id and not re.match(id_pattern, application_id):
                raise KiwiRuntimeError(
                    message_container_id_invalid.format(
                        application_id, id_pattern
                    )
                )

    def check_initrd_selection_required(self) -> None:
        """
        If the boot attribute is used without selecting kiwi
        as the initrd_system, the setting of the boot attribute
        will not have any effect. We assume that configurations
        which explicitly specify the boot attribute wants to use
        the custom kiwi initrd system and not dracut.
        """
        message_kiwi_initrd_system_not_selected = dedent('''\n
            Missing initrd_system selection for boot attribute

            The selected boot="'{0}'" boot description indicates
            the custom kiwi initrd system should be used instead
            of dracut. If this is correct please explicitly request
            the kiwi initrd system as follows:

            <type initrd_system="kiwi"/>

            If this is not want you want and dracut should be used
            as initrd system, please delete the boot attribute
            as it is obsolete in this case.
        ''')
        initrd_system = self.xml_state.get_initrd_system()
        boot_image_reference = self.xml_state.build_type.get_boot()
        if initrd_system != 'kiwi' and boot_image_reference:
            raise KiwiRuntimeError(
                message_kiwi_initrd_system_not_selected.format(
                    boot_image_reference
                )
            )

    def check_boot_description_exists(self) -> None:
        """
        If a kiwi initrd is used, a lookup to the specified boot
        description is done and fails early if it does not exist
        """
        message_no_boot_reference = dedent('''\n
            Boot description missing for '{0}' type

            The selected '{1}' initrd_system requires a boot description
            reference. Please update your type setup as follows

            <type image="{0}" boot="{0}boot/..."/>

            A collection of custom boot descriptions can be found
            in the kiwi-boot-descriptions package
        ''')
        message_boot_description_not_found = dedent('''\n
            Boot description '{0}' not found

            The selected boot description could not be found on
            the build host. A collection of custom boot descriptions
            can be found in the kiwi-boot-descriptions package
        ''')
        image_types_supporting_custom_boot_description = ['oem', 'pxe']
        build_type = self.xml_state.get_build_type_name()
        initrd_system = self.xml_state.get_initrd_system()
        if initrd_system == 'kiwi' and \
           build_type in image_types_supporting_custom_boot_description:

            boot_image_reference = self.xml_state.build_type.get_boot()
            if not boot_image_reference:
                raise KiwiRuntimeError(
                    message_no_boot_reference.format(build_type, initrd_system)
                )

            if not boot_image_reference[0] == os.sep:
                boot_image_reference = os.sep.join(
                    [
                        Defaults.get_boot_image_description_path(),
                        boot_image_reference
                    ]
                )
            if not os.path.exists(boot_image_reference):
                raise KiwiRuntimeError(
                    message_boot_description_not_found.format(
                        boot_image_reference
                    )
                )

    def check_consistent_kernel_in_boot_and_system_image(self) -> None:
        """
        If a kiwi initrd is used, the kernel used to build the kiwi
        initrd and the kernel used in the system image must be the
        same in order to avoid an inconsistent boot setup
        """
        message = dedent('''\n
            Possible kernel mismatch between kiwi initrd and system image

            The selected '{0}' boot image kernel is '{1}'. However this
            kernel package was not explicitly listed in the package list
            of the system image. Please fixup your system image
            description:

            1) Add <package name="{1}"/> to your system XML description

            2) Inherit kernel from system description to initrd via
               the custom kernel profile:

               <type ... bootkernel="custom" .../>

               <packages type="image"/>
                   <package name="desired-kernel" bootinclude="true"/>
               </packages>
        ''')
        boot_image_reference = self.xml_state.build_type.get_boot()
        boot_kernel_package_name = None
        if boot_image_reference:
            if not boot_image_reference[0] == '/':
                boot_image_reference = os.sep.join(
                    [
                        Defaults.get_boot_image_description_path(),
                        boot_image_reference
                    ]
                )
            boot_config_file = os.sep.join(
                [boot_image_reference, 'config.xml']
            )
            if os.path.exists(boot_config_file):
                boot_description = XMLDescription(
                    description=boot_config_file,
                    derived_from=self.xml_state.xml_data.description_dir
                )
                boot_kernel_profile = \
                    self.xml_state.build_type.get_bootkernel()
                if not boot_kernel_profile:
                    boot_kernel_profile = 'std'
                boot_xml_state = XMLState(
                    boot_description.load(), [boot_kernel_profile]
                )
                kernel_package_sections = []
                for packages_section in boot_xml_state.xml_data.get_packages():
                    # lookup package sections matching kernel profile in kiwi
                    # boot description. By definition this must be a packages
                    # section with a single profile name whereas the default
                    # profile name is 'std'. The section itself must contain
                    # one matching kernel package name for the desired
                    # architecture
                    if packages_section.get_profiles() == boot_kernel_profile:
                        for package in packages_section.get_package():
                            kernel_package_sections.append(package)

                for package in kernel_package_sections:
                    if boot_xml_state.package_matches_host_architecture(
                            package
                    ):
                        boot_kernel_package_name = package.get_name()

        if boot_kernel_package_name:
            # A kernel package name was found in the kiwi boot image
            # description. Let's check if this kernel is also used
            # in the system image
            image_package_names = self.xml_state.get_system_packages()
            if boot_kernel_package_name not in image_package_names:
                raise KiwiRuntimeError(
                    message.format(
                        self.xml_state.build_type.get_boot(),
                        boot_kernel_package_name
                    )
                )

    def check_dracut_module_versions_compatible_to_kiwi(
        self, root_dir: str
    ) -> None:
        """
        KIWI images which makes use of kiwi dracut modules
        has to use module versions compatible with the version
        of this KIWI builder code base. This is important to avoid
        inconsistencies between the way how kiwi includes its own
        dracut modules and former version of those dracut modules
        which could be no longer compatible with the builder.
        Therefore this runtime check maintains a min_version constraint
        for which we know this KIWI builder to be compatible with.
        """
        message = dedent('''\n
            Incompatible dracut-kiwi module(s) found

            The image was build with KIWI version={0}. The system
            root tree has the following dracut-kiwi-* module packages
            installed which are too old to work with this version of KIWI.
            Please make sure to use dracut-kiwi-* module packages
            which are >= than the versions listed below.

            {1}
        ''')
        kiwi_dracut_modules = {
            '90kiwi-dump': dracut_module_type(
                'dracut-kiwi-oem-dump', '9.20.1'
            ),
            '90kiwi-live': dracut_module_type(
                'dracut-kiwi-live', '9.20.1'
            ),
            '90kiwi-overlay': dracut_module_type(
                'dracut-kiwi-overlay', '9.20.1'
            ),
            '90kiwi-repart': dracut_module_type(
                'dracut-kiwi-oem-repart', '9.20.1'
            ),
            '99kiwi-dump-reboot': dracut_module_type(
                'dracut-kiwi-oem-dump', '9.20.1'
            ),
            '99kiwi-lib': dracut_module_type(
                'dracut-kiwi-lib', '9.20.1'
            )
        }
        dracut_module_dir = os.sep.join(
            [root_dir, '/usr/lib/dracut/modules.d']
        )
        if not os.path.isdir(dracut_module_dir):
            # no dracut module dir present
            return

        incompatible_modules = {}
        for module in os.listdir(dracut_module_dir):
            module_meta = kiwi_dracut_modules.get(module)
            if module_meta:
                module_version = self._get_dracut_module_version_from_pdb(
                    self.xml_state.get_package_manager(),
                    module_meta.package, root_dir
                )
                if module_version:
                    module_version_nr = tuple(
                        int(it) for it in module_version.split('.')
                    )
                    module_min_version_nr = tuple(
                        int(it) for it in module_meta.min_version.split('.')
                    )
                    if module_version_nr < module_min_version_nr:
                        incompatible_modules[
                            module_meta.package
                        ] = 'got:{0}, need:>={1}'.format(
                            module_version, module_meta.min_version
                        )
        if incompatible_modules:
            raise KiwiRuntimeError(
                message.format(__version__, incompatible_modules)
            )

    def check_dracut_module_for_oem_install_in_package_list(self) -> None:
        """
        OEM images if configured to use dracut as initrd system
        and configured with one of the installiso, installstick
        or installpxe attributes requires the KIWI provided
        dracut-kiwi-oem-dump module to be installed at the time
        dracut is called. Thus this runtime check examines if the
        required package is part of the package list in the
        image description.
        """
        message = dedent('''\n
            Required dracut module package missing in package list

            One of the packages '{0}' is required
            to build an installation image for the selected oem image type.
            Depending on your distribution, add the following in the
            <packages type="image"> section:

            <package name="ONE_FROM_ABOVE"/>
        ''')
        meta = Defaults.get_runtime_checker_metadata()
        required_dracut_packages = meta['package_names']['dracut_oem_dump']
        initrd_system = self.xml_state.get_initrd_system()
        build_type = self.xml_state.get_build_type_name()
        if build_type == 'oem' and initrd_system == 'dracut':
            install_iso = self.xml_state.build_type.get_installiso()
            install_stick = self.xml_state.build_type.get_installstick()
            install_pxe = self.xml_state.build_type.get_installpxe()
            if install_iso or install_stick or install_pxe:
                package_names = \
                    self.xml_state.get_bootstrap_packages() + \
                    self.xml_state.get_system_packages()
                if not RuntimeChecker._package_in_list(
                    package_names, required_dracut_packages
                ):
                    raise KiwiRuntimeError(
                        message.format(required_dracut_packages)
                    )

    def check_dracut_module_for_disk_oem_in_package_list(self) -> None:
        """
        OEM images if configured to use dracut as initrd system
        requires the KIWI provided dracut-kiwi-oem-repart module
        to be installed at the time dracut is called. Thus this
        runtime check examines if the required package is part of
        the package list in the image description.
        """
        message = dedent('''\n
            Required dracut module package missing in package list

            One of the packages '{0}' is required
            for the selected oem image type. Depending on your distribution,
            add the following in the <packages type="image"> section:

            <package name="ONE_FROM_ABOVE"/>
        ''')
        meta = Defaults.get_runtime_checker_metadata()
        required_dracut_packages = meta['package_names']['dracut_oem_repart']
        initrd_system = self.xml_state.get_initrd_system()
        disk_resize_requested = self.xml_state.get_oemconfig_oem_resize()
        build_type = self.xml_state.get_build_type_name()
        if build_type == 'oem' and initrd_system == 'dracut' and \
           disk_resize_requested:
            package_names = \
                self.xml_state.get_bootstrap_packages() + \
                self.xml_state.get_system_packages()
            if not RuntimeChecker._package_in_list(
                package_names, required_dracut_packages
            ):
                raise KiwiRuntimeError(
                    message.format(required_dracut_packages)
                )

    def check_dracut_module_for_live_iso_in_package_list(self) -> None:
        """
        Live ISO images uses a dracut initrd to boot and requires
        the KIWI provided kiwi-live dracut module to be installed
        at the time dracut is called. Thus this runtime check
        examines if the required package is part of the package
        list in the image description.
        """
        message = dedent('''\n
            Required dracut module package missing in package list

            One of the packages '{0}' is required
            for the selected live iso image type. Depending on your distribution,
            add the following in your <packages type="image"> section:

            <package name="ONE_FROM_ABOVE"/>
        ''')
        meta = Defaults.get_runtime_checker_metadata()
        required_dracut_packages = meta['package_names']['dracut_live']
        type_name = self.xml_state.get_build_type_name()
        type_flag = self.xml_state.build_type.get_flags()
        if type_name == 'iso' and type_flag != 'dmsquash':
            package_names = \
                self.xml_state.get_bootstrap_packages() + \
                self.xml_state.get_system_packages()
            if not RuntimeChecker._package_in_list(
                package_names, required_dracut_packages
            ):
                raise KiwiRuntimeError(
                    message.format(required_dracut_packages)
                )

    def check_dracut_module_for_disk_overlay_in_package_list(self) -> None:
        """
        Disk images configured to use a root filesystem overlay
        requires the KIWI provided kiwi-overlay dracut module to
        be installed at the time dracut is called. Thus this
        runtime check examines if the required package is part of
        the package list in the image description.
        """
        message = dedent('''\n
            Required dracut module package missing in package list

            The package '{0}' is required
            for the selected overlayroot activated image type.
            Depending on your distribution, add the following in your
            <packages type="image"> section:

            <package name="ONE_FROM_ABOVE"/>
        ''')
        initrd_system = self.xml_state.get_initrd_system()
        meta = Defaults.get_runtime_checker_metadata()
        required_dracut_packages = meta['package_names']['dracut_overlay']
        if initrd_system == 'dracut' and \
           self.xml_state.build_type.get_overlayroot():
            package_names = \
                self.xml_state.get_bootstrap_packages() + \
                self.xml_state.get_system_packages()
            if not RuntimeChecker._package_in_list(
                package_names, required_dracut_packages
            ):
                raise KiwiRuntimeError(
                    message.format(required_dracut_packages)
                )

    def check_efi_mode_for_disk_overlay_correctly_setup(self) -> None:
        """
        Disk images configured to use a root filesystem overlay
        only supports the standard EFI mode and not secure boot.
        That's because the shim setup performs changes to the
        root filesystem which can not be applied during the
        bootloader setup at build time because at that point
        the root filesystem is a read-only squashfs source.
        """
        message = dedent('''\n
            Secure Boot not supported with overlay disk image

            Disk images configured to use a root filesystem overlay
            only supports the standard EFI mode and not secure boot.
            That's because the shim setup performs changes to the
            root filesystem which can not be applied during the
            bootloader setup at build time because at that point
            the root filesystem is a read-only squashfs source

            Thus please change the firmware attribute in the <type>
            section of the system XML description as follows:

            <type ... firmware="efi"/>
        ''')
        overlayroot = self.xml_state.build_type.get_overlayroot()
        firmware = self.xml_state.build_type.get_firmware()
        if overlayroot and firmware == 'uefi':
            raise KiwiRuntimeError(message)

    def check_xen_uniquely_setup_as_server_or_guest(self) -> None:
        """
        If the image is classified to be used as Xen image, it can
        be either a Xen Server(dom0) or a Xen guest. The image
        configuration is checked if the information uniquely identifies
        the image as such
        """
        xen_message = dedent('''\n
            Inconsistent Xen setup found:

            The use of the 'xen_server' or 'xen_loader' attributes indicates
            the target system for this image is Xen. However the image
            specifies both attributes at the same time which classifies
            the image to be both, a Xen Server(dom0) and a Xen guest at
            the same time, which is not supported.

            Please cleanup your image description. Setup only one
            of 'xen_server' or 'xen_loader'.
        ''')
        ec2_message = dedent('''\n
            Inconsistent Amazon EC2 setup found:

            The firmware setup indicates the target system for this image
            is Amazon EC2, which uses a Xen based virtualisation technology.
            Therefore the image must be classified as a Xen guest and can
            not be a Xen server as indicated by the 'xen_server' attribute

            Please cleanup your image description. Delete the 'xen_server'
            attribute for images used with Amazon EC2.
        ''')
        if self.xml_state.is_xen_server() and self.xml_state.is_xen_guest():
            firmware = self.xml_state.build_type.get_firmware()
            ec2_firmware_names = Defaults.get_ec2_capable_firmware_names()
            if firmware and firmware in ec2_firmware_names:
                raise KiwiRuntimeError(ec2_message)
            else:
                raise KiwiRuntimeError(xen_message)

    def check_mediacheck_installed(self) -> None:
        """
        If the image description enables the mediacheck attribute
        the required tools to run this check must be installed
        on the image build host
        """
        message_tool_not_found = dedent('''\n
            Required tool {name} not found in caller environment

            The attribute 'mediacheck' is set to 'true' which requires
            the above tool to be installed on the build system
        ''')
        if self.xml_state.build_type.get_mediacheck() is True:
            tool = 'tagmedia'
            media_tagger = RuntimeConfig().get_iso_media_tag_tool()
            if media_tagger == 'checkmedia':
                tool = 'tagmedia'
            elif media_tagger == 'isomd5sum':
                tool = 'implantisomd5'
            if not Path.which(filename=tool, access_mode=os.X_OK):
                raise KiwiRuntimeError(
                    message_tool_not_found.format(name=tool)
                )

    def check_image_version_provided(self) -> None:
        """
        Kiwi requires a <version> element to be specified as part
        of at least one <preferences> section.
        """
        message_missing_version = dedent('''\n
            No version is defined in any of the <preferences>
            sections. Please add

                <version>image_version<version/>

            inside the <preferences> section.
        ''')

        if not self.xml_state.get_image_version():
            raise KiwiRuntimeError(message_missing_version)

    def check_image_type_unique(self) -> None:
        """
        Verify that the selected image type is unique within
        the range of the configured types and profiles.
        """
        message = dedent('''\n
            Conflicting image type setup detected

            The selected image type '{0}' in the {1} profile
            selection is not unique. There are the followng type
            settings which overrides each other:
            {2}
            To solve this conflict please move the image type
            setup into its own profile and select them using
            the --profile option at call time.
        ''')
        image_type_sections = []
        type_dict: Dict[str, List[Any]] = {}
        for preferences in self.xml_state.get_preferences_sections():
            image_type_sections += preferences.get_type()

        for image_type in image_type_sections:
            type_name = image_type.get_image()
            if type_dict.get(type_name):
                type_dict[type_name].append(image_type)
            else:
                type_dict[type_name] = [image_type]

        for type_name, type_list in list(type_dict.items()):
            if len(type_list) > 1:
                type_export = StringIO()
                for image_type in type_list:
                    type_export.write(os.linesep)
                    image_type.export(type_export, 0)
                raise KiwiRuntimeError(
                    message.format(
                        type_name, self.xml_state.profiles or ['Default'],
                        type_export.getvalue()
                    )
                )

    def check_efi_fat_image_has_correct_size(self) -> None:
        """
        Verify that the efifatimagesize does not exceed the max
        El Torito load size of 65535 * 512 bytes
        """
        message = dedent('''\n
            El Torito max load size exceeded

            The configured efifatimagesize of '{0}MB' exceeds
            the El Torito max load size of 65535 * 512 bytes (~31MB).
        ''')
        fat_image_mbsize = int(
            self.xml_state.build_type
                .get_efifatimagesize() or defaults.EFI_FAT_IMAGE_SIZE
        )
        if fat_image_mbsize > 31:
            raise KiwiRuntimeError(
                message.format(fat_image_mbsize)
            )

    @staticmethod
    def _package_in_list(
        package_list: List[str], search_list: List[str]
    ) -> str:
        result = ''
        for search in search_list:
            if search in package_list:
                result = search
                break
        return result

    @staticmethod
    def _get_dracut_module_version_from_pdb(
        package_manager: str, package_name: str, root_dir: str
    ) -> str:
        tool = Defaults.get_default_packager_tool(package_manager)
        package_query = None
        package_manager_query = None
        package_version = ''
        if tool == 'rpm':
            package_manager_query = [
                'chroot', root_dir, tool, '-q', '--qf',
                '%{VERSION}', package_name
            ]
        elif tool == 'dpkg':
            package_manager_query = [
                'chroot', root_dir, 'dpkg-query', '-W', '-f',
                '${Version}', package_name
            ]
        if package_manager_query:
            try:
                package_query = Command.run(package_manager_query)
                if package_query:
                    package_version = package_query.output.split('-', 1)[0]
            except Exception as issue:
                log.debug(f'Package manager query failed with: {issue}')
        return package_version
