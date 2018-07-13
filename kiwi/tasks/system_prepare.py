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
"""
usage: kiwi system prepare -h | --help
       kiwi system prepare --description=<directory> --root=<directory>
           [--allow-existing-root]
           [--clear-cache]
           [--ignore-repos]
           [--ignore-repos-used-for-build]
           [--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>]
           [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>...]
           [--add-package=<name>...]
           [--delete-package=<name>...]
           [--set-container-derived-from=<uri>]
           [--set-container-tag=<name>]
           [--add-container-label=<label>...]
           [--signing-key=<key-file>...]
       kiwi system prepare help

commands:
    prepare
        prepare and install a new system for chroot access
    prepare help
        show manual page for prepare command

options:
    --add-package=<name>
        install the given package name
    --add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>
        add repository with given source, type, alias, priority,
        the imageinclude flag and the package_gpgcheck flag
    --allow-existing-root
        allow to use an existing root directory. Use with caution
        this could cause an inconsistent root tree if the existing
        contents does not fit to the additional installation
    --clear-cache
        delete repository cache for each of the used repositories
        before installing any package
    --delete-package=<name>
        delete the given package name
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --ignore-repos
        ignore all repos from the XML configuration
    --ignore-repos-used-for-build
        ignore all repos from the XML configuration except the
        ones marked as imageonly
    --root=<directory>
        the path to the new root directory of the system
    --set-container-derived-from=<uri>
        overwrite the source location of the base container
        for the selected image type. The setting is only effective
        if the configured image type is setup with an initial
        derived_from reference
    --set-container-tag=<name>
        overwrite the container tag in the container configuration.
        The setting is only effective if the container configuraiton
        provides an initial tag value
    --add-container-label=<name=value>
        add a container label in the container configuration metadata. It
        overwrites the label with the provided key-value pair in case it was
        already defined in the XML description
    --set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck>
        overwrite the first XML listed repository source, type, alias,
        priority, the imageinclude flag and the package_gpgcheck flag
     --signing-key=<key-file>
        includes the key-file as a trusted key for package manager validations
"""
import os

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.system.prepare import SystemPrepare
from kiwi.system.setup import SystemSetup
from kiwi.defaults import Defaults
from kiwi.system.profile import Profile
from kiwi.logger import log


class SystemPrepareTask(CliTask):
    """
    Implements preparation and installation of a new root system

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):                                      # noqa: C901
        """
        Prepare and install a new system for chroot access
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        self.load_xml_description(
            self.command_args['--description']
        )

        abs_root_path = os.path.abspath(self.command_args['--root'])

        self.runtime_checker.check_efi_mode_for_disk_overlay_correctly_setup()
        self.runtime_checker.check_grub_efi_installed_for_efi_firmware()
        self.runtime_checker.check_boot_description_exists()
        self.runtime_checker.check_consistent_kernel_in_boot_and_system_image()
        self.runtime_checker.check_docker_tool_chain_installed()
        self.runtime_checker.check_volume_setup_has_no_root_definition()
        self.runtime_checker.check_volume_label_used_with_lvm()
        self.runtime_checker.check_xen_uniquely_setup_as_server_or_guest()
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            abs_root_path
        )
        self.runtime_checker.check_mediacheck_only_for_x86_arch()
        self.runtime_checker.check_dracut_module_for_live_iso_in_package_list()
        self.runtime_checker.check_dracut_module_for_disk_overlay_in_package_list()
        self.runtime_checker.check_dracut_module_for_disk_oem_in_package_list()
        self.runtime_checker.check_dracut_module_for_oem_install_in_package_list()

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()
        elif self.command_args['--ignore-repos-used-for-build']:
            self.xml_state.delete_repository_sections_used_for_build()

        if self.command_args['--set-repo']:
            self.xml_state.set_repository(
                *self.sextuple_token(self.command_args['--set-repo'])
            )

        if self.command_args['--add-repo']:
            for add_repo in self.command_args['--add-repo']:
                self.xml_state.add_repository(
                    *self.sextuple_token(add_repo)
                )

        if self.command_args['--set-container-tag']:
            self.xml_state.set_container_config_tag(
                self.command_args['--set-container-tag']
            )

        if self.command_args['--add-container-label']:
            for add_label in self.command_args['--add-container-label']:
                try:
                    (name, value) = add_label.split('=', 1)
                    self.xml_state.add_container_config_label(name, value)
                except Exception:
                    log.warning(
                        'Container label {0} ignored. Invalid format: '
                        'expected labelname=value'.format(add_label)
                    )

        if self.command_args['--set-container-derived-from']:
            self.xml_state.set_derived_from_image_uri(
                self.command_args['--set-container-derived-from']
            )

        self.runtime_checker.check_repositories_configured()
        self.runtime_checker.check_image_include_repos_publicly_resolvable()

        log.info('Preparing system')
        system = SystemPrepare(
            self.xml_state,
            abs_root_path,
            self.command_args['--allow-existing-root']
        )
        manager = system.setup_repositories(
            self.command_args['--clear-cache'],
            self.command_args['--signing-key']
        )
        system.install_bootstrap(manager)
        system.install_system(
            manager
        )

        if self.command_args['--add-package']:
            system.install_packages(
                manager, self.command_args['--add-package']
            )
        if self.command_args['--delete-package']:
            system.delete_packages(
                manager, self.command_args['--delete-package']
            )

        profile = Profile(self.xml_state)

        defaults = Defaults()
        defaults.to_profile(profile)

        setup = SystemSetup(
            self.xml_state, abs_root_path
        )
        setup.import_shell_environment(profile)

        setup.import_description()
        setup.import_overlay_files()
        setup.import_image_identifier()
        setup.setup_groups()
        setup.setup_users()
        setup.setup_keyboard_map()
        setup.setup_locale()
        setup.setup_plymouth_splash()
        setup.setup_timezone()

        # make sure manager instance is cleaned up now
        del manager

        # setup permanent image repositories after cleanup
        setup.import_repositories_marked_as_imageinclude()
        setup.call_config_script()

        # handle uninstall package requests, gracefully uninstall
        # with dependency cleanup
        system.pinch_system(force=False)

        # handle delete package requests, forced uninstall without
        # any dependency resolution
        system.pinch_system(force=True)

        # make sure system instance is cleaned up now
        del system

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::prepare')
        else:
            return False
        return self.manual
