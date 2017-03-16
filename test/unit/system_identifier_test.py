from mock import patch

import mock

from .test_helper import patch_open

from kiwi.system.identifier import SystemIdentifier


class TestSystemIdentifier(object):
    def setup(self):
        self.identifier = SystemIdentifier()

    def test_get_id(self):
        pass

    @patch('random.randrange')
    def test_calculate_id(self, mock_rand):
        mock_rand.return_value = 15
        self.identifier.calculate_id()
        assert self.identifier.get_id() == '0x0f0f0f0f'

    @patch_open
    def test_write(self, mock_open):
        self.identifier.image_id = 'some-id'
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.identifier.write('mbrid-file')
        mock_open.assert_called_once_with('mbrid-file', 'w')
        file_mock.write.assert_called_once_with('some-id\n')
