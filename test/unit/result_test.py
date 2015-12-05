from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.result import Result


class TestResult(object):
    def setup(self):
        self.result = Result()

    def test_add(self):
        self.result.add('foo', 'bar')
        assert self.result.get_results() == {'foo': 'bar'}

    @patch('kiwi.logger.log.info')
    def test_print_results_no_data(self, mock_info):
        self.result.print_results()
        assert mock_info.called == 0

    @patch('kiwi.logger.log.info')
    def test_print_results_data(self, mock_info):
        self.result.add('foo', 'bar')
        self.result.print_results()
        assert mock_info.called
