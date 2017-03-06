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
from textwrap import dedent

# project
from .xml_description import XMLDescription
from .xml_state import XMLState
from .system.uri import Uri
from .defaults import Defaults
from .path import Path
from .exceptions import (
    KiwiRuntimeError
)


class RuntimeChecker(object):
    """
    Implements build consistency checks at runtime

    The schema of an image description covers structure and syntax of
    the provided data. The RuntimeChecker provides methods to perform
    further semantic checks which allows to recognize potential build
    or boot problems early.

    * :attr:`xml_state`
        Instance of XMLState
    """
    def __init__(self, xml_state):
        self.xml_state = xml_state

    def check_repositories_configured(self):
        """
        Verify that that there are repositories configured
        """
        if not self.xml_state.get_repository_sections():
            raise KiwiRuntimeError(
                'No repositories configured'
            )

    def check_image_include_repos_http_resolvable(self):
        """
        Verify that all repos marked with the imageinclude attribute
        can be resolved into a http based web URL
        """

        message = dedent('''\n
            Repository: %s is not publicly available.
            Therefore it can't be included into the system image
            repository configuration. Please check the setup of
            the <imageinclude> attribute for this repository.
        ''')

        repository_sections = self.xml_state.get_repository_sections()
        for xml_repo in repository_sections:
            repo_marked_for_image_include = xml_repo.get_imageinclude()

            if repo_marked_for_image_include:
                repo_source = xml_repo.get_source().get_path()
                repo_type = xml_repo.get_type()
                uri = Uri(repo_source, repo_type)
                if not uri.is_remote() or Defaults.is_obs_worker():
                    raise KiwiRuntimeError(message % repo_source)

    def check_target_directory_not_in_shared_cache(self, target_dir):
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
        absolute_target_dir = os.path.abspath(
            os.path.normpath(target_dir)
        ).replace('//', '/')
        if absolute_target_dir.startswith('/' + shared_cache_location):
            raise KiwiRuntimeError(
                message % (target_dir, shared_cache_location)
            )

    def check_volume_setup_has_no_root_definition(self):
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

    def check_docker_tool_chain_installed(self):
        """
        When creating docker images the tools umoci and skopeo are used
        in order to create docker compatible images. This check searches
        for those tools to be installed in the build system and fails if
        it can't find them
        """
        message = dedent('''\n
            Required tool {0} not found in caller environment

            Creation of docker images requires the tools umoci and skopeo
            to be installed on the build system. For SUSE based systems
            you can find the tools at:

            http://download.opensuse.org/repositories/Virtualization:/containers
        ''')
        if self.xml_state.get_build_type_name() == 'docker':
            for tool in ['umoci', 'skopeo']:
                if not Path.which(filename=tool, access_mode=os.X_OK):
                    raise KiwiRuntimeError(message.format(tool))

    def check_consistent_kernel_in_boot_and_system_image(self):
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
                    if boot_xml_state.package_matches_host_architecture(package):
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

    def check_boot_image_reference_correctly_setup(self):
        """
        If an initrd_system different from "kiwi" is selected for a
        vmx (simple disk) image build, it does not make sense to setup
        a reference to a kiwi boot image description, because no kiwi
        boot image will be built.
        """
        message = dedent('''\n
            Selected initrd_system is: {0}

            The boot attribute selected: '{1}' which is an initrd image
            used for the 'kiwi' initrd system. This boot image will not be
            used according to the selected initrd system. Please cleanup
            your image description:

            1) If the selected initrd system is correct, delete the
               obsolete boot attribute from the selected '{2}' build type

            2) If the kiwi initrd image should be used, make sure to
               set initrd_system="kiwi"
        ''')
        build_type_name = self.xml_state.get_build_type_name()
        boot_image_reference = self.xml_state.build_type.get_boot()
        if build_type_name == 'vmx' and boot_image_reference:
            initrd_system = self.xml_state.build_type.get_initrd_system()
            if initrd_system and initrd_system == 'dracut':
                raise KiwiRuntimeError(
                    message.format(
                        initrd_system, boot_image_reference, build_type_name
                    )
                )
