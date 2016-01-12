import sys
import mock
from nose.tools import *
from mock import patch

import kiwi

import nose_helper

from kiwi.system_create_task import SystemCreateTask
from kiwi.exceptions import *


class TestSystemCreateTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'create',
            '--root', '../data/root-dir', '--target-dir', 'some-target'
        ]
        self.result = mock.Mock()
        kiwi.system_create_task.Privileges = mock.Mock()
        kiwi.system_create_task.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.disk = mock.MagicMock()
        self.disk.create = mock.Mock(
            return_value=self.result
        )
        self.archive = mock.MagicMock()
        self.archive.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_create_task.ArchiveBuilder = mock.Mock(
            return_value=self.archive
        )
        kiwi.system_create_task.DiskBuilder = mock.Mock(
            return_value=self.disk
        )
        self.filesystem = mock.MagicMock()
        self.filesystem.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_create_task.FileSystemBuilder = mock.Mock(
            return_value=self.filesystem
        )
        self.pxe = mock.MagicMock()
        self.pxe.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_create_task.PxeBuilder = mock.Mock(
            return_value=self.pxe
        )
        self.liveiso = mock.MagicMock()
        self.liveiso.create = mock.Mock(
            return_value=self.result
        )
        kiwi.system_create_task.LiveImageBuilder = mock.Mock(
            return_value=self.liveiso
        )
        self.task = SystemCreateTask()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['create'] = False
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--target-dir'] = 'some-target'

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_filesystem(self, mock_type):
        mock_type.return_value = 'ext4'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.filesystem.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_live_system(self, mock_type):
        mock_type.return_value = 'iso'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.liveiso.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_disk_with_install_media(self, mock_type):
        self.disk.install_media = True
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.disk.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_disk_with_disk_format(self, mock_type):
        self.disk.install_media = False
        self.disk.image_format = 'qcow2'
        mock_type.return_value = 'oem'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.disk.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_archive(self, mock_type):
        mock_type.return_value = 'tbz'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.archive.create.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_pxe(self, mock_type):
        mock_type.return_value = 'pxe'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.pxe.create.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    @raises(KiwiNotImplementedError)
    def test_process_system_create_container(self, mock_type):
        mock_type.return_value = 'docker'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()

    @raises(KiwiRequestedTypeError)
    @patch('kiwi.xml_state.XMLState.get_build_type_name')
    def test_process_system_create_raise(self, mock_type):
        mock_type.return_value = 'foo'
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()

    def test_process_system_create_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['create'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::create'
        )
