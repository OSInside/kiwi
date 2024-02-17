from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.storage.mapped_device import MappedDevice

from kiwi.exceptions import KiwiMappedDeviceError


class TestMappedDevice:
    @patch('os.path.exists')
    def setup(self, mock_path):
        mock_path.return_value = True
        self.device_provider = Mock()
        self.device_provider.is_loop = Mock()
        self.device = MappedDevice(
            '/dev/foo', self.device_provider
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_path):
        self.setup()

    @patch('os.path.exists')
    def test_device_not_existingr(self, mock_path):
        mock_path.return_value = False
        with raises(KiwiMappedDeviceError):
            MappedDevice('/dev/foo', Mock())

    def test_get_device(self):
        assert self.device.get_device() == '/dev/foo'

    def test_is_loop(self):
        assert self.device.is_loop() == self.device_provider.is_loop()
