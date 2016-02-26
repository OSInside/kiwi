from nose.tools import *
from mock import patch
from mock import call
import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.boot.image.base import BootImageBase


class TestBootImageBase(object):
    @patch('kiwi.boot.image.base.mkdtemp')
    @patch('kiwi.boot.image.base.os.path.exists')
    def setup(self, mock_exists, mock_mkdtemp):
        self.xml_state = mock.Mock()
        mock_mkdtemp.return_value = 'boot-root-directory'
        mock_exists.return_value = True
        self.task = BootImageBase(
            self.xml_state, 'some-target-dir'
        )
        mock_mkdtemp.assert_called_once_with(
            prefix='boot-image.', dir='some-target-dir'
        )

    @raises(KiwiTargetDirectoryNotFound)
    def test_boot_image_task_raises(self):
        BootImageBase(
            mock.Mock(), 'target-dir-does-not-exist', 'some-root-dir'
        )

    @raises(NotImplementedError)
    def test_prepare(self):
        self.task.prepare()

    @raises(NotImplementedError)
    def test_create_initrd(self):
        self.task.create_initrd()

    @patch('os.listdir')
    def test_is_prepared(self, mock_listdir):
        mock_listdir.return_value = True
        assert self.task.is_prepared() == mock_listdir.return_value

    @patch('kiwi.boot.image.base.Command.run')
    @patch('os.path.exists')
    def test_destructor(self, mock_path, mock_command):
        mock_path.return_value = True
        self.task.__del__()
        print(mock_command.call_args_list)
        assert mock_command.call_args_list == [
            call(['rm', '-r', '-f', 'boot-root-directory']),
        ]
