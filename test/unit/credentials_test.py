from mock import patch

from kiwi.credentials import Credentials


class TestCredentials:
    def setup(self):
        self.credentials = Credentials()

    @patch('kiwi.credentials.getpass')
    def test_get_obs_credentials(self, mock_getpass):
        assert self.credentials.get_obs_credentials('user') == \
            mock_getpass.return_value
        mock_getpass.assert_called_once_with(
            'Enter OBS password for user: '
        )
