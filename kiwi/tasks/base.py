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
import logging
import glob
from operator import attrgetter

# project
from kiwi.cli import Cli
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.runtime_checker import RuntimeChecker
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiConfigFileNotFound
)

log = logging.getLogger('kiwi')


class CliTask:
    """
    Base class for all task classes, loads the task and provides
    the interface to the command options and the XML description

    Attributes

    * :attr:`should_perform_task_setup`
        Indicates if the task should perform the setup steps
        which covers the following task configurations:
        * setup debug level
        * setup logfile
        * setup color output
    """
    def __init__(self, should_perform_task_setup=True):
        self.cli = Cli()

        # initialize runtime checker
        self.runtime_checker = None

        # initialize runtime configuration
        self.runtime_config = RuntimeConfig()

        # help requested
        self.cli.show_and_exit_on_help_request()

        # load/import task module
        self.task = self.cli.load_command()

        # get command specific args
        self.command_args = self.cli.get_command_args()

        # get global args
        self.global_args = self.cli.get_global_args()

        # initialize generic runtime check dicts
        self.checks_before_command_args = {
            'check_image_version_provided': [],
            'check_efi_mode_for_disk_overlay_correctly_setup': [],
            'check_initrd_selection_required': [],
            'check_boot_description_exists': [],
            'check_consistent_kernel_in_boot_and_system_image': [],
            'check_container_tool_chain_installed': [],
            'check_volume_setup_defines_reserved_labels': [],
            'check_volume_setup_defines_multiple_fullsize_volumes': [],
            'check_volume_setup_has_no_root_definition': [],
            'check_volume_label_used_with_lvm': [],
            'check_swap_name_used_with_lvm': [],
            'check_xen_uniquely_setup_as_server_or_guest': [],
            'check_mediacheck_installed': [],
            'check_dracut_module_for_live_iso_in_package_list': [],
            'check_dracut_module_for_disk_overlay_in_package_list': [],
            'check_dracut_module_for_disk_oem_in_package_list': [],
            'check_dracut_module_for_oem_install_in_package_list': [],
            'check_architecture_supports_iso_firmware_setup': [],
            'check_appx_naming_conventions_valid': [],
            'check_syslinux_installed_if_isolinux_is_used': [],
            'check_image_type_unique': []
        }
        self.checks_after_command_args = {
            'check_repositories_configured': [],
            'check_image_include_repos_publicly_resolvable': []
        }

        if should_perform_task_setup:
            # set log level
            if self.global_args['--debug']:
                log.setLogLevel(logging.DEBUG)
            else:
                log.setLogLevel(logging.INFO)

            # set log file
            if self.global_args['--logfile']:
                log.set_logfile(
                    self.global_args['--logfile']
                )

            if self.global_args['--color-output']:
                log.set_color_format()

    def load_xml_description(self, description_directory):
        """
        Load, upgrade, validate XML description

        Attributes

        * :attr:`xml_data`
            instance of XML data toplevel domain (image), stateless data

        * :attr:`config_file`
            used config file path

        * :attr:`xml_state`
            Instance of XMLState, stateful data
        """
        log.info('Loading XML description')
        config_file = description_directory + '/config.xml'
        if not os.path.exists(config_file):
            # alternative config file lookup location
            config_file = description_directory + '/image/config.xml'
        if not os.path.exists(config_file):
            # glob config file search, first match wins
            glob_match = description_directory + '/*.kiwi'
            for kiwi_file in sorted(glob.iglob(glob_match)):
                config_file = kiwi_file
                break

        if not os.path.exists(config_file):
            raise KiwiConfigFileNotFound(
                'no XML description found in %s' % description_directory
            )

        self.description = XMLDescription(
            config_file
        )
        self.xml_data = self.description.load()
        self.config_file = config_file.replace('//', '/')
        self.xml_state = XMLState(
            self.xml_data,
            self.global_args['--profile'],
            self.global_args['--type']
        )

        log.info('--> loaded %s', self.config_file)
        if self.xml_state.build_type:
            log.info(
                '--> Selected build type: %s',
                self.xml_state.get_build_type_name()
            )
        if self.xml_state.profiles:
            log.info(
                '--> Selected profiles: %s',
                ','.join(self.xml_state.profiles)
            )

        self.runtime_checker = RuntimeChecker(self.xml_state)

    def quadruple_token(self, option):
        """
        Helper method for commandline options of the form --option a,b,c,d

        Make sure to provide a common result for option values which
        separates the information in a comma separated list of values

        :return: common option value representation
        :rtype: str
        """
        tokens = option.split(',', 3)
        return [
            self._pop_token(tokens) if len(tokens) else None for _ in range(
                0, 4
            )
        ]

    def sextuple_token(self, option):
        """
        Helper method for commandline options of the form --option a,b,c,d,e,f

        Make sure to provide a common result for option values which
        separates the information in a comma separated list of values

        :return: common option value representation
        :rtype: str
        """
        tokens = option.split(',', 5)
        return [
            self._pop_token(tokens) if len(tokens) else None for _ in range(
                0, 6
            )
        ]

    def run_checks(self, checks):
        """
        This method runs the given runtime checks excluding the ones disabled
        in the runtime configuration file.

        :param dict checks: A dictionary with the runtime method names as keys
            and their arguments list as the values.
        """
        exclude_list = self.runtime_config.get_disabled_runtime_checks()
        if self.runtime_checker is not None:
            for method, args in {
                key: value for key, value in checks.items()
                    if key not in exclude_list
            }.items():
                attrgetter(method)(self.runtime_checker)(*args)

    def _pop_token(self, tokens):
        token = tokens.pop(0)
        if len(token) > 0 and token == 'true':
            return True
        elif len(token) > 0 and token == 'false':
            return False
        else:
            return token
