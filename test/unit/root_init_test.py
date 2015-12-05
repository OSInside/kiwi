from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import (
    KiwiRootDirExists,
    KiwiRootInitCreationError
)

from kiwi.root_init import RootInit


class TestRootInit(object):
    @raises(KiwiRootDirExists)
    @patch('os.path.exists')
    def test_init_raises_error(self, mock_path):
        mock_path.return_value = True
        RootInit('root_dir')

    @raises(KiwiRootInitCreationError)
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_create_raises_error(self, mock_path, mock_command):
        mock_path.return_value = False
        mock_command.side_effect = KiwiRootInitCreationError('some-error')
        root = RootInit('root_dir')
        root.create()

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_create(self, mock_path, mock_command):
        mock_path.return_value = False
        root = RootInit('root_dir')
        mock_path.return_value = True
        root.create()
        assert mock_command.called

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_delete(self, mock_path, mock_command):
        mock_path.return_value = False
        root = RootInit('root_dir')
        root.delete()
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'root_dir']
        )
