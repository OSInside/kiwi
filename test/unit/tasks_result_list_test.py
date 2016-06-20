import sys
import mock

from mock import patch

import kiwi

from .test_helper import *
from kiwi.exceptions import *
from kiwi.tasks.result_list import ResultListTask


class TestResultListTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], 'result', 'list', '--target-dir', 'directory'
        ]
        self.result = mock.Mock()
        kiwi.tasks.result_list.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = ResultListTask()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['list'] = False
        self.task.command_args['--target-dir'] = 'directory'

    @patch('kiwi.tasks.result_list.Result.load')
    def test_process_result_list(self, mock_load):
        mock_load.return_value = self.result
        self._init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        mock_load.assert_called_once_with('directory/kiwi.result')
        self.result.print_results.assert_called_once_with()

    def test_process_result_list_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['list'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::result::list'
        )
