import sys
import mock
from nose.tools import *
from mock import patch

import kiwi

import nose_helper

from kiwi.system_build_task import SystemBuildTask
from kiwi.exceptions import *


class TestSystemBuildTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'build',
            '--description', '../data/description',
            '--target-dir', 'some-target'
        ]
        kiwi.system_build_task.Privileges = mock.Mock()
        kiwi.system_build_task.Path = mock.Mock()

        kiwi.system_build_task.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.manager = mock.Mock()
        self.system = mock.Mock()
        self.system.setup_repositories = mock.Mock(
            return_value=self.manager
        )
        kiwi.system_build_task.System = mock.Mock(
            return_value=self.system
        )

        self.setup = mock.Mock()
        kiwi.system_build_task.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.profile = mock.Mock()
        kiwi.system_build_task.Profile = mock.Mock(
            return_value=self.profile
        )

        self.result = mock.Mock()
        self.builder = mock.MagicMock()
        self.builder.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.ImageBuilder = mock.Mock(
            return_value=self.builder
        )

        self.task = SystemBuildTask()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['build'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--target-dir'] = 'some-target'
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--add-repo'] = []

    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build(self, mock_log):
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.system.setup_repositories.assert_called_once_with()
        self.system.install_bootstrap.assert_called_once_with(self.manager)
        self.system.install_system.assert_called_once_with(
            self.manager
        )
        self.setup.import_shell_environment.assert_called_once_with(
            self.profile
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.import_overlay_files.assert_called_once_with()
        self.setup.call_config_script.assert_called_once_with()
        self.setup.import_image_identifier.assert_called_once_with()
        self.setup.setup_groups.assert_called_once_with()
        self.setup.setup_users.assert_called_once_with()
        self.setup.setup_keyboard_map.assert_called_once_with()
        self.setup.setup_locale.assert_called_once_with()
        self.setup.setup_timezone.assert_called_once_with()
        self.system.pinch_system.assert_called_once_with(self.manager)
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            'some-target/kiwi.result'
        )

    @patch('kiwi.xml_state.XMLState.set_repository')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_set_repo(
        self, mock_log, mock_set_repo
    ):
        self.__init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_add_repo(
        self, mock_log, mock_add_repo
    ):
        self.__init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_add_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    def test_process_system_build_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['build'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::build'
        )
