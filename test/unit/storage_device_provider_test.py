from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiDeviceProviderError

from kiwi.storage.device_provider import DeviceProvider


class TestDeviceProvider(object):
    def setup(self):
        self.provider = DeviceProvider()

    @raises(KiwiDeviceProviderError)
    def test_get_device(self):
        self.provider.get_device()

    @patch('kiwi.storage.device_provider.Command.run')
    def test_get_uuid(self, mock_command):
        uuid_call = mock.Mock()
        uuid_call.output = '0815\n'
        mock_command.return_value = uuid_call
        assert self.provider.get_uuid('/dev/some-device') == '0815'
        mock_command.assert_called_once_with(
            ['blkid', '/dev/some-device', '-s', 'UUID', '-o', 'value']
        )

    @patch('kiwi.storage.device_provider.Command.run')
    def test_get_byte_size(self, mock_command):
        blockdev_call = mock.Mock()
        blockdev_call.output = '1024\n'
        mock_command.return_value = blockdev_call
        assert self.provider.get_byte_size('/dev/some-device') == 1024
        mock_command.assert_called_once_with(
            ['blockdev', '--getsize64', '/dev/some-device']
        )

    def test_is_loop(self):
        assert self.provider.is_loop() is False
