from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.shell import Shell


class TestShell(object):
    def test_quote(self):
        assert Shell.quote('aa\!') == 'aa\\\\\\!'

    def test_quote_key_value_file(self):
        assert Shell.quote_key_value_file('../data/key_value') == [
            "foo='bar'",
            "bar='xxx'",
            "name='bob'",
            "strange='$a_foo'"
        ]

    @patch('kiwi.shell.Command.run')
    def test_run_common_function(self, mock_command):
        Shell.run_common_function('foo', ['"param1"', '"param2"'])
        mock_command.assert_called_once_with(
            ['bash', '-c', 'source config/functions.sh; foo "param1" "param2"']
        )
