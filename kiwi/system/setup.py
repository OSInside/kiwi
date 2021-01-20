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
import glob
import os
import logging
import copy
from collections import OrderedDict
from collections import namedtuple
from tempfile import NamedTemporaryFile
from typing import (
    Any, Optional
)

# project
import kiwi.defaults as defaults

from kiwi.utils.fstab import Fstab
from kiwi.xml_state import XMLState
from kiwi.runtime_config import RuntimeConfig
from kiwi.mount_manager import MountManager
from kiwi.system.uri import Uri
from kiwi.repository import Repository
from kiwi.system.root_bind import RootBind
from kiwi.system.root_init import RootInit
from kiwi.command import Command
from kiwi.command_process import CommandProcess
from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults
from kiwi.system.users import Users
from kiwi.system.shell import Shell
from kiwi.path import Path
from kiwi.archive.tar import ArchiveTar
from kiwi.utils.compress import Compress
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.utils.rpm_database import RpmDataBase
from kiwi.system.profile import Profile

from kiwi.exceptions import (
    KiwiImportDescriptionError,
    KiwiScriptFailed
)

log: Any = logging.getLogger('kiwi')


class SystemSetup:
    """
    **Implementation of system setup steps supported by kiwi**

    Kiwi is not responsible for the system configuration, however
    some setup steps needs to be performed in order to provide
    a minimal work environment inside of the image according to
    the desired image type.

    :param object xml_state: instance of :class:`XMLState`
    :param str root_dir: root directory path name
    """

    def __init__(self, xml_state: XMLState, root_dir: str):
        self.runtime_config = RuntimeConfig()
        self.arch = Defaults.get_platform_name()
        self.xml_state = xml_state
        self.description_dir = \
            xml_state.xml_data.description_dir
        self.derived_description_dir = \
            xml_state.xml_data.derived_description_dir
        self.root_dir = root_dir
        self._preferences_lookup()
        self._oemconfig_lookup()

    def import_description(self) -> None:
        """
        Import XML descriptions, custom scripts, archives and
        script helper methods
        """
        log.info('Importing Image description to system tree')
        description = os.path.join(
            self.root_dir, defaults.IMAGE_METADATA_DIR, 'config.xml'
        )
        log.info(
            '--> Importing state XML description to {0}'.format(description)
        )
        Path.create(
            os.path.join(self.root_dir, defaults.IMAGE_METADATA_DIR)
        )
        with open(description, 'w', encoding='utf-8') as config:
            config.write('<?xml version="1.0" encoding="utf-8"?>')
            self.xml_state.xml_data.export(outfile=config, level=0)

        self._import_custom_scripts()
        self._import_custom_archives()
        self._import_cdroot_archive()

    def script_exists(self, name: str) -> bool:
        """
        Check if provided script base name exists in the image description

        :param str name: script base name
        """
        return os.path.exists(os.path.join(self.description_dir, name))

    def cleanup(self) -> None:
        """
        Delete all traces of a kiwi description which are not
        required in the later image
        """
        Command.run(
            [
                'chroot', self.root_dir,
                'rm', '-rf', '.kconfig', defaults.IMAGE_METADATA_DIR
            ]
        )

    def import_repositories_marked_as_imageinclude(self) -> None:
        """
        Those <repository> sections which are marked with the
        imageinclude attribute should be permanently added to
        the image repository configuration
        """
        repository_sections = \
            self.xml_state.get_repository_sections_used_in_image()
        root = RootInit(
            root_dir=self.root_dir, allow_existing=True
        )
        repo = Repository.new(
            RootBind(root), self.xml_state.get_package_manager()
        )
        repo.use_default_location()
        for xml_repo in repository_sections:
            repo_type = xml_repo.get_type()
            repo_source = xml_repo.get_source().get_path()
            repo_user = xml_repo.get_username()
            repo_secret = xml_repo.get_password()
            repo_alias = xml_repo.get_alias()
            repo_priority = xml_repo.get_priority()
            repo_dist = xml_repo.get_distribution()
            repo_components = xml_repo.get_components()
            repo_repository_gpgcheck = xml_repo.get_repository_gpgcheck()
            repo_package_gpgcheck = xml_repo.get_package_gpgcheck()
            repo_sourcetype = xml_repo.get_sourcetype()
            uri = Uri(repo_source, repo_type)
            repo_source_translated = uri.translate(
                check_build_environment=False
            )
            if not repo_alias:
                repo_alias = uri.alias()
            log.info('Setting up image repository {0}'.format(repo_source))
            log.info('--> Type: {0}'.format(repo_type))
            log.info('--> Translated: {0}'.format(repo_source_translated))
            log.info('--> Alias: {0}'.format(repo_alias))
            repo.add_repo(
                repo_alias, repo_source_translated,
                repo_type, repo_priority, repo_dist, repo_components,
                repo_user, repo_secret, uri.credentials_file_name(),
                repo_repository_gpgcheck, repo_package_gpgcheck,
                repo_sourcetype
            )

    def import_cdroot_files(self, target_dir: str) -> None:
        """
        Copy cdroot files from the image description to the
        specified target directory. Supported is a tar
        archive named config-cdroot.tar[.compression-postfix]

        :param str target_dir: directory to unpack archive to
        """
        glob_match = self.description_dir + '/config-cdroot.tar*'
        for cdroot_archive in sorted(glob.iglob(glob_match)):
            log.info(
                'Extracting ISO user config archive: {0} to: {1}'.format(
                    cdroot_archive, target_dir
                )
            )
            archive = ArchiveTar(cdroot_archive)
            archive.extract(target_dir)
            break

    def import_overlay_files(
        self, follow_links: bool = False, preserve_owner_group: bool = False
    ) -> None:
        """
        Copy overlay files from the image description to
        the image root tree. Supported are a root/ directory
        or a root.tar.gz tarball. The root/ directory takes
        precedence over the tarball.

        In addition the method also supports profile specific
        overlay files which are searched in a directory of the
        same name as the profile name.

        The overall order for including overlay files is as
        follows:

        1. root/ dir or root.tar.gz
        2. PROFILE_NAME/ dir(s) in the order of the selected
           profiles

        :param bool follow_links: follow symlinks true|false
        :param bool preserve_owner_group: preserve permissions true|false
        """
        overlay_directory = self.description_dir + '/root/'
        overlay_archive = self.description_dir + '/root.tar.gz'
        if os.path.exists(overlay_directory):
            self._sync_overlay_files(
                overlay_directory, follow_links, preserve_owner_group
            )
        elif os.path.exists(overlay_archive):
            log.info('Extracting user defined files from archive to image tree')
            archive = ArchiveTar(overlay_archive)
            archive.extract(self.root_dir)

        for profile in self.xml_state.profiles:
            overlay_directory = os.path.join(
                self.description_dir, profile
            ) + os.sep
            if os.path.exists(overlay_directory):
                self._sync_overlay_files(
                    overlay_directory, follow_links, preserve_owner_group,
                    profile
                )

    def setup_machine_id(self) -> None:
        """
        Setup systemd machine id

        Empty out the machine id which was provided by the package
        installation process. This will instruct the dracut initrd
        code to create a new machine id. This way a golden image
        produces unique machine id's on first deployment and boot
        of the image.

        Note: Requires dracut connected image type

        This method must only be called if the image is of
        a type which gets booted via a dracut created initrd.
        Deleting the machine-id without the dracut initrd
        creating a new one produces an inconsistent system
        """
        machine_id = os.path.join(
            self.root_dir, 'etc', 'machine-id'
        )

        if os.path.exists(machine_id):
            with open(machine_id, 'w'):
                pass

    def setup_permissions(self) -> None:
        """
        Check and Fix permissions using chkstat

        Call chkstat in system mode which reads /etc/sysconfig/security
        to determine the configured security level and applies the
        appropriate permission definitions from the /etc/permissions*
        files. It's possible to provide those files as overlay files
        in the image description to apply a certain permission setup
        when needed. Otherwise the default setup as provided on the
        package level applies.

        It's required that the image root system has chkstat installed.
        If not present KIWI skips this step and continuous with a
        warning.
        """
        chkstat = Path.which(
            'chkstat', root_dir=self.root_dir, access_mode=os.X_OK
        )
        if chkstat:
            log.info('Check/Fix File Permissions')
            Command.run(
                ['chroot', self.root_dir, 'chkstat', '--system', '--set']
            )
        else:
            log.warning(
                'chkstat not found in image. File Permissions Check skipped'
            )

    def setup_keyboard_map(self) -> None:
        """
        Setup console keyboard
        """
        if 'keytable' in self.preferences:
            log.info(
                'Setting up keytable: {0}'.format(self.preferences['keytable'])
            )
            if CommandCapabilities.has_option_in_help(
                'systemd-firstboot', '--keymap',
                root=self.root_dir, raise_on_error=False
            ):
                Path.wipe(self.root_dir + '/etc/vconsole.conf')
                Command.run([
                    'chroot', self.root_dir, 'systemd-firstboot',
                    '--keymap=' + self.preferences['keytable']
                ])
            elif os.path.exists(self.root_dir + '/etc/sysconfig/keyboard'):
                Shell.run_common_function(
                    'baseUpdateSysConfig', [
                        self.root_dir + '/etc/sysconfig/keyboard', 'KEYTABLE',
                        '"' + self.preferences['keytable'] + '"'
                    ]
                )
            else:
                log.warning(
                    'keyboard setup skipped no capable '
                    'systemd-firstboot or etc/sysconfig/keyboard found'
                )

    def setup_locale(self) -> None:
        """
        Setup UTF8 system wide locale
        """
        if 'locale' in self.preferences:
            if 'POSIX' in self.preferences['locale'].split(','):
                locale = 'POSIX'
            else:
                locale = '{0}.UTF-8'.format(
                    self.preferences['locale'].split(',')[0]
                )
            log.info(
                'Setting up locale: {0}'.format(self.preferences['locale'])
            )
            if CommandCapabilities.has_option_in_help(
                'systemd-firstboot', '--locale',
                root=self.root_dir, raise_on_error=False
            ):
                Path.wipe(self.root_dir + '/etc/locale.conf')
                Command.run([
                    'chroot', self.root_dir, 'systemd-firstboot',
                    '--locale=' + locale
                ])

    def setup_timezone(self) -> None:
        """
        Setup timezone symlink
        """
        if 'timezone' in self.preferences:
            log.info(
                'Setting up timezone: {0}'.format(self.preferences['timezone'])
            )
            if CommandCapabilities.has_option_in_help(
                'systemd-firstboot', '--timezone',
                root=self.root_dir, raise_on_error=False
            ):
                Path.wipe(self.root_dir + '/etc/localtime')
                Command.run([
                    'chroot', self.root_dir, 'systemd-firstboot',
                    '--timezone=' + self.preferences['timezone']
                ])
            else:
                zoneinfo = '/usr/share/zoneinfo/' + self.preferences['timezone']
                Command.run([
                    'chroot', self.root_dir,
                    'ln', '-s', '-f', zoneinfo, '/etc/localtime'
                ])

    def setup_groups(self) -> None:
        """
        Add groups for configured users
        """
        system_users = Users(self.root_dir)

        for user in self.xml_state.get_users():
            for group in self.xml_state.get_user_groups(user.get_name()):
                if not system_users.group_exists(group):
                    log.info('Adding group {0}'.format(group))
                    system_users.group_add(group, [])

    def setup_users(self) -> None:
        """
        Add/Modify configured users
        """
        system_users = Users(self.root_dir)

        for user in self.xml_state.get_users():
            log.info('Setting up user {0}'.format(user.get_name()))
            password = user.get_password()
            password_format = user.get_pwdformat()
            home_path = user.get_home()
            user_name = user.get_name()
            user_id = user.get_id()
            user_realname = user.get_realname()
            user_shell = user.get_shell()
            user_groups = self.xml_state.get_user_groups(user.get_name())

            user_exists = system_users.user_exists(user_name)

            options = self._process_user_options(
                password_format, password, user_shell, user_groups,
                user_id, user_realname, user_exists, home_path
            )

            group_msg = '--> Primary group for user {0}: {1}'.format(
                user_name, user_groups[0]
            ) if len(user_groups) else ''

            if user_exists:
                log.info('--> Modifying user: {0}'.format(user_name))
                if group_msg:
                    log.info(group_msg)
                system_users.user_modify(user_name, options)
            else:
                log.info('--> Adding user: {0}'.format(user_name))
                if group_msg:
                    log.info(group_msg)
                system_users.user_add(user_name, options)
                if home_path:
                    log.info(
                        '--> Setting permissions for {0}'.format(home_path)
                    )
                    # Emtpy group string assumes the login or default group
                    system_users.setup_home_for_user(
                        user_name,
                        user_groups[0] if len(user_groups) else '',
                        home_path
                    )

    def setup_plymouth_splash(self) -> None:
        """
        Setup the KIWI configured splash theme as default

        The method uses the plymouth-set-default-theme tool to setup the
        theme for the plymouth splash system. Only in case the tool could
        be found in the image root, it is assumed plymouth splash is in
        use and the tool is called in a chroot operation
        """
        theme_setup = 'plymouth-set-default-theme'
        if Path.which(filename=theme_setup, root_dir=self.root_dir):
            for preferences in self.xml_state.get_preferences_sections():
                splash_section_content = preferences.get_bootsplash_theme()
                if splash_section_content:
                    splash_theme = splash_section_content[0]
                    Command.run(
                        ['chroot', self.root_dir, theme_setup, splash_theme]
                    )

    def import_image_identifier(self) -> None:
        """
        Create etc/ImageID identifier file
        """
        image_id = self.xml_state.xml_data.get_id()
        if image_id and os.path.exists(self.root_dir + '/etc'):
            image_id_file = self.root_dir + '/etc/ImageID'
            log.info(
                'Creating image identifier: {0} in {1}'.format(
                    image_id, image_id_file
                )
            )
            with open(image_id_file, 'w') as identifier:
                identifier.write('{0}{1}'.format(image_id, os.linesep))

    def set_selinux_file_contexts(self, security_context_file: str) -> None:
        """
        Initialize the security context fields (extended attributes)
        on the files matching the security_context_file

        :param str security_context_file: path file name
        """
        log.info('Processing SELinux file security contexts')
        Command.run(
            [
                'chroot', self.root_dir,
                'setfiles', security_context_file, '/', '-v'
            ]
        )

    def export_modprobe_setup(self, target_root_dir: str) -> None:
        """
        Export etc/modprobe.d to given root_dir

        :param str target_root_dir: path name
        """
        modprobe_config = self.root_dir + '/etc/modprobe.d'
        if os.path.exists(modprobe_config):
            log.info('Export modprobe configuration')
            Path.create(target_root_dir + '/etc')
            data = DataSync(
                modprobe_config, target_root_dir + '/etc/'
            )
            data.sync_data(
                options=['-a']
            )

    def export_package_list(self, target_dir: str) -> Optional[str]:
        """
        Export image package list as metadata reference
        used by the open buildservice

        :param str target_dir: path name
        """
        image_version = self.xml_state.get_image_version() or 'unspecified'
        filename = ''.join(
            [
                target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + image_version,
                '.packages'
            ]
        )
        packager = Defaults.get_default_packager_tool(
            self.xml_state.get_package_manager()
        )
        if packager == 'rpm':
            self._export_rpm_package_list(filename)
            return filename
        elif packager == 'dpkg':
            self._export_deb_package_list(filename)
            return filename
        elif packager == 'pacman':
            self._export_pacman_package_list(filename)
            return filename
        return None

    def export_package_changes(self, target_dir: str) -> Optional[str]:
        """
        Export image package changelog for comparision of
        actual changes of the installed packages

        :param str target_dir: path name
        """
        image_version = self.xml_state.get_image_version() or 'unspecified'
        if self.runtime_config.get_package_changes():
            filename = ''.join(
                [
                    target_dir, '/',
                    self.xml_state.xml_data.get_name(),
                    '.' + self.arch,
                    '-' + image_version,
                    '.changes'
                ]
            )
            packager = Defaults.get_default_packager_tool(
                self.xml_state.get_package_manager()
            )
            if packager == 'rpm':
                self._export_rpm_package_changes(filename)
                return filename
            elif packager == 'dpkg':
                self._export_deb_package_changes(filename)
                return filename
        return None

    def export_package_verification(self, target_dir: str) -> Optional[str]:
        """
        Export package verification result as metadata reference
        used by the open buildservice

        :param str target_dir: path name
        """
        image_version = self.xml_state.get_image_version() or 'unspecified'
        filename = ''.join(
            [
                target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + image_version,
                '.verified'
            ]
        )
        packager = Defaults.get_default_packager_tool(
            self.xml_state.get_package_manager()
        )
        if packager == 'rpm':
            self._export_rpm_package_verification(filename)
            return filename
        elif packager == 'dpkg':
            self._export_deb_package_verification(filename)
            return filename
        return None

    def call_disk_script(self) -> None:
        """
        Call disk.sh script chrooted
        """
        self._call_script(
            defaults.POST_DISK_SYNC_SCRIPT
        )

    def call_config_script(self) -> None:
        """
        Call config.sh script chrooted
        """
        self._call_script(
            defaults.POST_PREPARE_SCRIPT
        )

    def call_image_script(self) -> None:
        """
        Call images.sh script chrooted
        """
        self._call_script(
            defaults.PRE_CREATE_SCRIPT
        )

    def call_edit_boot_config_script(
        self, filesystem: str, boot_part_id: int, working_directory: str = None
    ) -> None:
        """
        Call configured editbootconfig script _NON_ chrooted

        Pass the boot filesystem name and the partition number of
        the boot partition as parameters to the call

        :param str filesystem: boot filesystem name
        :param int boot_part_id: boot partition number
        :param str working_directory: directory name
        """
        self._call_script_no_chroot(
            name=defaults.EDIT_BOOT_CONFIG_SCRIPT,
            option_list=[filesystem, format(boot_part_id)],
            working_directory=working_directory
        )

    def call_edit_boot_install_script(
        self, diskname: str, boot_device_node: str,
        working_directory: str = None
    ) -> None:
        """
        Call configured editbootinstall script _NON_ chrooted

        Pass the disk file name and the device node of the boot partition
        as parameters to the call

        :param str diskname: file path name
        :param str boot_device_node: boot device node name
        :param str working_directory: directory name
        """
        self._call_script_no_chroot(
            name=defaults.EDIT_BOOT_INSTALL_SCRIPT,
            option_list=[diskname, boot_device_node],
            working_directory=working_directory
        )

    def create_fstab(self, fstab: Fstab) -> None:
        """
        Create etc/fstab from given Fstab object

        Custom fstab modifications are possible and handled
        in the following order:

        1. Look for an optional fstab.append file which allows
           to append custom fstab entries to the final fstab. Once
           embedded the fstab.append file will be deleted

        2. Look for an optional fstab.patch file which allows
           to patch the current contents of the fstab file with
           a given patch file. Once patched the fstab.patch file will
           be deleted

        3. Look for an optional fstab.script file which is called
           chrooted for the purpose of updating the fstab file as
           appropriate. Note: There is no validation in place that
           checks if the script actually handles fstab or any other
           file in the image rootfs. Once called the fstab.script
           file will be deleted

        :param object fstab: instance of Fstab
        """
        fstab_file = self.root_dir + '/etc/fstab'
        fstab_append_file = self.root_dir + '/etc/fstab.append'
        fstab_patch_file = self.root_dir + '/etc/fstab.patch'
        fstab_script_file = self.root_dir + '/etc/fstab.script'

        fstab.export(fstab_file)

        if os.path.exists(fstab_append_file):
            with open(fstab_file, 'a') as fstab_io:
                with open(fstab_append_file, 'r') as append:
                    fstab_io.write(append.read())
                Path.wipe(fstab_append_file)

        if os.path.exists(fstab_patch_file):
            Command.run(
                ['patch', fstab_file, fstab_patch_file]
            )
            Path.wipe(fstab_patch_file)

        if os.path.exists(fstab_script_file):
            Command.run(
                ['chroot', self.root_dir, '/etc/fstab.script']
            )
            Path.wipe(fstab_script_file)

    def create_init_link_from_linuxrc(self) -> None:
        """
        kiwi boot images provides the linuxrc script, however the kernel
        also expects an init executable to be present. This method creates
        a hard link to the linuxrc file
        """
        Command.run(
            ['ln', self.root_dir + '/linuxrc', self.root_dir + '/init']
        )

    def create_recovery_archive(self) -> None:
        """
        Create a compressed recovery archive from the root tree
        for use with kiwi's recvoery system. The method creates
        additional data into the image root filesystem which is
        deleted prior to the creation of a new recovery data set
        """
        # cleanup
        bash_comand = [
            'rm', '-f', self.root_dir + '/recovery.*'
        ]
        Command.run(['bash', '-c', ' '.join(bash_comand)])
        if not self.oemconfig['recovery']:
            return
        # recovery.tar
        log.info('Creating recovery tar archive')
        metadata = {
            'archive_name':
                self.root_dir + '/recovery.tar',
            'archive_filecount':
                self.root_dir + '/recovery.tar.files',
            'archive_size':
                self.root_dir + '/recovery.tar.size',
            'partition_size':
                self.root_dir + '/recovery.partition.size',
            'partition_filesystem':
                self.root_dir + '/recovery.tar.filesystem'
        }
        recovery_archive = NamedTemporaryFile(
            delete=False
        )
        archive = ArchiveTar(
            filename=recovery_archive.name,
            create_from_file_list=False
        )
        archive.create(
            source_dir=self.root_dir,
            exclude=['dev', 'proc', 'sys'],
            options=[
                '--numeric-owner',
                '--hard-dereference',
                '--preserve-permissions'
            ]
        )
        Command.run(
            ['mv', recovery_archive.name, metadata['archive_name']]
        )
        # recovery.tar.filesystem
        recovery_filesystem = self.xml_state.build_type.get_filesystem()
        with open(metadata['partition_filesystem'], 'w') as partfs:
            partfs.write('{0}'.format(recovery_filesystem))
        log.info(
            '--> Recovery partition filesystem: {0}'.format(recovery_filesystem)
        )
        # recovery.tar.files
        bash_comand = [
            'tar', '-tf', metadata['archive_name'], '|', 'wc', '-l'
        ]
        tar_files_call = Command.run(
            ['bash', '-c', ' '.join(bash_comand)]
        )
        tar_files_count = int(tar_files_call.output.rstrip('\n'))
        with open(metadata['archive_filecount'], 'w') as files:
            files.write('{0}{1}'.format(tar_files_count, os.linesep))
        log.info(
            '--> Recovery file count: {0} files'.format(tar_files_count)
        )
        # recovery.tar.size
        recovery_archive_size_bytes = os.path.getsize(metadata['archive_name'])
        with open(metadata['archive_size'], 'w') as size:
            size.write('{0}'.format(recovery_archive_size_bytes))
        log.info(
            '--> Recovery uncompressed size: {0} mbytes'.format(
                int(recovery_archive_size_bytes / 1048576)
            )
        )
        # recovery.tar.gz
        log.info('--> Compressing recovery archive')
        compress = Compress(self.root_dir + '/recovery.tar')
        compress.gzip()
        # recovery.partition.size
        recovery_archive_gz_size_mbytes = int(
            os.path.getsize(metadata['archive_name'] + '.gz') / 1048576
        )
        recovery_partition_mbytes = recovery_archive_gz_size_mbytes \
            + Defaults.get_recovery_spare_mbytes()
        with open(metadata['partition_size'], 'w') as gzsize:
            gzsize.write('{0}'.format(recovery_partition_mbytes))
        log.info(
            '--> Recovery partition size: {0} mbytes'.format(
                recovery_partition_mbytes
            )
        )
        # delete recovery archive if inplace recovery is requested
        # In this mode the recovery archive is created at install time
        # and not at image creation time. However the recovery metadata
        # is preserved in order to be able to check if enough space
        # is available on the disk to create the recovery archive.
        if self.oemconfig['recovery_inplace']:
            log.info(
                '--> Inplace recovery requested, deleting archive'
            )
            Path.wipe(metadata['archive_name'] + '.gz')

    def _process_user_options(
        self, password_format, password, user_shell, user_groups,
        user_id, user_realname, user_exists, home_path
    ):
        options = []
        if password_format == 'plain':
            password = self._create_passwd_hash(password)
        if password:
            options.append('-p')
            options.append(password)
        if user_shell:
            options.append('-s')
            options.append(user_shell)
        if len(user_groups):
            options.append('-g')
            options.append(user_groups[0])
            if len(user_groups) > 1:
                options.append('-G')
                options.append(','.join(user_groups[1:]))
        if user_id:
            options.append('-u')
            options.append('{0}'.format(user_id))
        if user_realname:
            options.append('-c')
            options.append(user_realname)
        if not user_exists:
            options.append('-m')
            if home_path:
                options.append('-d')
                options.append(home_path)
        return options

    def _import_cdroot_archive(self):
        glob_match = self.description_dir + '/config-cdroot.tar*'
        for cdroot_archive in sorted(glob.iglob(glob_match)):
            archive_file = os.path.join(
                self.root_dir, defaults.IMAGE_METADATA_DIR
            )
            log.info(
                '--> Importing {0} archive to {1}'.format(
                    cdroot_archive, archive_file
                )
            )
            Command.run(
                ['cp', cdroot_archive, archive_file + os.sep]
            )
            break

    def _import_custom_archives(self):
        """
        Import custom tar archive files
        """
        archive_list = []
        system_archives = self.xml_state.get_system_archives()
        bootstrap_archives = self.xml_state.get_bootstrap_archives()
        if system_archives:
            archive_list += system_archives
        if bootstrap_archives:
            archive_list += bootstrap_archives

        archive_target_dir = os.path.join(
            self.root_dir, defaults.IMAGE_METADATA_DIR
        ) + os.sep

        for archive in archive_list:
            archive_is_absolute = archive.startswith(os.sep)
            if archive_is_absolute:
                archive_file = archive
            else:
                archive_file = os.path.join(self.description_dir, archive)

            archive_exists = os.path.exists(archive_file)

            if not archive_exists:
                if self.derived_description_dir and not archive_is_absolute:
                    archive_file = self.derived_description_dir + '/' + archive
                    archive_exists = os.path.exists(archive_file)

            if archive_exists:
                log.info(
                    '--> Importing {0} archive to {1}'.format(
                        archive_file, archive_target_dir
                    )
                )
                Command.run(
                    ['cp', archive_file, archive_target_dir]
                )
            else:
                raise KiwiImportDescriptionError(
                    'Specified archive {0} does not exist'.format(archive_file)
                )

    def _import_custom_scripts(self):
        """
        Import custom scripts
        """
        # custom_scripts defines a dictionary with all script hooks
        # for each script name a the filepath and additional flags
        # are defined. the filepath could be either a relative or
        # absolute information. If filepath is set to None this indicates
        # the script hook is not used. The raise_if_not_exists flag
        # causes kiwi to raise an exception if a specified script
        # filepath does not exist
        script_type = namedtuple(
            'script_type', ['filepath', 'raise_if_not_exists']
        )
        custom_scripts = {
            defaults.POST_PREPARE_SCRIPT: script_type(
                filepath=defaults.POST_PREPARE_SCRIPT,
                raise_if_not_exists=False
            ),
            defaults.PRE_CREATE_SCRIPT: script_type(
                filepath=defaults.PRE_CREATE_SCRIPT,
                raise_if_not_exists=False
            ),
            defaults.POST_DISK_SYNC_SCRIPT: script_type(
                filepath=defaults.POST_DISK_SYNC_SCRIPT,
                raise_if_not_exists=False
            ),
            defaults.EDIT_BOOT_CONFIG_SCRIPT: script_type(
                filepath=self.xml_state.build_type.get_editbootconfig(),
                raise_if_not_exists=True
            ),
            defaults.EDIT_BOOT_INSTALL_SCRIPT: script_type(
                filepath=self.xml_state.build_type.get_editbootinstall(),
                raise_if_not_exists=True
            )
        }
        sorted_custom_scripts = OrderedDict(
            sorted(custom_scripts.items())
        )

        script_target_dir = os.path.join(
            self.root_dir, defaults.IMAGE_METADATA_DIR
        )
        need_script_helper_functions = False

        for name, script in list(sorted_custom_scripts.items()):
            if script.filepath:
                if script.filepath.startswith('/'):
                    script_file = script.filepath
                else:
                    script_file = os.path.join(
                        self.description_dir, script.filepath
                    )
                if os.path.exists(script_file):
                    script_target_file = os.path.join(
                        script_target_dir, name
                    )
                    log.info(
                        '--> Importing {0} script to {1}'.format(
                            script.filepath, script_target_file
                        )
                    )
                    Command.run(
                        ['cp', script_file, script_target_file]
                    )
                    need_script_helper_functions = True
                elif script.raise_if_not_exists:
                    raise KiwiImportDescriptionError(
                        'Specified script {0} does not exist'.format(
                            script_file
                        )
                    )

        if need_script_helper_functions:
            log.info('--> Importing script helper functions')
            Command.run(
                [
                    'cp',
                    Defaults.get_common_functions_file(),
                    self.root_dir + '/.kconfig'
                ]
            )

    def _call_script(self, name, option_list=None):
        script_path = os.path.join(self.root_dir, 'image', name)
        if os.path.exists(script_path):
            options = option_list or []
            command = ['chroot', self.root_dir]
            if not Path.access(script_path, os.X_OK):
                command.append('bash')
            command.append(
                os.path.join(defaults.IMAGE_METADATA_DIR, name)
            )
            command.extend(options)
            profile = Profile(self.xml_state)
            caller_environment = copy.deepcopy(os.environ)
            caller_environment.update(profile.get_settings())
            config_script = Command.call(command, caller_environment)
            process = CommandProcess(
                command=config_script, log_topic='Calling ' + name + ' script'
            )
            result = process.poll_and_watch()
            if result.returncode != 0:
                raise KiwiScriptFailed(
                    '{0} failed: {1}'.format(name, result.stderr)
                )

    def _call_script_no_chroot(
        self, name, option_list, working_directory
    ):
        if not working_directory:
            working_directory = self.root_dir
        script_path = os.path.abspath(
            os.sep.join([self.root_dir, 'image', name])
        )
        if os.path.exists(script_path):
            bash_command = [
                'cd', working_directory, '&&',
                'bash', '--norc', script_path, ' '.join(option_list)
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
                    '{0} failed: {1}'.format(name, result.stderr)
                )

    def _create_passwd_hash(self, password):
        openssl = Command.run(
            ['openssl', 'passwd', '-1', '-salt', 'xyz', password]
        )
        return openssl.output[:-1]

    def _preferences_lookup(self):
        self.preferences = {}
        for preferences in self.xml_state.get_preferences_sections():
            timezone_section = preferences.get_timezone()
            locale_section = preferences.get_locale()
            keytable_section = preferences.get_keytable()
            if timezone_section:
                self.preferences['timezone'] = timezone_section[0]
            if locale_section:
                self.preferences['locale'] = locale_section[0]
            if keytable_section:
                self.preferences['keytable'] = keytable_section[0]

    def _oemconfig_lookup(self):
        self.oemconfig = {
            'recovery_inplace': False,
            'recovery': False
        }
        oemconfig = self.xml_state.get_build_type_oemconfig_section()
        if oemconfig:
            self.oemconfig['recovery'] = \
                self._text(oemconfig.get_oem_recovery())
            self.oemconfig['recovery_inplace'] = \
                self._text(oemconfig.get_oem_inplace_recovery())

    def _text(self, section_content):
        """
        Helper method to return the text for XML elements of the
        following structure: <section>text</section>.
        """
        if section_content:
            return section_content[0]

    def _export_rpm_package_list(self, filename):
        log.info('Export rpm packages metadata')
        dbpath_option = [
            '--dbpath', self._get_rpm_database_location()
        ]
        query_call = Command.run(
            [
                'rpm', '--root', self.root_dir, '-qa', '--qf',
                '|'.join(
                    [
                        '%{NAME}', '%{EPOCH}', '%{VERSION}',
                        '%{RELEASE}', '%{ARCH}', '%{DISTURL}', '%{LICENSE}'
                    ]
                ) + '\\n'
            ] + dbpath_option
        )
        with open(filename, 'w', encoding='utf-8') as packages:
            packages.write(
                os.linesep.join(sorted(query_call.output.splitlines()))
            )
            packages.write(os.linesep)

    def _export_deb_package_list(self, filename):
        log.info('Export deb packages metadata')
        query_call = Command.run(
            [
                'dpkg-query', '--admindir',
                os.sep.join([self.root_dir, 'var/lib/dpkg']), '-W', '-f',
                '|'.join(
                    [
                        '${Package}', 'None', '${Version}',
                        'None', '${Architecture}', 'None', 'None'
                    ]
                ) + '\\n'
            ]
        )
        with open(filename, 'w', encoding='utf-8') as packages:
            packages.write(
                os.linesep.join(sorted(query_call.output.splitlines()))
            )
            packages.write(os.linesep)

    def _export_pacman_package_list(self, filename):
        log.info('Export pacman packages metadata')
        query_call = Command.run(
            [
                'pacman', '--query', '--dbpath',
                os.sep.join([self.root_dir, 'var/lib/pacman'])
            ]
        )
        with open(filename, 'w') as packages:
            for line in query_call.output.splitlines():
                package, _, version_release = line.partition(' ')
                version, _, release = version_release.partition('-')
                packages.writelines([
                    '{0}|None|{1}|{2}|None|None|None{3}'.format(
                        package, version, release, os.linesep
                    )
                ])

    def _export_rpm_package_changes(self, filename):
        log.info('Export rpm packages changelog metadata')
        dbpath_option = [
            '--dbpath', self._get_rpm_database_location()
        ]
        query_call = Command.run(
            [
                'rpm', '--root', self.root_dir,
                '-qa', '--qf', '%{NAME}|\\n', '--changelog'
            ] + dbpath_option
        )
        with open(filename, 'w', encoding='utf-8') as changelog:
            changelog.write(query_call.output)

    def _export_deb_package_changes(self, filename):
        log.info('Export deb packages changelog metadata')
        package_doc_dir = os.sep.join(
            [self.root_dir, '/usr/share/doc']
        )
        with open(filename, 'w', encoding='utf-8') as changelog:
            for package in sorted(os.listdir(package_doc_dir)):
                changelog_file = os.sep.join(
                    [package_doc_dir, package, 'changelog.Debian.gz']
                )
                if os.path.exists(changelog_file):
                    changelog.write(
                        '{0}{1}{2}'.format(package, '|', os.linesep)
                    )
                    changelog.write(
                        '{0}{1}'.format(
                            Command.run(['zcat', changelog_file]).output,
                            os.linesep
                        )
                    )

    def _export_rpm_package_verification(self, filename):
        log.info('Export rpm verification metadata')
        dbpath_option = [
            '--dbpath', self._get_rpm_database_location()
        ]
        query_call = Command.run(
            command=['rpm', '--root', self.root_dir, '-Va'] + dbpath_option,
            raise_on_error=False
        )
        with open(filename, 'w', encoding='utf-8') as verified:
            verified.write(query_call.output)

    def _export_deb_package_verification(self, filename):
        log.info('Export deb verification metadata')
        query_call = Command.run(
            command=[
                'dpkg', '--root', self.root_dir,
                '-V', '--verify-format', 'rpm'
            ],
            raise_on_error=False
        )
        with open(filename, 'w', encoding='utf-8') as verified:
            verified.write(query_call.output)

    def _get_rpm_database_location(self):
        shared_mount = MountManager(
            device='/dev', mountpoint=self.root_dir + '/dev'
        )
        if not shared_mount.is_mounted():
            shared_mount.bind_mount()
        rpmdb = RpmDataBase(self.root_dir)
        if rpmdb.has_rpm():
            dbpath = rpmdb.rpmdb_image.expand_query('%_dbpath')
        else:
            dbpath = rpmdb.rpmdb_host.expand_query('%_dbpath')
        if shared_mount.is_mounted():
            shared_mount.umount_lazy()
        return dbpath

    def _sync_overlay_files(
        self, overlay_directory, follow_links=False,
        preserve_owner_group=False, profile=None
    ):
        log.info(
            'Copying user defined {0} to image tree'.format(
                'files for profile: {0}'.format(profile) if profile else 'files'
            )
        )
        sync_options = [
            '-r', '-p', '-t', '-D', '-H', '-X', '-A', '--one-file-system'
        ]
        if follow_links:
            sync_options.append('--copy-links')
        else:
            sync_options.append('--links')
        if preserve_owner_group:
            sync_options.append('-o')
            sync_options.append('-g')
        data = DataSync(
            overlay_directory, self.root_dir
        )
        data.sync_data(
            options=sync_options
        )
