from unittest.mock import Mock
from kiwi.logger_socket import PlainTextSocketHandler


class TestPlainTextSocketHandler:
    def setup(self):
        self.logger_socket = PlainTextSocketHandler('socket', None)
        self.logger_socket.formatter = Mock()

    def setup_method(self, cls):
        self.setup()

    def test_makePickle(self):
        self.logger_socket.makePickle('record')
        self.logger_socket.formatter.format.assert_called_once_with('record')
