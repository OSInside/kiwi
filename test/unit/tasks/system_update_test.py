import sys
import os
from unittest.mock import (
    patch, Mock, MagicMock
)

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.tasks.system_update import SystemUpdateTask


class TestSystemUpdateTask:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'update',
            '--root', '../data/root-dir'
        ]
        self.abs_target_dir = os.path.abspath('some-target')

        kiwi.tasks.system_update.Privileges = Mock()
        kiwi.tasks.system_update.Path = Mock()

        kiwi.tasks.system_update.Help = Mock(
            return_value=Mock()
        )
        self.task = SystemUpdateTask()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['update'] = False
        self.task.command_args['--add-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--root'] = '../data/root-dir'

    @patch('kiwi.tasks.system_update.SystemPrepare')
    def test_process_system_update(self, mock_SystemPrepare):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.process()
        system_prepare.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        system_prepare.update_system.assert_called_once_with(
            manager.__enter__.return_value
        )

    @patch('kiwi.tasks.system_update.SystemPrepare')
    def test_process_system_update_add_package(self, mock_SystemPrepare):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        system_prepare.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        system_prepare.install_packages.assert_called_once_with(
            manager.__enter__.return_value, ['vim']
        )

    @patch('kiwi.tasks.system_update.SystemPrepare')
    def test_process_system_update_delete_package(self, mock_SystemPrepare):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        self._init_command_args()
        self.task.command_args['update'] = True
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        system_prepare.setup_repositories.assert_called_once_with(
            target_arch=None
        )
        system_prepare.delete_packages.assert_called_once_with(
            manager.__enter__.return_value, ['vim']
        )

    def test_process_system_update_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['update'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::update'
        )
