from unittest.mock import (
    patch, mock_open
)

from kiwi.system.identifier import SystemIdentifier


class TestSystemIdentifier:
    def setup(self):
        self.identifier = SystemIdentifier()

    def setup_method(self, cls):
        self.setup()

    def test_get_id(self):
        assert self.identifier.get_id() is None

    @patch('random.randrange')
    def test_calculate_id(self, mock_rand):
        mock_rand.return_value = 15
        assert self.identifier.calculate_id() is None
        assert self.identifier.get_id() == '0x0f0f0f0f'

    def test_write(self):
        self.identifier.image_id = 'some-id'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            assert self.identifier.write('mbrid-file') is None

        m_open.assert_called_once_with('mbrid-file', 'w')
        m_open.return_value.write.assert_called_once_with('some-id\n')

    @patch('kiwi.storage.device_provider.DeviceProvider')
    def test_write_to_disk(self, mock_device_provider):
        self.identifier.image_id = '1'
        mock_device_provider.get_device.return_value('device')

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            assert self.identifier.write_to_disk(mock_device_provider) \
                is None
