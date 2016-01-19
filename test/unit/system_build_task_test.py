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
        self.result = mock.Mock()

        kiwi.system_build_task.Path = mock.Mock()

        kiwi.system_build_task.Privileges = mock.Mock()

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

        self.container = mock.MagicMock()
        self.container.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.ContainerBuilder = mock.Mock(
            return_value=self.container
        )

        self.archive = mock.MagicMock()
        self.archive.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.ArchiveBuilder = mock.Mock(
            return_value=self.archive
        )

        self.disk = mock.MagicMock()
        self.disk.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.DiskBuilder = mock.Mock(
            return_value=self.disk
        )

        self.filesystem = mock.MagicMock()
        self.filesystem.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.FileSystemBuilder = mock.Mock(
            return_value=self.filesystem
        )

        self.pxe = mock.MagicMock()
        self.pxe.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.PxeBuilder = mock.Mock(
            return_value=self.pxe
        )

        self.liveiso = mock.MagicMock()
        self.liveiso.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_build_task.LiveImageBuilder = mock.Mock(
            return_value=self.liveiso
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

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage(self, mock_log, mock_type):
        mock_type.return_value = 'oem'
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
        self.setup.setup_hardware_clock.assert_called_once_with()
        self.setup.setup_keyboard_map.assert_called_once_with()
        self.setup.setup_locale.assert_called_once_with()
        self.setup.setup_timezone.assert_called_once_with()

        self.system.pinch_system.assert_called_once_with(self.manager)

    @patch('kiwi.xml_state.XMLState.set_repository')
    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_set_repo(
        self, mock_log, mock_type, mock_set_repo
    ):
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_add_repo(
        self, mock_log, mock_type, mock_add_repo
    ):
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_add_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_filesystem(self, mock_log, mock_type):
        mock_type.return_value = 'ext4'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.filesystem.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_live_system(self, mock_log, mock_type):
        mock_type.return_value = 'iso'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.liveiso.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_disk_with_install_media(
        self, mock_log, mock_type
    ):
        self.disk.install_media = True
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.disk.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_disk_with_disk_format(
        self, mock_log, mock_type
    ):
        self.disk.install_media = False
        self.disk.image_format = 'qcow2'
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.disk.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_archive(self, mock_log, mock_type):
        mock_type.return_value = 'tbz'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.archive.create.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_pxe(self, mock_log, mock_type):
        mock_type.return_value = 'pxe'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.pxe.create.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_container(self, mock_log, mock_type):
        mock_type.return_value = 'docker'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.container.create.assert_called_once_with()

    @raises(KiwiRequestedTypeError)
    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_raise(self, mock_log, mock_type):
        mock_type.return_value = 'foo'
        self.__init_command_args()
        self.task.command_args['build'] = True
        self.task.process()

    def test_process_system_build_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['build'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::build'
        )
