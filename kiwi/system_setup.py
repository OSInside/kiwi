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

# project
from command import Command
from command_process import CommandProcess
from logger import log
from defaults import Defaults
from users import Users
from shell import Shell
from path import Path

from exceptions import (
    KiwiScriptFailed
)


class SystemSetup(object):
    """
        Implementation of system setup steps supported by kiwi.
        kiwi is not responsible for the system configuration, however
        some setup steps needs to be performed in order to provide
        a minimal work environment inside of the image.
    """
    def __init__(self, xml_state, description_dir, root_dir):
        self.xml_state = xml_state
        self.description_dir = description_dir
        self.root_dir = root_dir
        self.__preferences_lookup()

    def import_description(self):
        """
            import XML descriptions, custom scripts and script helper methods
        """
        log.info('Importing Image description to system tree')
        description = self.root_dir + '/image/config.xml'
        log.info('--> Importing state XML description as image/config.xml')
        Path.create(self.root_dir + '/image')
        with open(description, 'w') as config:
            config.write('<?xml version="1.0" encoding="utf-8"?>')
            self.xml_state.xml_data.export(outfile=config, level=0)

        need_script_helper_functions = False
        config_script = self.description_dir + '/config.sh'
        image_script = self.description_dir + '/images.sh'

        bootloader_scripts = {
            'edit_boot_config.sh':
                self.xml_state.build_type.get_editbootconfig(),
            'edit_boot_install.sh':
                self.xml_state.build_type.get_editbootinstall()
        }

        script_target = self.root_dir + '/image/'

        for name, bootloader_script in bootloader_scripts.iteritems():
            if bootloader_script:
                script_file = self.description_dir + '/' + bootloader_script
                if os.path.exists(script_file):
                    log.info(
                        '--> Importing %s script as %s',
                        bootloader_script, 'image/' + name
                    )
                    Command.run(
                        [
                            'cp', script_file, script_target + name
                        ]
                    )
                else:
                    raise KiwiScriptFailed(
                        'Specified script %s does not exist' % script_file
                    )

        if os.path.exists(config_script):
            log.info('--> Importing config script as image/config.sh')
            Command.run(['cp', config_script, script_target])
            need_script_helper_functions = True

        if os.path.exists(image_script):
            log.info('--> Importing image script as image/images.sh')
            Command.run(['cp', image_script, script_target])
            need_script_helper_functions = True

        if need_script_helper_functions:
            script_functions = Defaults.get_common_functions_file()
            script_functions_target = self.root_dir + '/.kconfig'
            log.info('--> Importing script helper functions')
            Command.run([
                'cp', script_functions, script_functions_target
            ])

    def cleanup(self):
        """
            delete all traces of a kiwi description which are not
            required in the later image
        """
        Command.run(['rm', '-r', '-f', '/.kconfig', '/image'])

    def import_shell_environment(self, profile):
        """
            create profile environment to let scripts consume
            information from the XML description.
        """
        profile_file = self.root_dir + '/.profile'
        log.info('Creating .profile environment')
        profile_environment = profile.create()
        with open(profile_file, 'w') as profile:
            for line in profile_environment:
                profile.write(line + '\n')
                log.debug('--> %s', line)

    def import_overlay_files(
        self, follow_links=False, preserve_owner_group=False
    ):
        """
            copy overlay files from the image description to
            the image root tree
        """
        overlay_directory = self.description_dir + '/root/'
        if os.path.exists(overlay_directory):
            log.info('Copying user defined files to image tree')
            rsync_options = [
                '-r', '-p', '-t', '-D', '-H', '-X', '-A', '--one-file-system'
            ]
            if follow_links:
                rsync_options.append('--copy-links')
            else:
                rsync_options.append('--links')
            if preserve_owner_group:
                rsync_options.append('-o')
                rsync_options.append('-g')
            Command.run(
                ['rsync'] + rsync_options + [
                    overlay_directory, self.root_dir
                ]
            )

    def setup_hardware_clock(self):
        if 'hwclock' in self.preferences:
            log.info(
                'Setting up hardware clock: %s', self.preferences['hwclock']
            )
            Command.run([
                'chroot', self.root_dir,
                'hwclock', '--adjust', '--' + self.preferences['hwclock']
            ])

    def setup_keyboard_map(self):
        if 'keytable' in self.preferences:
            log.info(
                'Setting up keytable: %s', self.preferences['keytable']
            )
            Shell.run_common_function(
                'baseUpdateSysConfig', [
                    self.root_dir + '/etc/sysconfig/keyboard', 'KEYTABLE',
                    '"' + self.preferences['keytable'] + '"'
                ]
            )

    def setup_locale(self):
        if 'locale' in self.preferences:
            log.info(
                'Setting up locale: %s', self.preferences['locale']
            )
            Shell.run_common_function(
                'baseUpdateSysConfig', [
                    self.root_dir + '/etc/sysconfig/language', 'RC_LANG',
                    self.preferences['locale'].split(',')[0] + '.UTF-8'
                ]
            )

    def setup_timezone(self):
        if 'timezone' in self.preferences:
            log.info(
                'Setting up timezone: %s', self.preferences['timezone']
            )
            zoneinfo = '/usr/share/zoneinfo/' + self.preferences['timezone']
            Command.run([
                'chroot', self.root_dir,
                'ln', '-s', '-f', zoneinfo, '/etc/localtime'
            ])

    def setup_groups(self):
        """
            add groups for configured users
        """
        users_sections = self.xml_state.get_users_sections()
        if users_sections:
            for users in users_sections:
                group_name = users.get_group()
                group_id = users.get_id()
                system_users = Users(self.root_dir)
                if not system_users.group_exists(group_name):
                    options = []
                    if group_id:
                        options.append('-g')
                        options.append(group_id)
                    log.info('Adding group %s', group_name)
                    system_users.group_add(group_name, options)

    def setup_users(self):
        """
            add/modify configured users
        """
        users_sections = self.xml_state.get_users_sections()
        if users_sections:
            for users in users_sections:
                user_sections = users.get_user()
                if user_sections:
                    log.info('Setting up users')
                    group_name = users.get_group()
                    group_id = users.get_id()
                    for user in user_sections:
                        password = user.get_password()
                        password_format = user.get_pwdformat()
                        home_path = user.get_home()
                        user_name = user.get_name()
                        user_id = user.get_id()
                        user_realname = user.get_realname()
                        user_shell = user.get_shell()

                        system_users = Users(self.root_dir)
                        user_exists = system_users.user_exists(user_name)

                        options = []
                        if password_format == 'plain':
                            password = self.__create_passwd_hash(password)
                        if password:
                            options.append('-p')
                            options.append(password)
                        if user_shell:
                            options.append('-s')
                            options.append(user_shell)
                        if group_id or group_name:
                            options.append('-g')
                            if group_id:
                                options.append(group_id)
                            else:
                                options.append(group_name)
                        if user_id:
                            options.append('-u')
                            options.append(user_id)
                        if user_realname:
                            options.append('-c')
                            options.append(user_realname)
                        if not user_exists and home_path:
                            options.append('-m')
                            options.append('-d')
                            options.append(home_path)

                        if user_exists:
                            log.info(
                                '--> Modifying user: %s [%s]',
                                user_name, group_name
                            )
                            system_users.user_modify(user_name, options)
                        else:
                            log.info(
                                '--> Adding user: %s [%s]',
                                user_name, group_name
                            )
                            system_users.user_add(user_name, options)
                            if home_path:
                                log.info(
                                    '--> Setting permissions for %s', home_path
                                )
                                system_users.setup_home_for_user(
                                    user_name, group_name, home_path
                                )

    def import_image_identifier(self):
        """
            create an /etc/ImageID identifier file
        """
        image_id = self.xml_state.xml_data.get_id()
        if image_id and os.path.exists(self.root_dir + '/etc'):
            image_id_file = self.root_dir + '/etc/ImageID'
            log.info('Creating identifier: %s as %s', image_id, image_id_file)
            with open(image_id_file, 'w') as identifier:
                identifier.write('%s\n' % image_id)

    def call_config_script(self):
        self.__call_script('config.sh')

    def call_image_script(self):
        self.__call_script('images.sh')

    def call_edit_boot_config_script(self, filesystem, boot_part_id):
        self.__call_script_no_chroot(
            'edit_boot_config.sh', [filesystem, format(boot_part_id)]
        )

    def call_edit_boot_install_script(self, diskname, boot_device_node):
        self.__call_script_no_chroot(
            'edit_boot_install.sh', [diskname, boot_device_node]
        )

    def create_init_link_from_linuxrc(self):
        """
            kiwi boot images provides the linuxrc script, however the kernel
            also expects an init executable to be present. This method creates
            a hard link to the linuxrc file
        """
        Command.run(
            ['ln', self.root_dir + '/linuxrc', self.root_dir + '/init']
        )

    def create_recovery_archive(self):
        """
            create a compressed recovery archive from the root tree
            for use with kiwi's recvoery system
        """
        # TODO
        pass

    def __call_script(self, name):
        if os.path.exists(self.root_dir + '/image/' + name):
            config_script = Command.call(
                ['chroot', self.root_dir, '/image/' + name]
            )
            process = CommandProcess(
                command=config_script, log_topic='Calling ' + name + ' script'
            )
            result = process.poll_and_watch()
            if result.returncode != 0:
                raise KiwiScriptFailed(
                    '%s failed: %s' % (name, format(result.stderr))
                )
            log.debug(result.stderr)

    def __call_script_no_chroot(self, name, option_list):
        if os.path.exists(self.root_dir + '/image/' + name):
            bash_command = [
                'cd', self.root_dir, '&&',
                'bash', '--norc', 'image/' + name, ' '.join(option_list)
            ]
            config_script = Command.call(
                ['bash', '-c', ' '.join(bash_command)]
            )
            process = CommandProcess(
                command=config_script, log_topic='Calling ' + name + ' script'
            )
            result = process.poll_and_watch()
            if result.returncode != 0:
                raise KiwiScriptFailed(
                    '%s failed: %s' % (name, format(result.stderr))
                )
            log.debug(result.stderr)

    def __create_passwd_hash(self, password):
        openssl = Command.run(
            ['openssl', 'passwd', '-1', '-salt', 'xyz', password]
        )
        return openssl.output

    def __preferences_lookup(self):
        self.preferences = {}
        for preferences in self.xml_state.get_preferences_sections():
            timezone_section = preferences.get_timezone()
            locale_section = preferences.get_locale()
            hwclock_section = preferences.get_hwclock()
            keytable_section = preferences.get_keytable()
            if timezone_section:
                self.preferences['timezone'] = timezone_section[0]
            if locale_section:
                self.preferences['locale'] = locale_section[0]
            if hwclock_section:
                self.preferences['hwclock'] = hwclock_section[0]
            if keytable_section:
                self.preferences['keytable'] = keytable_section[0]
