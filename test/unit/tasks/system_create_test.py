import sys
from unittest.mock import (
    Mock, MagicMock
)
import os

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.system_create import SystemCreateTask


class TestSystemCreateTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'create',
            '--root', '../data/root-dir', '--target-dir', 'some-target'
        ]

        self.abs_root_dir = os.path.abspath('../data/root-dir')
        self.abs_target_dir = os.path.abspath('some-target')

        kiwi.tasks.system_create.Path = Mock()
        kiwi.tasks.system_create.Privileges = Mock()

        kiwi.tasks.system_create.Help = Mock(
            return_value=Mock()
        )

        self.runtime_checker = Mock()
        kiwi.tasks.base.RuntimeChecker = Mock(
            return_value=self.runtime_checker
        )

        self.runtime_config = Mock()
        self.runtime_config.get_disabled_runtime_checks.return_value = []
        kiwi.tasks.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )

        self.setup = Mock()
        kiwi.tasks.system_create.SystemSetup = Mock(
            return_value=self.setup
        )

        self.result = Mock()
        self.builder = MagicMock()
        self.builder.create = Mock(
            return_value=self.result
        )
        kiwi.tasks.system_create.ImageBuilder.new = Mock(
            return_value=self.builder
        )

        self.task = SystemCreateTask()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['create'] = False
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--target-dir'] = 'some-target'
        self.task.command_args['--signing-key'] = ['some-key-file']

    def test_process_system_create(self):
        self._init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.runtime_checker.\
            check_target_directory_not_in_shared_cache.\
            assert_called_once_with(self.abs_root_dir)
        self.runtime_checker.\
            check_dracut_module_versions_compatible_to_kiwi.\
            assert_called_once_with(self.abs_root_dir)
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            os.sep.join([self.abs_target_dir, 'kiwi.result'])
        )

    def test_process_system_create_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::create'
        )
