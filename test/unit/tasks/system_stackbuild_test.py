import sys
from pytest import raises
from unittest.mock import (
    Mock, patch, call
)

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.system_stackbuild import SystemStackbuildTask
from kiwi.exceptions import (
    KiwiStackBuildTargetDirExists,
    KiwiStackBuildRootSyncFailed
)


class TestSystemStackbuildTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'a', '--profile', 'b',
            '--type', 'iso', 'system', 'stackbuild',
            '--stash', 'name', '--target-dir', 'some-target-dir', 'kiwi',
            '--signing-key', 'some-key'
        ]
        self.task = SystemStackbuildTask()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['stackbuild'] = False
        self.task.command_args['--stash'] = []
        self.task.command_args['--from-registry'] = None
        self.task.command_args['--target-dir'] = None
        self.task.command_args['--description'] = None
        self.task.command_args['system_build_or_create'] = [
            '--signing-key', 'some-key'
        ]

    @patch('kiwi.tasks.system_stackbuild.Help')
    def test_process_help(self, mock_Help):
        Help = Mock()
        mock_Help.return_value = Help
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['stackbuild'] = True
        self.task.process()
        Help.show.assert_called_once_with(
            'kiwi::system::stackbuild'
        )

    @patch('kiwi.tasks.system_stackbuild.Privileges')
    @patch('os.path.exists')
    def test_process_target_dir_exists(
        self, mock_os_path_exists, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        mock_os_path_exists.return_value = True
        with raises(KiwiStackBuildTargetDirExists):
            self.task.process()

    @patch('kiwi.tasks.system_stackbuild.DataSync')
    @patch('kiwi.tasks.system_stackbuild.Privileges')
    @patch('kiwi.tasks.system_stackbuild.Path.create')
    @patch('kiwi.tasks.system_stackbuild.Command.run')
    @patch('kiwi.tasks.system_stackbuild.SystemCreateTask')
    @patch('os.path.exists')
    def test_process_root_sync_failed(
        self, mock_os_path_exists, mock_SystemCreateTask, mock_Command_run,
        mock_Path_create, mock_Privileges, mock_DataSync
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        mock_os_path_exists.return_value = False

        mock_DataSync.side_effect = Exception

        kiwi_task = Mock()
        mock_SystemCreateTask.return_value = kiwi_task
        with raises(KiwiStackBuildRootSyncFailed):
            self.task.process()

    @patch('kiwi.tasks.system_stackbuild.Privileges')
    @patch('kiwi.tasks.system_stackbuild.Path.create')
    @patch('kiwi.tasks.system_stackbuild.Command.run')
    @patch('kiwi.tasks.system_stackbuild.SystemCreateTask')
    @patch('os.path.exists')
    @patch('kiwi.tasks.system_stackbuild.patch.object')
    def test_process_rebuild_typer_commandline(
        self, mock_patch_object, mock_os_path_exists,
        mock_SystemCreateTask, mock_Command_run,
        mock_Path_create, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        self.task.command_args['--from-registry'] = 'registry.uri'
        mock_os_path_exists.return_value = False
        mock_Command_run.return_value.output = '/podman/mount/path'
        kiwi_task = Mock()
        mock_SystemCreateTask.return_value = kiwi_task
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'pull', 'registry.uri/name']),
            call(['podman', 'image', 'mount', 'name']),
            call(
                [
                    'rsync', '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system', '--inplace',
                    '/podman/mount/path/',
                    '/some/target-dir/build/image-root'
                ]
            ),
            call(
                ['podman', 'image', 'umount', '--force', 'name'],
                raise_on_error=False
            )
        ]
        mock_SystemCreateTask.assert_called_once_with(
            should_perform_task_setup=False
        )
        kiwi_task.process.assert_called_once_with()
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--type', 'iso',
                '--profile', 'a', '--profile', 'b',
                'system', 'create',
                '--root', '/some/target-dir/build/image-root',
                '--target-dir', '/some/target-dir',
                '--signing-key', 'some-key'
            ]
        )

    @patch('kiwi.tasks.system_stackbuild.Privileges')
    @patch('kiwi.tasks.system_stackbuild.Path.create')
    @patch('kiwi.tasks.system_stackbuild.Command.run')
    @patch('kiwi.tasks.system_stackbuild.SystemBuildTask')
    @patch('os.path.exists')
    @patch('kiwi.tasks.system_stackbuild.patch.object')
    def test_process_new_build_typer_commandline(
        self, mock_patch_object, mock_os_path_exists,
        mock_SystemBuildTask, mock_Command_run,
        mock_Path_create, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        self.task.command_args['--description'] = '/path/to/kiwi/description'
        self.task.command_args['--from-registry'] = 'registry.uri'
        mock_os_path_exists.return_value = False
        mock_Command_run.return_value.output = '/podman/mount/path'
        kiwi_task = Mock()
        mock_SystemBuildTask.return_value = kiwi_task
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'pull', 'registry.uri/name']),
            call(['podman', 'image', 'mount', 'name']),
            call(
                [
                    'rsync', '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system', '--inplace',
                    '/podman/mount/path/',
                    '/some/target-dir/build/image-root'
                ]
            ),
            call(
                ['podman', 'image', 'umount', '--force', 'name'],
                raise_on_error=False
            )
        ]
        mock_SystemBuildTask.assert_called_once_with(
            should_perform_task_setup=False
        )
        kiwi_task.process.assert_called_once_with()
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--type', 'iso',
                '--profile', 'a', '--profile', 'b',
                'system', 'build',
                '--description', '/path/to/kiwi/description',
                '--target-dir', '/some/target-dir',
                '--allow-existing-root',
                '--signing-key', 'some-key'
            ]
        )

    @patch('kiwi.tasks.system_stackbuild.Privileges')
    @patch('kiwi.tasks.system_stackbuild.Path.create')
    @patch('kiwi.tasks.system_stackbuild.Command.run')
    @patch('kiwi.tasks.system_stackbuild.DataSync')
    @patch('kiwi.tasks.system_stackbuild.SystemBuildTask')
    @patch('os.path.exists')
    @patch('kiwi.tasks.system_stackbuild.patch.object')
    def test_process_new_build_no_kiwi_subcommand(
        self, mock_patch_object, mock_os_path_exists,
        mock_SystemBuildTask, mock_DataSync, mock_Command_run,
        mock_Path_create, mock_Privileges
    ):
        self._init_command_args()
        self.task.global_args = {
            '--kiwi-file': 'appliance.kiwi'
        }
        self.task.command_args['system_build_or_create'] = None
        self.task.command_args['--stash'] = ['base', 'layer']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        self.task.command_args['--description'] = '/path/to/kiwi/description'
        mock_os_path_exists.return_value = False
        mock_Command_run.return_value.output = '/podman/mount/path'
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'image', 'mount', 'base']),
            call(
                ['podman', 'image', 'umount', '--force', 'base'],
                raise_on_error=False
            ),
            call(['podman', 'image', 'mount', 'layer']),
            call(
                ['podman', 'image', 'umount', '--force', 'layer'],
                raise_on_error=False
            )
        ]
        assert mock_DataSync.return_value.sync_data.call_count == 2
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--kiwi-file', 'appliance.kiwi',
                'system', 'build',
                '--description', '/path/to/kiwi/description',
                '--target-dir', '/some/target-dir',
                '--allow-existing-root'
            ]
        )
        mock_SystemBuildTask.return_value.process.assert_called_once_with()
