import sys
import mock
from nose.tools import *
from mock import patch

import kiwi

from . import nose_helper

from kiwi.system_create_task import SystemCreateTask
from kiwi.exceptions import *


class TestSystemCreateTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'create',
            '--root', '../data/root-dir', '--target-dir', 'some-target'
        ]
        kiwi.system_create_task.Privileges = mock.Mock()
        kiwi.system_create_task.Path = mock.Mock()

        kiwi.system_create_task.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.setup = mock.Mock()
        kiwi.system_create_task.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.result = mock.Mock()
        self.builder = mock.MagicMock()
        self.builder.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_create_task.ImageBuilder = mock.Mock(
            return_value=self.builder
        )

        self.task = SystemCreateTask()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['create'] = False
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--target-dir'] = 'some-target'

    def test_process_system_create(self):
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            'some-target/kiwi.result'
        )

    def test_process_system_create_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::create'
        )
