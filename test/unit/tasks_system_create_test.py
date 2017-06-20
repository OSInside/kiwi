import sys
import mock
import os

import kiwi

from .test_helper import argv_kiwi_tests

from kiwi.tasks.system_create import SystemCreateTask


class TestSystemCreateTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'create',
            '--root', '../data/root-dir', '--target-dir', 'some-target'
        ]

        self.abs_root_dir = os.path.abspath('../data/root-dir')
        self.abs_target_dir = os.path.abspath('some-target')

        kiwi.tasks.system_create.Path = mock.Mock()
        kiwi.tasks.system_create.Privileges = mock.Mock()
        kiwi.tasks.system_create.Path = mock.Mock()

        kiwi.tasks.system_create.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.runtime_checker = mock.Mock()
        kiwi.tasks.base.RuntimeChecker = mock.Mock(
            return_value=self.runtime_checker
        )

        self.runtime_config = mock.Mock()
        kiwi.tasks.base.RuntimeConfig = mock.Mock(
            return_value=self.runtime_config
        )

        self.setup = mock.Mock()
        kiwi.tasks.system_create.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.result = mock.Mock()
        self.builder = mock.MagicMock()
        self.builder.create = mock.Mock(
            return_value=self.result
        )
        kiwi.tasks.system_create.ImageBuilder = mock.Mock(
            return_value=self.builder
        )

        self.task = SystemCreateTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

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
        self.runtime_checker.check_target_directory_not_in_shared_cache.called_once_with(
            self.abs_target_dir
        )
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
