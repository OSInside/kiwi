import sys
import os
import logging
import io
from mock import (
    patch, call, Mock, MagicMock, mock_open
)
from pytest import (
    raises, fixture
)
from collections import namedtuple

from ..test_helper import argv_kiwi_tests

from kiwi.system.setup import SystemSetup
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiScriptFailed,
    KiwiImportDescriptionError
)


class TestSystemSetup:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.system.setup.RuntimeConfig')
    def setup(self, mock_RuntimeConfig):
        Defaults.set_platform_name('x86_64')
        self.runtime_config = Mock()
        self.runtime_config.get_package_changes = Mock(
            return_value=True
        )
        mock_RuntimeConfig.return_value = self.runtime_config
        self.xml_state = MagicMock()
        self.xml_state.get_package_manager = Mock(
            return_value='zypper'
        )
        self.xml_state.build_type.get_filesystem = Mock(
            return_value='ext3'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='some-image'
        )
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.description_dir = 'description_dir'
        self.setup = SystemSetup(
            self.xml_state, 'root_dir'
        )
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        self.description_dir = os.path.dirname(description.description_origin)
        self.setup_with_real_xml = SystemSetup(
            XMLState(description.load()), 'root_dir'
        )
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        self.run_result = command_run(
            output='password-hash\n',
            error='stderr',
            returncode=0
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def test_setup_ix86(self):
        Defaults.set_platform_name('i686')
        setup = SystemSetup(
            MagicMock(), 'root_dir'
        )
        assert setup.arch == 'ix86'

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.system.setup.glob.iglob')
    def test_import_description(
        self, mock_iglob, mock_path, mock_command
    ):
        mock_iglob.return_value = ['config-cdroot.tar.xz']
        mock_path.return_value = True

        with patch('builtins.open'):
            self.setup_with_real_xml.import_description()

        mock_iglob.assert_called_once_with(
            '{0}/config-cdroot.tar*'.format(self.description_dir)
        )
        assert mock_command.call_args_list == [
            call(
                [
                    'cp', '{0}/config.sh'.format(self.description_dir),
                    'root_dir/image/config.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/disk.sh'.format(self.description_dir),
                    'root_dir/image/disk.sh'
                ]
            ),
            call(
                [
                    'cp',
                    '{0}/my_edit_boot_script'.format(self.description_dir),
                    'root_dir/image/edit_boot_config.sh'
                ]
            ),
            call(
                [
                    'cp', '/absolute/path/to/my_edit_boot_install',
                    'root_dir/image/edit_boot_install.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/images.sh'.format(self.description_dir),
                    'root_dir/image/images.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/post_bootstrap.sh'.format(self.description_dir),
                    'root_dir/image/post_bootstrap.sh'
                ]
            ),
            call(
                [
                    'cp', Defaults.project_file('config/functions.sh'),
                    'root_dir/.kconfig'
                ]
            ),
            call(
                [
                    'cp', '/absolute/path/to/image.tgz', 'root_dir/image/'
                ]
            ),
            call(
                [
                    'cp', '{0}/bootstrap.tgz'.format(self.description_dir),
                    'root_dir/image/'
                ]
            ),
            call(
                ['cp', 'config-cdroot.tar.xz', 'root_dir/image/']
            )
        ]

    @patch('kiwi.path.Path.create')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_import_description_archive_from_derived(
        self, mock_path, mock_command, mock_create
    ):
        path_return_values = [
            True, False, True, True, True, True, True, True, True
        ]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect

        with patch('builtins.open'):
            self.setup_with_real_xml.import_description()

        assert mock_command.call_args_list == [
            call(
                [
                    'cp', '{0}/config.sh'.format(self.description_dir),
                    'root_dir/image/config.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/disk.sh'.format(self.description_dir),
                    'root_dir/image/disk.sh'
                ]
            ),
            call(
                [
                    'cp',
                    '{0}/my_edit_boot_script'.format(self.description_dir),
                    'root_dir/image/edit_boot_config.sh'
                ]
            ),
            call(
                [
                    'cp', '/absolute/path/to/my_edit_boot_install',
                    'root_dir/image/edit_boot_install.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/images.sh'.format(self.description_dir),
                    'root_dir/image/images.sh'
                ]
            ),
            call(
                [
                    'cp', '{0}/post_bootstrap.sh'.format(self.description_dir),
                    'root_dir/image/post_bootstrap.sh'
                ]
            ),
            call(
                [
                    'cp', Defaults.project_file('config/functions.sh'),
                    'root_dir/.kconfig'
                ]
            ),
            call(
                ['cp', '/absolute/path/to/image.tgz', 'root_dir/image/']
            ),
            call(
                ['cp', 'derived/description/bootstrap.tgz', 'root_dir/image/']
            )
        ]
        mock_create.assert_called_once_with('root_dir/image')

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_import_description_configured_editboot_scripts_not_found(
        self, mock_path, mock_command
    ):
        path_return_values = [False, True, True, True]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect
        with patch('builtins.open'):
            with raises(KiwiImportDescriptionError):
                self.setup_with_real_xml.import_description()

    @patch('kiwi.path.Path.create')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_import_description_configured_archives_not_found(
        self, mock_path, mock_command, mock_create
    ):
        path_return_values = [
            False, False, True, True, True, True, True, True
        ]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect

        with patch('builtins.open'):
            with raises(KiwiImportDescriptionError):
                self.setup_with_real_xml.import_description()

    @patch('kiwi.command.Command.run')
    def test_cleanup(self, mock_command):
        self.setup.cleanup()
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'rm', '-rf', '.kconfig', 'image']
        )

    @patch('kiwi.system.setup.ArchiveTar')
    @patch('kiwi.system.setup.glob.iglob')
    def test_import_cdroot_files(self, mock_iglob, mock_ArchiveTar):
        archive = Mock()
        mock_ArchiveTar.return_value = archive
        mock_iglob.return_value = ['config-cdroot.tar.xz']
        self.setup.import_cdroot_files('target_dir')
        mock_iglob.assert_called_once_with('description_dir/config-cdroot.tar*')
        mock_ArchiveTar.assert_called_once_with('config-cdroot.tar.xz')
        archive.extract.assert_called_once_with('target_dir')

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.setup.DataSync')
    @patch('os.path.exists')
    def test_import_overlay_files_copy_links(
        self, mock_os_path, mock_DataSync, mock_command
    ):
        data = Mock()
        mock_DataSync.return_value = data
        mock_os_path.return_value = True
        self.setup.import_overlay_files(
            follow_links=True, preserve_owner_group=True
        )
        mock_DataSync.assert_called_once_with(
            'description_dir/root/', 'root_dir'
        )
        data.sync_data.assert_called_once_with(
            options=[
                '-r', '-p', '-t', '-D', '-H', '-X', '-A',
                '--one-file-system', '--copy-links', '-o', '-g'
            ]
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.setup.DataSync')
    @patch('os.path.exists')
    def test_import_overlay_files_links(
        self, mock_os_path, mock_DataSync, mock_command
    ):
        data = Mock()
        mock_DataSync.return_value = data
        mock_os_path.return_value = True
        self.setup.import_overlay_files(
            follow_links=False, preserve_owner_group=True
        )
        mock_DataSync.assert_called_once_with(
            'description_dir/root/', 'root_dir'
        )
        data.sync_data.assert_called_once_with(
            options=[
                '-r', '-p', '-t', '-D', '-H', '-X', '-A',
                '--one-file-system', '--links', '-o', '-g'
            ]
        )

    @patch('kiwi.system.setup.ArchiveTar')
    @patch('os.path.exists')
    def test_import_overlay_files_from_archive(
        self, mock_os_path, mock_archive
    ):
        archive = Mock()
        mock_archive.return_value = archive

        exists_results = [True, False]

        def side_effect(arg):
            return exists_results.pop()

        mock_os_path.side_effect = side_effect

        self.setup.import_overlay_files()

        mock_archive.assert_called_once_with(
            'description_dir/root.tar.gz'
        )
        archive.extract.assert_called_once_with(
            'root_dir'
        )

    @patch('kiwi.system.setup.DataSync')
    @patch('os.path.exists')
    def test_import_overlay_files_from_profile(
        self, mock_os_path, mock_DataSync
    ):
        exists_results = [True, False, False]

        def side_effect(arg):
            return exists_results.pop()

        data = Mock()
        mock_DataSync.return_value = data
        mock_os_path.side_effect = side_effect
        self.xml_state.profiles = ['profile_root']
        self.setup.import_overlay_files()
        mock_DataSync.assert_called_once_with(
            'description_dir/profile_root/', 'root_dir'
        )
        data.sync_data.assert_called_once_with(
            options=[
                '-r', '-p', '-t', '-D', '-H', '-X', '-A',
                '--one-file-system', '--links'
            ]
        )

    @patch('kiwi.system.setup.Shell.run_common_function')
    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    def test_setup_keyboard_map(self, mock_path, mock_run, mock_shell):
        mock_path.return_value = True
        self.setup.preferences['keytable'] = 'keytable'
        self.setup.setup_keyboard_map()
        mock_shell.assert_called_once_with(
            'baseUpdateSysConfig', [
                'root_dir/etc/sysconfig/keyboard', 'KEYTABLE', '"keytable"'
            ]
        )

    @patch('kiwi.system.setup.CommandCapabilities.has_option_in_help')
    @patch('kiwi.system.setup.Shell.run_common_function')
    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    def test_setup_keyboard_map_with_systemd(
        self, mock_path, mock_run, mock_shell, mock_caps
    ):
        mock_caps.return_value = True
        mock_path.return_value = True
        self.setup.preferences['keytable'] = 'keytable'
        self.setup.setup_keyboard_map()
        mock_run.assert_has_calls([
            call(['rm', '-r', '-f', 'root_dir/etc/vconsole.conf']),
            call([
                'chroot', 'root_dir', 'systemd-firstboot',
                '--keymap=keytable'
            ])
        ])

    @patch('os.path.exists')
    def test_setup_keyboard_skipped(self, mock_exists):
        mock_exists.return_value = False
        self.setup.preferences['keytable'] = 'keytable'
        with self._caplog.at_level(logging.WARNING):
            self.setup.setup_keyboard_map()

    @patch('kiwi.system.setup.CommandCapabilities.has_option_in_help')
    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    def test_setup_locale(
        self, mock_path, mock_run, mock_caps
    ):
        mock_caps.return_valure = True
        mock_path.return_value = True
        self.setup.preferences['locale'] = 'locale1,locale2'
        self.setup.setup_locale()
        mock_run.assert_has_calls([
            call(['rm', '-r', '-f', 'root_dir/etc/locale.conf']),
            call([
                'chroot', 'root_dir', 'systemd-firstboot',
                '--locale=locale1.UTF-8'
            ])
        ])

    @patch('kiwi.system.setup.CommandCapabilities.has_option_in_help')
    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    def test_setup_locale_POSIX(self, mock_path, mock_run, mock_caps):
        mock_caps.return_valure = True
        mock_path.return_value = True
        self.setup.preferences['locale'] = 'POSIX,locale2'
        self.setup.setup_locale()
        mock_run.assert_has_calls([
            call(['rm', '-r', '-f', 'root_dir/etc/locale.conf']),
            call([
                'chroot', 'root_dir', 'systemd-firstboot',
                '--locale=POSIX'
            ])
        ])

    @patch('kiwi.system.setup.Command.run')
    def test_setup_timezone(self, mock_command):
        self.setup.preferences['timezone'] = 'timezone'
        self.setup.setup_timezone()
        mock_command.assert_has_calls([
            call([
                'chroot', 'root_dir', 'ln', '-s', '-f',
                '/usr/share/zoneinfo/timezone', '/etc/localtime'
            ])
        ])

    @patch('kiwi.system.setup.CommandCapabilities.has_option_in_help')
    @patch('kiwi.system.setup.Command.run')
    def test_setup_timezone_with_systemd(self, mock_command, mock_caps):
        mock_caps.return_value = True
        self.setup.preferences['timezone'] = 'timezone'
        self.setup.setup_timezone()
        mock_command.assert_has_calls([
            call([
                'chroot', 'root_dir', 'systemd-firstboot',
                '--timezone=timezone'
            ])
        ])

    @patch('kiwi.system.setup.Users')
    def test_setup_groups(self, mock_users):
        users = Mock()
        users.group_exists = Mock(
            return_value=False
        )
        mock_users.return_value = users

        self.setup_with_real_xml.setup_groups()

        calls = [
            call('users'),
            call('kiwi'),
            call('admin')
        ]
        users.group_exists.assert_has_calls(calls)

        calls = [
            call('users', []),
            call('kiwi', []),
            call('admin', [])
        ]
        users.group_add.assert_has_calls(calls)

    @patch('kiwi.system.setup.Users')
    @patch('kiwi.system.setup.Command.run')
    def test_setup_users_add(self, mock_command, mock_users):
        users = Mock()
        users.user_exists = Mock(
            return_value=False
        )
        mock_users.return_value = users
        mock_command.return_value = self.run_result

        self.setup_with_real_xml.setup_users()

        calls = [
            call('root'),
            call('tux'),
            call('kiwi')
        ]
        users.user_exists.assert_has_calls(calls)

        calls = [
            call(
                'root', [
                    '-p', 'password-hash',
                    '-s', '/bin/bash',
                    '-u', '815', '-c', 'Bob',
                    '-m', '-d', '/root'
                ]
            ),
            call(
                'tux', [
                    '-p', 'password-hash',
                    '-g', 'users',
                    '-m', '-d', '/home/tux'
                ]
            ),
            call(
                'kiwi', [
                    '-p', 'password-hash',
                    '-g', 'kiwi', '-G', 'admin,users', '-m'
                ]
            )
        ]
        users.user_add.assert_has_calls(calls)

        mock_command.assert_called_with(
            ['openssl', 'passwd', '-1', '-salt', 'xyz', 'mypwd']
        )

    @patch('kiwi.system.setup.Users')
    @patch('kiwi.system.setup.Command.run')
    def test_setup_users_modify(self, mock_command, mock_users):
        users = Mock()
        users.user_exists = Mock(
            return_value=True
        )
        mock_users.return_value = users
        mock_command.return_value = self.run_result

        self.setup_with_real_xml.setup_users()
        calls = [
            call('root'),
            call('tux'),
            call('kiwi')
        ]
        users.user_exists.assert_has_calls(calls)

        calls = [
            call(
                'root', [
                    '-p', 'password-hash',
                    '-s', '/bin/bash', '-u', '815', '-c', 'Bob'
                ]
            ),
            call(
                'tux', [
                    '-p', 'password-hash',
                    '-g', 'users'
                ]
            ),
            call(
                'kiwi', [
                    '-p', 'password-hash',
                    '-g', 'kiwi', '-G', 'admin,users'
                ]
            )
        ]
        users.user_modify.assert_has_calls(calls)

    @patch('kiwi.system.setup.Path.which')
    @patch('kiwi.system.setup.Command.run')
    def test_setup_plymouth_splash(self, mock_command, mock_which):
        mock_which.return_value = 'plymouth-set-default-theme'
        preferences = Mock()
        preferences.get_bootsplash_theme = Mock(
            return_value=['some-theme']
        )
        self.xml_state.get_preferences_sections = Mock(
            return_value=[preferences]
        )
        self.setup.setup_plymouth_splash()
        mock_which.assert_called_once_with(
            root_dir='root_dir',
            filename='plymouth-set-default-theme'
        )
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'plymouth-set-default-theme', 'some-theme']
        )

    @patch('os.path.exists')
    def test_import_image_identifier(self, mock_os_path):
        self.xml_state.xml_data.get_id = Mock(
            return_value='42'
        )
        mock_os_path.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.setup.import_image_identifier()

        m_open.assert_called_once_with('root_dir/etc/ImageID', 'w')
        m_open.return_value.write.assert_called_once_with('42\n')

    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    @patch('copy.deepcopy')
    def test_call_non_excutable_config_script(
        self, mock_copy_deepcopy, mock_access, mock_stat, mock_os_path,
        mock_watch, mock_command, mock_Profile
    ):
        mock_copy_deepcopy.return_value = {}
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        mock_access.return_value = False

        self.setup.call_config_script()
        mock_copy_deepcopy.assert_called_once_with(os.environ)
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'bash', 'image/config.sh'], {}
        )

    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    @patch('copy.deepcopy')
    def test_call_excutable_config_script(
        self, mock_copy_deepcopy, mock_access, mock_stat, mock_os_path,
        mock_watch, mock_command, mock_Profile
    ):
        mock_copy_deepcopy.return_value = {}
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result

        # pretend that the script is executable
        mock_access.return_value = True
        self.setup.call_config_script()

        mock_copy_deepcopy.assert_called_once_with(os.environ)
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'image/config.sh'], {}
        )

    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    @patch('copy.deepcopy')
    def test_call_excutable_post_bootstrap_script(
        self, mock_copy_deepcopy, mock_access, mock_stat, mock_os_path,
        mock_watch, mock_command, mock_Profile
    ):
        mock_copy_deepcopy.return_value = {}
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result

        # pretend that the script is executable
        mock_access.return_value = True
        self.setup.call_post_bootstrap_script()

        mock_copy_deepcopy.assert_called_once_with(os.environ)
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'image/post_bootstrap.sh'], {}
        )

    @patch('kiwi.system.setup.Defaults.is_buildservice_worker')
    @patch('kiwi.logger.Logger.getLogLevel')
    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    @patch('copy.deepcopy')
    def test_call_disk_script(
        self, mock_copy_deepcopy, mock_access, mock_stat, mock_os_path,
        mock_watch, mock_command, mock_Profile, mock_getLogLevel,
        mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = False
        mock_getLogLevel.return_value = logging.DEBUG
        mock_copy_deepcopy.return_value = {}
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        mock_access.return_value = False

        self.setup.call_disk_script()
        mock_copy_deepcopy.assert_called_once_with(os.environ)
        mock_command.assert_called_once_with(
            [
                'screen', '-t', '-X',
                'chroot', 'root_dir', 'bash', 'image/disk.sh'
            ], {}
        )

    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    @patch('copy.deepcopy')
    def test_call_image_script(
        self, mock_copy_deepcopy, mock_access, mock_stat, mock_os_path,
        mock_watch, mock_command, mock_Profile
    ):
        mock_copy_deepcopy.return_value = {}
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        mock_access.return_value = False

        self.setup.call_image_script()
        mock_copy_deepcopy.assert_called_once_with(os.environ)
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'bash', 'image/images.sh'], {}
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_call_edit_boot_config_script(
        self, mock_abspath, mock_exists, mock_watch, mock_command
    ):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_exists.return_value = True
        mock_abspath.return_value = '/root_dir/image/edit_boot_config.sh'
        mock_watch.return_value = mock_result
        self.setup.call_edit_boot_config_script('ext4', 1)
        mock_abspath.assert_called_once_with(
            'root_dir/image/edit_boot_config.sh'
        )
        mock_command.assert_called_once_with([
            'bash', '-c',
            'cd root_dir && bash --norc /root_dir/image/edit_boot_config.sh '
            'ext4 1'
        ])

    @patch('kiwi.system.setup.Defaults.is_buildservice_worker')
    @patch('kiwi.logger.Logger.getLogLevel')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_call_edit_boot_install_script(
        self, mock_abspath, mock_exists, mock_watch, mock_command,
        mock_getLogLevel, mock_is_buildservice_worker
    ):
        mock_is_buildservice_worker.return_value = False
        mock_getLogLevel.return_value = logging.DEBUG
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_exists.return_value = True
        mock_abspath.return_value = '/root_dir/image/edit_boot_install.sh'
        mock_watch.return_value = mock_result
        self.setup.call_edit_boot_install_script(
            'my_image.raw', '/dev/mapper/loop0p1'
        )
        mock_abspath.assert_called_once_with(
            'root_dir/image/edit_boot_install.sh'
        )
        mock_command.assert_called_once_with(
            [
                'screen', '-t', '-X',
                'bash', '-c',
                'cd root_dir && bash --norc '
                '/root_dir/image/edit_boot_install.sh '
                'my_image.raw /dev/mapper/loop0p1'
            ]
        )

    @patch('kiwi.system.setup.Profile')
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('os.access')
    def test_call_image_script_raises(
        self, mock_access, mock_stat, mock_os_path, mock_watch,
        mock_command, mock_Profile
    ):
        profile = Mock()
        mock_Profile.return_value = profile
        profile.get_settings.return_value = {}
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=1)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        mock_access.return_value = False
        with raises(KiwiScriptFailed):
            self.setup.call_image_script()

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_edit_boot_install_script_raises(
        self, mock_os_path, mock_watch, mock_command
    ):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=1)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        with raises(KiwiScriptFailed):
            self.setup.call_edit_boot_install_script(
                'my_image.raw', '/dev/mapper/loop0p1'
            )

    @patch('kiwi.command.Command.run')
    def test_create_init_link_from_linuxrc(self, mock_command):
        self.setup.create_init_link_from_linuxrc()
        mock_command.assert_called_once_with(
            ['ln', 'root_dir/linuxrc', 'root_dir/init']
        )

    @patch('kiwi.command.Command.run')
    def test_create_recovery_archive_cleanup_only(self, mock_command):
        self.setup.oemconfig['recovery'] = False
        self.setup.create_recovery_archive()
        assert mock_command.call_args_list[0] == call(
            ['bash', '-c', 'rm -f root_dir/recovery.*']
        )

    @patch('os.path.exists')
    @patch('kiwi.system.setup.Path.wipe')
    @patch('kiwi.command.Command.run')
    def test_create_fstab(
        self, mock_command, mock_wipe, mock_exists
    ):
        fstab = Mock()
        mock_exists.return_value = True

        m_open = mock_open(read_data='append_entry')
        with patch('builtins.open', m_open, create=True):
            self.setup.create_fstab(fstab)

        fstab.export.assert_called_once_with('root_dir/etc/fstab')

        assert m_open.call_args_list == [
            call('root_dir/etc/fstab', 'a'),
            call('root_dir/etc/fstab.append', 'r')
        ]
        assert m_open.return_value.write.call_args_list == [
            call('append_entry')
        ]
        assert mock_command.call_args_list == [
            call(['patch', 'root_dir/etc/fstab', 'root_dir/etc/fstab.patch']),
            call(['chroot', 'root_dir', '/etc/fstab.script'])
        ]
        assert mock_wipe.call_args_list == [
            call('root_dir/etc/fstab.append'),
            call('root_dir/etc/fstab.patch'),
            call('root_dir/etc/fstab.script')
        ]

    @patch('kiwi.command.Command.run')
    @patch('pathlib.Path.touch')
    @patch('kiwi.system.setup.ArchiveTar')
    @patch('kiwi.system.setup.Compress')
    @patch('os.path.getsize')
    @patch('kiwi.system.setup.Path.wipe')
    def test_create_recovery_archive(
        self, mock_wipe, mock_getsize, mock_compress,
        mock_archive, mock_pathlib_Path_touch, mock_command
    ):
        mock_getsize.return_value = 42
        compress = Mock()
        mock_compress.return_value = compress
        archive = Mock()
        mock_archive.return_value = archive
        self.setup.oemconfig['recovery'] = True
        self.setup.oemconfig['recovery_inplace'] = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.setup.create_recovery_archive()

        assert mock_command.call_args_list[0] == call(
            ['bash', '-c', 'rm -f root_dir/recovery.*']
        )
        mock_archive.assert_called_once_with(
            create_from_file_list=False, filename='root_dir/recovery.tar'
        )
        archive.create.assert_called_once_with(
            exclude=['dev', 'proc', 'sys'],
            options=[
                '--numeric-owner',
                '--hard-dereference',
                '--preserve-permissions'
            ],
            source_dir='root_dir'
        )
        assert m_open.call_args_list[0] == call(
            'root_dir/recovery.tar.filesystem', 'w'
        )
        assert m_open.return_value.write.call_args_list[0] == call('ext3')

        assert mock_command.call_args_list[1] == call(
            ['bash', '-c', 'tar -tf root_dir/recovery.tar | wc -l']
        )
        assert m_open.call_args_list[1] == call(
            'root_dir/recovery.tar.files', 'w'
        )
        assert mock_getsize.call_args_list[0] == call(
            'root_dir/recovery.tar'
        )
        assert m_open.return_value.write.call_args_list[1] == call('1\n')
        assert m_open.call_args_list[2] == call(
            'root_dir/recovery.tar.size', 'w'
        )
        assert m_open.return_value.write.call_args_list[2] == call('42')
        mock_compress.assert_called_once_with(
            'root_dir/recovery.tar'
        )
        compress.gzip.assert_called_once_with()
        assert mock_getsize.call_args_list[1] == call(
            'root_dir/recovery.tar.gz'
        )
        assert m_open.call_args_list[3] == call(
            'root_dir/recovery.partition.size', 'w'
        )
        assert m_open.return_value.write.call_args_list[3] == call('300')
        mock_wipe.assert_called_once_with(
            'root_dir/recovery.tar.gz'
        )

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.Path.create')
    @patch('kiwi.system.setup.DataSync')
    @patch('os.path.exists')
    def test_export_modprobe_setup(
        self, mock_exists, mock_DataSync, mock_path, mock_command
    ):
        data = Mock()
        mock_DataSync.return_value = data
        mock_exists.return_value = True
        self.setup.export_modprobe_setup('target_root_dir')
        mock_path.assert_called_once_with('target_root_dir/etc')
        mock_DataSync.assert_called_once_with(
            'root_dir/etc/modprobe.d', 'target_root_dir/etc/'
        )
        data.sync_data.assert_called_once_with(
            options=['-a']
        )

    @patch('kiwi.defaults.Defaults.get_default_packager_tool')
    def test_export_package_list_unknown_packager(
        self, mock_get_default_packager_tool
    ):
        assert self.setup.export_package_list('target_dir') == ''

    @patch('kiwi.defaults.Defaults.get_default_packager_tool')
    def test_export_package_changes_unknown_packager(
        self, mock_get_default_packager_tool
    ):
        assert self.setup.export_package_changes('target_dir') == ''

    @patch('kiwi.defaults.Defaults.get_default_packager_tool')
    def test_export_package_verification_unknown_packager(
        self, mock_get_default_packager_tool
    ):
        assert self.setup.export_package_verification('target_dir') == ''

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.RpmDataBase')
    @patch('kiwi.system.setup.MountManager')
    def test_export_package_list_rpm(
        self, mock_MountManager, mock_RpmDataBase, mock_command
    ):
        rpmdb = Mock()
        rpmdb.rpmdb_image.expand_query.return_value = 'image_dbpath'
        rpmdb.rpmdb_host.expand_query.return_value = 'host_dbpath'
        rpmdb.has_rpm.return_value = True
        mock_RpmDataBase.return_value = rpmdb
        command = Mock()
        command.output = 'packages_data'
        mock_command.return_value = command

        with patch('builtins.open') as m_open:
            result = self.setup.export_package_list('target_dir')
            m_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.packages', 'w',
                encoding='utf-8'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.packages'
        mock_command.assert_called_once_with(
            [
                'rpm', '--root', 'root_dir', '-qa', '--qf',
                '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|'
                '%{DISTURL}|%{LICENSE}\\n',
                '--dbpath', 'image_dbpath'
            ]
        )
        rpmdb.has_rpm.return_value = False
        mock_command.reset_mock()

        with patch('builtins.open'):
            result = self.setup.export_package_list('target_dir')

        assert result == 'target_dir/some-image.x86_64-1.2.3.packages'
        mock_command.assert_called_once_with(
            [
                'rpm', '--root', 'root_dir', '-qa', '--qf',
                '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|'
                '%{DISTURL}|%{LICENSE}\\n',
                '--dbpath', 'host_dbpath'
            ]
        )

    @patch('kiwi.system.setup.os.path.exists')
    def test_setup_machine_id(self, mock_path_exists):
        mock_path_exists.return_value = True

        with patch('builtins.open') as m_open:
            self.setup.setup_machine_id()
            m_open.assert_called_once_with(
                'root_dir/etc/machine-id', 'w'
            )

        mock_path_exists.return_value = False

        self.setup.setup_machine_id()

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.Path.which')
    def test_setup_permissions(
        self, mock_path_which, mock_command
    ):
        mock_path_which.return_value = 'chkstat'
        self.setup.setup_permissions()
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'chkstat', '--system', '--set']
        )
        mock_path_which.return_value = None
        with self._caplog.at_level(logging.WARNING):
            self.setup.setup_permissions()

    @patch('kiwi.system.setup.Command.run')
    def test_export_package_list_dpkg(self, mock_command):
        command = Mock()
        command.output = 'packages_data'
        mock_command.return_value = command
        self.xml_state.get_package_manager = Mock(
            return_value='apt'
        )

        with patch('builtins.open') as m_open:
            result = self.setup.export_package_list('target_dir')
            m_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.packages', 'w',
                encoding='utf-8'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.packages'
        mock_command.assert_called_once_with([
            'dpkg-query', '--admindir', 'root_dir/var/lib/dpkg', '-W',
            '-f', '${Package}|None|${Version}|None|${Architecture}|None|None\\n'
        ])

    @patch('kiwi.system.setup.Command.run')
    def test_export_package_list_pacman(self, mock_command):
        command = Mock()
        command.output = 'packages_data'
        mock_command.return_value = command
        self.xml_state.get_package_manager = Mock(
            return_value='pacman'
        )

        with patch('builtins.open') as m_open:
            result = self.setup.export_package_list('target_dir')
            m_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.packages', 'w'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.packages'
        mock_command.assert_called_once_with(
            ['pacman', '--query', '--dbpath', 'root_dir/var/lib/pacman']
        )

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.RpmDataBase')
    @patch('kiwi.system.setup.MountManager')
    def test_export_package_changes_rpm(
        self, mock_MountManager, mock_RpmDataBase, mock_command
    ):
        rpmdb = Mock()
        rpmdb.rpmdb_image.expand_query.return_value = 'image_dbpath'
        rpmdb.rpmdb_host.expand_query.return_value = 'host_dbpath'
        rpmdb.has_rpm.return_value = True
        mock_RpmDataBase.return_value = rpmdb
        command = Mock()
        command.output = 'package|\nchanges'
        mock_command.return_value = command

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            result = self.setup.export_package_changes('target_dir')
            mock_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.changes', 'w',
                encoding='utf-8'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.changes'
        mock_command.assert_called_once_with(
            [
                'rpm', '--root', 'root_dir', '-qa', '--qf',
                '%{NAME}|\\n', '--changelog', '--dbpath', 'image_dbpath'
            ]
        )
        self.runtime_config.get_package_changes.assert_called_once_with()

    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_export_package_changes_dpkg(
        self, mock_os_listdir, mock_os_path_exists, mock_command
    ):
        command = Mock()
        command.output = 'changes'
        mock_command.return_value = command
        self.xml_state.get_package_manager = Mock(
            return_value='apt'
        )
        mock_os_listdir.return_value = ['package_b', 'package_a']
        mock_os_path_exists.return_value = True

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            result = self.setup.export_package_changes('target_dir')
            file_handle = mock_open.return_value.__enter__.return_value
            mock_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.changes', 'w',
                encoding='utf-8'
            )
            assert result == 'target_dir/some-image.x86_64-1.2.3.changes'
            assert file_handle.write.call_args_list == [
                call('package_a|\n'),
                call('changes\n'),
                call('package_b|\n'),
                call('changes\n')
            ]
        self.runtime_config.get_package_changes.assert_called_once_with()

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.RpmDataBase')
    @patch('kiwi.system.setup.MountManager')
    def test_export_package_verification(
        self, mock_MountManager, mock_RpmDataBase, mock_command
    ):
        is_mounted_return = [True, False]

        def is_mounted():
            return is_mounted_return.pop()

        shared_mount = Mock()
        shared_mount.is_mounted.side_effect = is_mounted
        mock_MountManager.return_value = shared_mount
        rpmdb = Mock()
        rpmdb.rpmdb_image.expand_query.return_value = 'image_dbpath'
        rpmdb.rpmdb_host.expand_query.return_value = 'host_dbpath'
        rpmdb.has_rpm.return_value = True
        mock_RpmDataBase.return_value = rpmdb
        command = Mock()
        command.output = 'verification_data'
        mock_command.return_value = command

        with patch('builtins.open') as m_open:
            result = self.setup.export_package_verification('target_dir')
            m_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.verified', 'w',
                encoding='utf-8'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.verified'
        mock_command.assert_called_once_with(
            command=[
                'rpm', '--root', 'root_dir', '-Va',
                '--dbpath', 'image_dbpath'
            ], raise_on_error=False
        )

        mock_MountManager.assert_called_once_with(
            device='/dev', mountpoint='root_dir/dev'
        )
        shared_mount.bind_mount.assert_called_once_with()
        shared_mount.umount_lazy.assert_called_once_with()
        rpmdb.has_rpm.return_value = False
        is_mounted_return = [True, False]
        mock_command.reset_mock()
        shared_mount.reset_mock()

        with patch('builtins.open'):
            result = self.setup.export_package_verification('target_dir')

        assert result == 'target_dir/some-image.x86_64-1.2.3.verified'
        mock_command.assert_called_once_with(
            command=[
                'rpm', '--root', 'root_dir', '-Va',
                '--dbpath', 'host_dbpath'
            ], raise_on_error=False
        )
        shared_mount.bind_mount.assert_called_once_with()
        shared_mount.umount_lazy.assert_called_once_with()

    @patch('kiwi.system.setup.Command.run')
    def test_export_package_verification_dpkg(self, mock_command):
        command = Mock()
        command.output = 'verification_data'
        mock_command.return_value = command
        self.xml_state.get_package_manager = Mock(
            return_value='apt'
        )

        with patch('builtins.open') as m_open:
            result = self.setup.export_package_verification('target_dir')
            m_open.assert_called_once_with(
                'target_dir/some-image.x86_64-1.2.3.verified', 'w',
                encoding='utf-8'
            )

        assert result == 'target_dir/some-image.x86_64-1.2.3.verified'
        mock_command.assert_called_once_with(
            command=[
                'dpkg', '--root', 'root_dir', '-V',
                '--verify-format', 'rpm'
            ],
            raise_on_error=False
        )

    @patch('kiwi.system.setup.Command.run')
    def test_set_selinux_file_contexts(self, mock_command):
        self.setup.set_selinux_file_contexts('security_context_file')
        mock_command.assert_called_once_with(
            [
                'chroot', 'root_dir',
                'setfiles', 'security_context_file', '/', '-v'
            ]
        )

    @patch('kiwi.system.setup.Repository.new')
    @patch('kiwi.system.setup.Uri')
    def test_import_repositories_marked_as_imageinclude(
        self, mock_uri, mock_repo
    ):
        uri = Mock()
        mock_uri.return_value = uri
        uri.translate = Mock(
            return_value="uri"
        )
        uri.alias = Mock(
            return_value="uri-alias"
        )
        uri.credentials_file_name = Mock(
            return_value='kiwiRepoCredentials'
        )
        mock_uri.return_value = uri
        repo = Mock()
        mock_repo.return_value = repo
        self.setup_with_real_xml.import_repositories_marked_as_imageinclude()
        assert repo.add_repo.call_args_list[0] == call(
            'uri-alias', 'uri', 'rpm-md', None, None, None, None, None,
            'kiwiRepoCredentials', None, None, None, False, '../data/script'
        )

    @patch('os.path.exists')
    def test_script_exists(self, mock_path_exists):
        assert self.setup.script_exists('some-script') == \
            mock_path_exists.return_value
