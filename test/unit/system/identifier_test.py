from mock import (
    patch, mock_open
)

from kiwi.system.identifier import SystemIdentifier


class TestSystemIdentifier:
    def setup(self):
        self.identifier = SystemIdentifier()

    def test_get_id(self):
        pass

    @patch('random.randrange')
    def test_calculate_id(self, mock_rand):
        mock_rand.return_value = 15
        self.identifier.calculate_id()
        assert self.identifier.get_id() == '0x0f0f0f0f'

    def test_write(self):
        self.identifier.image_id = 'some-id'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.identifier.write('mbrid-file')

        m_open.assert_called_once_with('mbrid-file', 'w')
        m_open.return_value.write.assert_called_once_with('some-id\n')
