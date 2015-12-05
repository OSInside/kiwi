from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.device_provider import DeviceProvider


class TestDeviceProvider(object):
    def setup(self):
        self.provider = DeviceProvider()

    @raises(KiwiDeviceProviderError)
    def test_get_device(self):
        self.provider.get_device()

    @patch('kiwi.device_provider.Command.run')
    def test_get_uuid(self, mock_command):
        uuid_call = mock.Mock()
        uuid_call.output = '0815\n'
        mock_command.return_value = uuid_call
        assert self.provider.get_uuid('/dev/some-device') == '0815'
        mock_command.assert_called_once_with(
            ['blkid', '/dev/some-device', '-s', 'UUID', '-o', 'value']
        )

    def test_is_loop(self):
        assert self.provider.is_loop() == False
