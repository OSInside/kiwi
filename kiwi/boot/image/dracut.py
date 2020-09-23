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

# project
from kiwi.command import Command
from kiwi.system.kernel import Kernel
from kiwi.boot.image.base import BootImageBase
from kiwi.defaults import Defaults
from kiwi.system.profile import Profile
from kiwi.system.setup import SystemSetup

log = logging.getLogger('kiwi')


class BootImageDracut(BootImageBase):
    """
    **Implements creation of dracut boot(initrd) images.**
    """
    def post_init(self):
        """
        Post initialization method

        Initialize empty list of dracut caller options
        """
        # signing keys are only taken into account on install of
        # packages. As dracut runs from a pre defined root directory,
        # no signing keys will be used in the process of creating
        # an initrd with dracut
        self.signing_keys = None

        # Initialize empty list of dracut caller options
        self.dracut_options = []
        self.included_files = []
        self.included_files_install = []
        self.modules = []
        self.install_modules = []
        self.omit_modules = []
        self.omit_install_modules = []
        self.available_modules = self._get_modules()

    def include_file(self, filename, install_media=False):
        """
        Include file to dracut boot image

        :param string filename: file path name
        """
        self.included_files.append('--install')
        self.included_files.append(filename)
        if install_media:
            self.included_files_install.append('--install')
            self.included_files_install.append(filename)

    def include_module(self, module, install_media=False):
        """
        Include module to dracut boot image

        :param string module: module to include
        :param bool install_media: include the module for install initrds
        """
        warn_msg = 'module "{0}" not included in initrd'.format(module)
        if self._module_available(module):
            if install_media and module not in self.install_modules:
                self.install_modules.append(module)
            elif module not in self.modules:
                self.modules.append(module)
        else:
            log.warning(warn_msg)

    def omit_module(self, module, install_media=False):
        """
        Omit module to dracut boot image

        :param string module: module to omit
        :param bool install_media: omit the module for install initrds
        """
        if install_media and module not in self.omit_install_modules:
            self.omit_install_modules.append(module)
        elif module not in self.omit_modules:
            self.omit_modules.append(module)

    def write_system_config_file(self, config, config_file=None):
        """
        Writes modules configuration into a dracut configuration file.

        :param dict config: a dictionary containing the modules to add and omit
        :param string conf_file: configuration file to write
        """
        dracut_config = []
        if not config_file:
            config_file = os.path.normpath(
                self.boot_root_directory + Defaults.get_dracut_conf_name()
            )
        if config.get('modules'):
            modules = [
                module for module in config['modules']
                if self._module_available(module)
            ]
            dracut_config.append(
                'add_dracutmodules+=" {0} "\n'.format(' '.join(modules))
            )
        if config.get('omit_modules'):
            dracut_config.append(
                'omit_dracutmodules+=" {0} "\n'.format(
                    ' '.join(config['omit_modules'])
                )
            )
        if config.get('install_items'):
            dracut_config.append(
                'install_items+=" {0} "\n'.format(
                    ' '.join(config['install_items'])
                )
            )
        if dracut_config:
            with open(config_file, 'w') as config:
                config.writelines(dracut_config)

    def prepare(self):
        """
        Prepare dracut caller environment

        * Setup machine_id(s) to be generic and rebuild by dracut on boot
        """
        setup = SystemSetup(
            self.xml_state, self.boot_root_directory
        )
        setup.setup_machine_id()
        self.dracut_options.append('--install')
        self.dracut_options.append('/.profile')

    def create_initrd(self, mbrid=None, basename=None, install_initrd=False):
        """
        Create kiwi .profile environment to be included in dracut initrd.
        Call dracut as chroot operation to create the initrd and move
        the result into the image build target directory

        :param object mbrid: unused
        :param string basename: base initrd file name
        :param bool install_initrd: installation media initrd
        """
        if self.is_prepared():
            log.info('Creating generic dracut initrd archive')
            self._create_profile_environment()
            kernel_info = Kernel(self.boot_root_directory)
            kernel_details = kernel_info.get_kernel(raise_on_not_found=True)
            if basename:
                dracut_initrd_basename = basename
            else:
                dracut_initrd_basename = self.initrd_base_name
            if install_initrd:
                included_files = self.included_files_install
                modules_args = [
                    '--add', ' {0} '.format(' '.join(self.install_modules))
                ] if self.install_modules else []
                omit_modules_args = [
                    '--omit', ' {0} '.format(
                        ' '.join(self.omit_install_modules)
                    )
                ] if self.omit_install_modules else []
            else:
                included_files = self.included_files
                modules_args = [
                    '--add', ' {0} '.format(' '.join(self.modules))
                ] if self.modules else []
                omit_modules_args = [
                    '--omit', ' {0} '.format(' '.join(self.omit_modules))
                ] if self.omit_modules else []
            dracut_initrd_basename += '.xz'
            options = self.dracut_options + modules_args +\
                omit_modules_args + included_files
            dracut_call = Command.run(
                [
                    'chroot', self.boot_root_directory,
                    'dracut', '--verbose',
                    '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--xz'
                ] + options + [
                    dracut_initrd_basename,
                    kernel_details.version
                ],
                stderr_to_stdout=True
            )
            log.debug(dracut_call.output)
            Command.run(
                [
                    'mv',
                    os.sep.join(
                        [self.boot_root_directory, dracut_initrd_basename]
                    ),
                    self.target_dir
                ]
            )
            self.initrd_filename = os.sep.join(
                [self.target_dir, dracut_initrd_basename]
            )

    def _get_modules(self):
        cmd = Command.run(
            [
                'chroot', self.boot_root_directory,
                'dracut', '--list-modules', '--no-kernel'
            ]
        )
        return cmd.output.splitlines()

    def _module_available(self, module):
        warn_msg = 'dracut module "{0}" not found in the root tree'
        if module in self.available_modules:
            return True
        log.warning(warn_msg.format(module))
        return False

    def _create_profile_environment(self):
        profile = Profile(self.xml_state)
        defaults = Defaults()
        defaults.to_profile(profile)
        profile.create(
            Defaults.get_profile_file(self.boot_root_directory)
        )
