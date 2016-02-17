from nose.tools import *
from mock import patch
from mock import call

import mock

from . import nose_helper
from collections import namedtuple

from kiwi.system_setup import SystemSetup
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.exceptions import *
from kiwi.defaults import Defaults


class TestSystemSetup(object):
    def setup(self):
        self.xml_state = mock.MagicMock()
        self.xml_state.build_type.get_filesystem = mock.Mock(
            return_value='ext3'
        )
        self.setup = SystemSetup(
            self.xml_state, 'description_dir', 'root_dir'
        )
        description = XMLDescription('../data/example_config.xml')
        self.setup_with_real_xml = SystemSetup(
            XMLState(description.load()), 'description_dir', 'root_dir'
        )
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        self.run_result = command_run(
            output='password-hash',
            error='stderr',
            returncode=0
        )

    @patch('kiwi.command.Command.run')
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_import_description(self, mock_path, mock_open, mock_command):
        mock_path.return_value = True
        self.setup_with_real_xml.import_description()
        assert mock_command.call_args_list == [
            call(['mkdir', '-p', 'root_dir/image']),
            call([
                'cp', 'description_dir/my_edit_boot_script',
                'root_dir/image/edit_boot_config.sh'
            ]),
            call([
                'cp', 'description_dir/my_edit_boot_install',
                'root_dir/image/edit_boot_install.sh'
            ]),
            call(['cp', 'description_dir/config.sh', 'root_dir/image/']),
            call(['cp', 'description_dir/images.sh', 'root_dir/image/']),
            call([
                'cp', Defaults.project_file('config/functions.sh'),
                'root_dir/.kconfig'
            ])
        ]

    @patch('kiwi.command.Command.run')
    @patch('builtins.open')
    @patch('os.path.exists')
    @raises(KiwiScriptFailed)
    def test_import_description_configured_editboot_scripts_not_found(
        self, mock_path, mock_open, mock_command
    ):
        mock_path.return_value = False
        self.setup_with_real_xml.import_description()

    @patch('kiwi.command.Command.run')
    def test_cleanup(self, mock_command):
        self.setup.cleanup()
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', '/.kconfig', '/image']
        )

    @patch('builtins.open')
    def test_import_shell_environment(self, mock_open):
        mock_profile = mock.MagicMock()
        mock_profile.create = mock.Mock(
            return_value=['a']
        )
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.setup.import_shell_environment(mock_profile)

        mock_profile.create.assert_called_once_with()
        mock_open.assert_called_once_with('root_dir/.profile', 'w')
        file_mock.write.assert_called_once_with('a\n')

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_import_overlay_files_copy_links(self, mock_os_path, mock_command):
        mock_os_path.return_value = True
        self.setup.import_overlay_files(
            follow_links=True, preserve_owner_group=True
        )
        mock_command.assert_called_once_with(
            [
                'rsync', '-r', '-p', '-t', '-D', '-H', '-X', '-A',
                '--one-file-system', '--copy-links', '-o', '-g',
                'description_dir/root/', 'root_dir'
            ]
        )

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_import_overlay_files_links(self, mock_os_path, mock_command):
        mock_os_path.return_value = True
        self.setup.import_overlay_files(
            follow_links=False, preserve_owner_group=True
        )
        mock_command.assert_called_once_with(
            [
                'rsync', '-r', '-p', '-t', '-D', '-H', '-X', '-A',
                '--one-file-system', '--links', '-o', '-g',
                'description_dir/root/', 'root_dir'
            ]
        )

    @patch('kiwi.system_setup.ArchiveTar')
    @patch('os.path.exists')
    def test_import_overlay_files_from_archive(
        self, mock_os_path, mock_archive
    ):
        archive = mock.Mock()
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

    @patch('kiwi.system_setup.Command.run')
    def test_setup_hardware_clock(self, mock_command):
        self.setup.preferences['hwclock'] = 'clock'
        self.setup.setup_hardware_clock()
        mock_command.assert_called_once_with(
            [
                'chroot', 'root_dir', 'hwclock', '--adjust', '--clock'
            ]
        )

    @patch('kiwi.system_setup.Shell.run_common_function')
    @patch('os.path.exists')
    def test_setup_keyboard_map(self, mock_path, mock_shell):
        mock_path.return_value = True
        self.setup.preferences['keytable'] = 'keytable'
        self.setup.setup_keyboard_map()
        mock_shell.assert_called_once_with(
            'baseUpdateSysConfig', [
                'root_dir/etc/sysconfig/keyboard', 'KEYTABLE', '"keytable"'
            ]
        )

    @patch('kiwi.logger.log.warning')
    @patch('os.path.exists')
    def test_setup_keyboard_skipped(self, mock_exists, mock_log_warn):
        mock_exists.return_value = False
        self.setup.preferences['keytable'] = 'keytable'
        self.setup.setup_keyboard_map()
        assert mock_log_warn.called

    @patch('kiwi.system_setup.Shell.run_common_function')
    @patch('os.path.exists')
    def test_setup_locale(self, mock_path, mock_shell):
        mock_path.return_value = True
        self.setup.preferences['locale'] = 'locale1,locale2'
        self.setup.setup_locale()
        mock_shell.assert_called_once_with(
            'baseUpdateSysConfig', [
                'root_dir/etc/sysconfig/language', 'RC_LANG', 'locale1.UTF-8'
            ]
        )

    @patch('kiwi.logger.log.warning')
    @patch('os.path.exists')
    def test_setup_locale_skipped(self, mock_exists, mock_log_warn):
        mock_exists.return_value = False
        self.setup.preferences['locale'] = 'locale1,locale2'
        self.setup.setup_locale()
        assert mock_log_warn.called

    @patch('kiwi.system_setup.Command.run')
    def test_setup_timezone(self, mock_command):
        self.setup.preferences['timezone'] = 'timezone'
        self.setup.setup_timezone()
        mock_command.assert_called_once_with([
            'chroot', 'root_dir', 'ln', '-s', '-f',
            '/usr/share/zoneinfo/timezone', '/etc/localtime'
        ])

    @patch('kiwi.system_setup.Users')
    def test_setup_groups(self, mock_users):
        users = mock.Mock()
        users.group_exists = mock.Mock(
            return_value=False
        )
        mock_users.return_value = users

        self.setup_with_real_xml.setup_groups()

        users.group_exists.assert_called_once_with('root')
        users.group_add.assert_called_once_with('root', ['-g', 42])

    @patch('kiwi.system_setup.Users')
    @patch('kiwi.system_setup.Command.run')
    def test_setup_users_add(self, mock_command, mock_users):
        users = mock.Mock()
        users.user_exists = mock.Mock(
            return_value=False
        )
        mock_users.return_value = users
        mock_command.return_value = self.run_result

        self.setup_with_real_xml.setup_users()

        users.user_exists.assert_called_once_with('root')
        users.user_add.assert_called_once_with(
            'root', [
                '-p', 'password-hash',
                '-s', '/bin/bash', '-g', 42, '-u', 815, '-c', 'Bob',
                '-m', '-d', '/root'
            ]
        )
        mock_command.assert_called_once_with(
            ['openssl', 'passwd', '-1', '-salt', 'xyz', 'mypwd']
        )

    @patch('kiwi.system_setup.Users')
    @patch('kiwi.system_setup.Command.run')
    def test_setup_users_modify(self, mock_command, mock_users):
        users = mock.Mock()
        users.user_exists = mock.Mock(
            return_value=True
        )
        mock_users.return_value = users
        mock_command.return_value = self.run_result

        self.setup_with_real_xml.setup_users()

        users.user_exists.assert_called_once_with('root')
        users.user_modify.assert_called_once_with(
            'root', [
                '-p', 'password-hash',
                '-s', '/bin/bash', '-g', 42, '-u', 815, '-c', 'Bob'
            ]
        )

    @patch('kiwi.system_setup.Users')
    @patch('kiwi.system_setup.Command.run')
    def test_setup_users_modify_group_name(self, mock_command, mock_users):
        # unset group id and expect use of group name now
        self.setup_with_real_xml.xml_state.xml_data.get_users()[0].set_id(None)
        users = mock.Mock()
        users.user_exists = mock.Mock(
            return_value=True
        )
        mock_users.return_value = users
        mock_command.return_value = self.run_result

        self.setup_with_real_xml.setup_users()

        users.user_modify.assert_called_once_with(
            'root', [
                '-p', 'password-hash',
                '-s', '/bin/bash', '-g', 'root', '-u', 815, '-c', 'Bob'
            ]
        )

    @patch('builtins.open')
    @patch('os.path.exists')
    def test_import_image_identifier(self, mock_os_path, mock_open):
        self.xml_state.xml_data.get_id = mock.Mock(
            return_value='42'
        )
        mock_os_path.return_value = True
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.setup.import_image_identifier()

        mock_open.assert_called_once_with('root_dir/etc/ImageID', 'w')
        file_mock.write.assert_called_once_with('42\n')

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_config_script(self, mock_os_path, mock_watch, mock_command):
        result_type = namedtuple(
            'result', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        self.setup.call_config_script()
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'bash', '/image/config.sh']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_image_script(self, mock_os_path, mock_watch, mock_command):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        self.setup.call_image_script()
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'bash', '/image/images.sh']
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_edit_boot_config_script(
        self, mock_os_path, mock_watch, mock_command
    ):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        self.setup.call_edit_boot_config_script('ext4', 1)
        mock_command.assert_called_once_with([
            'bash', '-c',
            'cd root_dir && bash --norc image/edit_boot_config.sh ext4 1'
        ])

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_edit_boot_install_script(
        self, mock_os_path, mock_watch, mock_command
    ):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=0)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        self.setup.call_edit_boot_install_script(
            'my_image.raw', '/dev/mapper/loop0p1'
        )
        mock_command.assert_called_once_with([
            'bash', '-c',
            'cd root_dir && bash --norc image/edit_boot_install.sh my_image.raw /dev/mapper/loop0p1'
        ])

    @raises(KiwiScriptFailed)
    @patch('kiwi.command.Command.call')
    @patch('kiwi.command_process.CommandProcess.poll_and_watch')
    @patch('os.path.exists')
    def test_call_image_script_raises(
        self, mock_os_path, mock_watch, mock_command
    ):
        result_type = namedtuple(
            'result_type', ['stderr', 'returncode']
        )
        mock_result = result_type(stderr='stderr', returncode=1)
        mock_os_path.return_value = True
        mock_watch.return_value = mock_result
        self.setup.call_image_script()

    @raises(KiwiScriptFailed)
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

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system_setup.NamedTemporaryFile')
    @patch('kiwi.system_setup.ArchiveTar')
    @patch('builtins.open')
    @patch('kiwi.system_setup.Compress')
    @patch('os.path.getsize')
    @patch('kiwi.system_setup.Path.wipe')
    def test_create_recovery_archive(
        self, mock_wipe, mock_getsize, mock_compress,
        mock_open, mock_archive, mock_temp, mock_command
    ):
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        mock_getsize.return_value = 42
        compress = mock.Mock()
        mock_compress.return_value = compress
        archive = mock.Mock()
        mock_archive.return_value = archive
        tmpdir = mock.Mock()
        tmpdir.name = 'tmpdir'
        mock_temp.return_value = tmpdir
        self.setup.oemconfig['recovery'] = True
        self.setup.oemconfig['recovery_inplace'] = True

        self.setup.create_recovery_archive()

        assert mock_command.call_args_list[0] == call(
            ['bash', '-c', 'rm -f root_dir/recovery.*']
        )
        mock_archive.assert_called_once_with(
            create_from_file_list=False, filename='tmpdir'
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
        assert mock_command.call_args_list[1] == call(
            ['mv', 'tmpdir', 'root_dir/recovery.tar']
        )
        assert mock_open.call_args_list[0] == call(
            'root_dir/recovery.tar.filesystem', 'w'
        )
        assert file_mock.write.call_args_list[0] == call('ext3')
        assert mock_command.call_args_list[2] == call(
            ['bash', '-c', 'tar -tf root_dir/recovery.tar | wc -l']
        )
        assert mock_open.call_args_list[1] == call(
            'root_dir/recovery.tar.files', 'w'
        )
        assert mock_getsize.call_args_list[0] == call(
            'root_dir/recovery.tar'
        )
        assert file_mock.write.call_args_list[1] == call('1\n')
        assert mock_open.call_args_list[2] == call(
            'root_dir/recovery.tar.size', 'w'
        )
        assert file_mock.write.call_args_list[2] == call('42')
        mock_compress.assert_called_once_with(
            'root_dir/recovery.tar'
        )
        compress.gzip.assert_called_once_with()
        assert mock_getsize.call_args_list[1] == call(
            'root_dir/recovery.tar.gz'
        )
        assert mock_open.call_args_list[3] == call(
            'root_dir/recovery.partition.size', 'w'
        )
        assert file_mock.write.call_args_list[3] == call('300')
        mock_wipe.assert_called_once_with(
            'root_dir/recovery.tar.gz'
        )

    @patch('kiwi.system_setup.Command.run')
    @patch('kiwi.system_setup.Path.create')
    @patch('os.path.exists')
    def test_export_modprobe_setup(self, mock_exists, mock_path, mock_command):
        mock_exists.return_value = True
        self.setup.export_modprobe_setup('target_root_dir')
        mock_path.assert_called_once_with('target_root_dir/etc')
        mock_command.assert_called_once_with(
            ['rsync', '-zav', 'root_dir/etc/modprobe.d', 'target_root_dir/etc/']
        )
