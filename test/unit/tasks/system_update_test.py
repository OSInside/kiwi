import sys
import mock

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.system_update import SystemUpdateTask


class TestSystemUpdateTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'update',
            '--root', '../data/root-dir'
        ]
        self.manager = mock.Mock()
        self.system_prepare = mock.Mock()
        kiwi.tasks.system_update.Privileges = mock.Mock()
        self.system_prepare.setup_repositories = mock.Mock(
            return_value=self.manager
        )
        kiwi.tasks.system_update.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )
        kiwi.tasks.system_update.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = SystemUpdateTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['update'] = False
        self.task.command_args['--add-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--root'] = '../data/root-dir'

    def test_process_system_update(self):
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.process()
        self.task.system.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        self.task.system.update_system.assert_called_once_with(self.manager)

    def test_process_system_update_add_package(self):
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        self.task.system.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        self.task.system.install_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    def test_process_system_update_delete_package(self):
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        self.task.system.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        self.task.system.delete_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    def test_process_system_update_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['update'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::update'
        )
