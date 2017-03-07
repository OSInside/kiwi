
from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiMappedDeviceError
from kiwi.storage.mapped_device import MappedDevice


class TestMappedDevice(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
        mock_path.return_value = True
        self.device_provider = mock.Mock()
        self.device_provider.is_loop = mock.Mock()
        self.device = MappedDevice(
            '/dev/foo', self.device_provider
        )

    @patch('os.path.exists')
    @raises(KiwiMappedDeviceError)
    def test_device_not_existingr(self, mock_path):
        mock_path.return_value = False
        MappedDevice('/dev/foo', mock.Mock())

    def test_get_device(self):
        assert self.device.get_device() == '/dev/foo'

    def test_is_loop(self):
        assert self.device.is_loop() == self.device_provider.is_loop()
