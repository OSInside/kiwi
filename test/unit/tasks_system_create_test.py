import sys
import mock

from mock import patch

import kiwi

from .test_helper import *

from kiwi.tasks.system_create import SystemCreateTask
from kiwi.exceptions import *


class TestSystemCreateTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'create',
            '--root', '../data/root-dir', '--target-dir', 'some-target'
        ]
        kiwi.tasks.system_create.Privileges = mock.Mock()
        kiwi.tasks.system_create.Path = mock.Mock()

        kiwi.tasks.system_create.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.runtime_checker = mock.Mock()
        kiwi.tasks.base.RuntimeChecker = mock.Mock(
            return_value=self.runtime_checker
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

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['create'] = False
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--target-dir'] = 'some-target'

    def test_process_system_create(self):
        self._init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.runtime_checker.check_target_directory_not_in_shared_cache.called_once_with('some-target')
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            'some-target/kiwi.result'
        )

    def test_process_system_create_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::create'
        )
