from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.storage.device_provider import DeviceProvider

from kiwi.exceptions import KiwiDeviceProviderError


class TestDeviceProvider:
    def setup(self):
        self.provider = DeviceProvider()

    def test_get_device(self):
        with raises(KiwiDeviceProviderError):
            self.provider.get_device()

    @patch('kiwi.storage.device_provider.Command.run')
    def test_get_uuid(self, mock_command):
        uuid_call = Mock()
        uuid_call.output = '0815\n'
        mock_command.return_value = uuid_call
        assert self.provider.get_uuid('/dev/some-device') == '0815'
        mock_command.assert_called_once_with(
            ['blkid', '/dev/some-device', '-s', 'UUID', '-o', 'value']
        )

    @patch('kiwi.storage.device_provider.Command.run')
    def test_get_byte_size(self, mock_command):
        blockdev_call = Mock()
        blockdev_call.output = '1024\n'
        mock_command.return_value = blockdev_call
        assert self.provider.get_byte_size('/dev/some-device') == 1024
        mock_command.assert_called_once_with(
            ['blockdev', '--getsize64', '/dev/some-device']
        )

    def test_is_loop(self):
        assert self.provider.is_loop() is False
