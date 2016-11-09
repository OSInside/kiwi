
from mock import patch
from mock import call

import mock

from .test_helper import *
from collections import namedtuple

from kiwi.system.setup import SystemSetup
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.exceptions import *
from kiwi.defaults import Defaults


class TestSystemSetup(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        self.xml_state = mock.MagicMock()
        self.xml_state.build_type.get_filesystem = mock.Mock(
            return_value='ext3'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='some-image'
        )
        self.xml_state.get_image_version = mock.Mock(
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

    @patch('platform.machine')
    def test_setup_ix86(self, mock_machine):
        mock_machine.return_value = 'i686'
        setup = SystemSetup(
            mock.MagicMock(), 'root_dir'
        )
        assert setup.arch == 'ix86'

    @patch('kiwi.command.Command.run')
    @patch_open
    @patch('os.path.exists')
    def test_import_description(self, mock_path, mock_open, mock_command):
        mock_path.return_value = True
        self.setup_with_real_xml.import_description()

        assert mock_command.call_args_list == [
            call(['mkdir', '-p', 'root_dir/image']),
            call(['cp', '../data/config.sh', 'root_dir/image/config.sh']),
            call([
                'cp', '../data/my_edit_boot_script',
                'root_dir/image/edit_boot_config.sh'
            ]),
            call([
                'cp', '/absolute/path/to/my_edit_boot_install',
                'root_dir/image/edit_boot_install.sh'
            ]),
            call(['cp', '../data/images.sh', 'root_dir/image/images.sh']),
            call([
                'cp', Defaults.project_file('config/functions.sh'),
                'root_dir/.kconfig'
            ]),
            call(['cp', '/absolute/path/to/image.tgz', 'root_dir/image/']),
            call(['cp', '../data/bootstrap.tgz', 'root_dir/image/'])]

    @patch('kiwi.command.Command.run')
    @patch_open
    @patch('os.path.exists')
    def test_import_description_archive_from_derived(
        self, mock_path, mock_open, mock_command
    ):
        path_return_values = [
            True, False, True, True, True, True, True
        ]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect
        self.setup_with_real_xml.import_description()

        assert mock_command.call_args_list == [
            call(['mkdir', '-p', 'root_dir/image']),
            call(['cp', '../data/config.sh', 'root_dir/image/config.sh']),
            call([
                'cp', '../data/my_edit_boot_script',
                'root_dir/image/edit_boot_config.sh'
            ]),
            call([
                'cp', '/absolute/path/to/my_edit_boot_install',
                'root_dir/image/edit_boot_install.sh'
            ]),
            call(['cp', '../data/images.sh', 'root_dir/image/images.sh']),
            call([
                'cp', Defaults.project_file('config/functions.sh'),
                'root_dir/.kconfig'
            ]),
            call(['cp', '/absolute/path/to/image.tgz', 'root_dir/image/']),
            call([
                'cp', 'derived/description/bootstrap.tgz', 'root_dir/image/'
            ])
        ]

    @patch('kiwi.command.Command.run')
    @patch_open
    @patch('os.path.exists')
    @raises(KiwiImportDescriptionError)
    def test_import_description_configured_editboot_scripts_not_found(
        self, mock_path, mock_open, mock_command
    ):
        path_return_values = [False, True, True]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect
        self.setup_with_real_xml.import_description()

    @patch('kiwi.command.Command.run')
    @patch_open
    @patch('os.path.exists')
    @raises(KiwiImportDescriptionError)
    def test_import_description_configured_archives_not_found(
        self, mock_path, mock_open, mock_command
    ):
        path_return_values = [False, False, True, True, True, True]

        def side_effect(arg):
            return path_return_values.pop()

        mock_path.side_effect = side_effect
        self.setup_with_real_xml.import_description()

    @patch('kiwi.command.Command.run')
    def test_cleanup(self, mock_command):
        self.setup.cleanup()
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', '/.kconfig', '/image']
        )

    @patch_open
    def test_import_shell_environment(self, mock_open):
        mock_profile = mock.MagicMock()
        mock_profile.create = mock.Mock(
            return_value=['a']
        )
        mock_open.return_value = self.context_manager_mock
        self.setup.import_shell_environment(mock_profile)
        mock_profile.create.assert_called_once_with()
        mock_open.assert_called_once_with('root_dir/.profile', 'w')
        self.file_mock.write.assert_called_once_with('a\n')

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

    @patch('kiwi.system.setup.ArchiveTar')
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

    @patch('kiwi.system.setup.Command.run')
    def test_setup_hardware_clock(self, mock_command):
        self.setup.preferences['hwclock'] = 'clock'
        self.setup.setup_hardware_clock()
        mock_command.assert_called_once_with(
            [
                'chroot', 'root_dir', 'hwclock', '--adjust', '--clock'
            ]
        )

    @patch('kiwi.system.setup.Shell.run_common_function')
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

    @patch('kiwi.system.setup.Shell.run_common_function')
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

    @patch('kiwi.system.setup.Command.run')
    def test_setup_timezone(self, mock_command):
        self.setup.preferences['timezone'] = 'timezone'
        self.setup.setup_timezone()
        mock_command.assert_called_once_with([
            'chroot', 'root_dir', 'ln', '-s', '-f',
            '/usr/share/zoneinfo/timezone', '/etc/localtime'
        ])

    @patch('kiwi.system.setup.Users')
    def test_setup_groups(self, mock_users):
        users = mock.Mock()
        users.group_exists = mock.Mock(
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
        users = mock.Mock()
        users.user_exists = mock.Mock(
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
                    '-g', 'kiwi', '-G', 'admin,users',
                    '-m', '-d', '/home/kiwi'
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
        users = mock.Mock()
        users.user_exists = mock.Mock(
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

    @patch_open
    @patch('os.path.exists')
    def test_import_image_identifier(self, mock_os_path, mock_open):
        self.xml_state.xml_data.get_id = mock.Mock(
            return_value='42'
        )
        mock_os_path.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.setup.import_image_identifier()
        mock_open.assert_called_once_with('root_dir/etc/ImageID', 'w')
        self.file_mock.write.assert_called_once_with('42\n')

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

    @patch_open
    def test_create_fstab(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.setup.create_fstab(['fstab_entry'])
        mock_open.assert_called_once_with(
            'root_dir/etc/fstab', 'w'
        )
        self.file_mock.write.assert_called_once_with('fstab_entry\n')

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.setup.NamedTemporaryFile')
    @patch('kiwi.system.setup.ArchiveTar')
    @patch_open
    @patch('kiwi.system.setup.Compress')
    @patch('os.path.getsize')
    @patch('kiwi.system.setup.Path.wipe')
    def test_create_recovery_archive(
        self, mock_wipe, mock_getsize, mock_compress,
        mock_open, mock_archive, mock_temp, mock_command
    ):
        mock_open.return_value = self.context_manager_mock
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
        assert self.file_mock.write.call_args_list[0] == call('ext3')
        assert mock_command.call_args_list[2] == call(
            ['bash', '-c', 'tar -tf root_dir/recovery.tar | wc -l']
        )
        assert mock_open.call_args_list[1] == call(
            'root_dir/recovery.tar.files', 'w'
        )
        assert mock_getsize.call_args_list[0] == call(
            'root_dir/recovery.tar'
        )
        assert self.file_mock.write.call_args_list[1] == call('1\n')
        assert mock_open.call_args_list[2] == call(
            'root_dir/recovery.tar.size', 'w'
        )
        assert self.file_mock.write.call_args_list[2] == call('42')
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
        assert self.file_mock.write.call_args_list[3] == call('300')
        mock_wipe.assert_called_once_with(
            'root_dir/recovery.tar.gz'
        )

    @patch('kiwi.system.setup.Command.run')
    @patch('kiwi.system.setup.Path.create')
    @patch('os.path.exists')
    def test_export_modprobe_setup(self, mock_exists, mock_path, mock_command):
        mock_exists.return_value = True
        self.setup.export_modprobe_setup('target_root_dir')
        mock_path.assert_called_once_with('target_root_dir/etc')
        mock_command.assert_called_once_with(
            [
                'rsync', '-z', '-a',
                'root_dir/etc/modprobe.d', 'target_root_dir/etc/'
            ]
        )

    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_export_rpm_package_list(
        self, mock_open, mock_exists, mock_command
    ):
        command = mock.Mock()
        command.output = 'packages_data'
        mock_exists.return_value = True
        mock_command.return_value = command
        result = self.setup.export_rpm_package_list('target_dir')
        assert result == 'target_dir/some-image.x86_64-1.2.3.packages'
        mock_command.assert_called_once_with([
            'rpm', '--root', 'root_dir', '-qa', '--qf',
            '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{DISTURL}|\\n'
        ])
        mock_open.assert_called_once_with(
            'target_dir/some-image.x86_64-1.2.3.packages', 'w'
        )

    @patch('kiwi.system.setup.Command.run')
    @patch('os.path.exists')
    @patch_open
    def test_export_rpm_package_verification(
        self, mock_open, mock_exists, mock_command
    ):
        command = mock.Mock()
        command.output = 'verification_data'
        mock_exists.return_value = True
        mock_command.return_value = command
        result = self.setup.export_rpm_package_verification('target_dir')
        assert result == 'target_dir/some-image.x86_64-1.2.3.verified'
        mock_command.assert_called_once_with(
            command=['rpm', '--root', 'root_dir', '-Va'],
            raise_on_error=False
        )
        mock_open.assert_called_once_with(
            'target_dir/some-image.x86_64-1.2.3.verified', 'w'
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

    @patch('kiwi.system.setup.Repository')
    def test_import_repositories_marked_as_imageinclude(self, mock_repo):
        repo = mock.Mock()
        mock_repo.return_value = repo
        self.setup_with_real_xml.import_repositories_marked_as_imageinclude()
        repo.delete_all_repos.assert_called_once_with()
        repo.add_repo.assert_called_once_with(
            '95811799a6d1889c5b2363d3886986de',
            'http://download.opensuse.org/repositories/Devel:PubCloud:AmazonEC2/SLE_12_GA',
            'rpm-md',
            None,
            None,
            None
        )
