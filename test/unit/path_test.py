from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.path import Path


class TestPath(object):
    def test_sort_by_hierarchy(self):
        ordered = Path.sort_by_hierarchy(
            ['usr', 'usr/bin', 'etc', 'usr/lib']
        )
        assert ordered == ['usr', 'etc', 'usr/bin', 'usr/lib']

    @patch('kiwi.command.Command.run')
    def test_create(self, mock_command):
        Path.create('foo')
        mock_command.assert_called_once_with(
            ['mkdir', '-p', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_wipe(self, mock_command):
        Path.wipe('foo')
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_remove(self, mock_command):
        Path.remove('foo')
        mock_command.assert_called_once_with(
            ['rmdir', 'foo']
        )

    @patch('kiwi.command.Command.run')
    def test_remove_hierarchy(self, mock_command):
        Path.remove_hierarchy('foo')
        mock_command.assert_called_once_with(
            ['rmdir', '-p', '--ignore-fail-on-non-empty', 'foo']
        )
