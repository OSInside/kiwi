from mock import patch

from kiwi.utils.temporary import Temporary


class TestTemporary:
    def setup(self):
        self.temporary = Temporary()

    @patch('kiwi.utils.temporary.NamedTemporaryFile')
    def test_new_file(self, mock_NamedTemporaryFile):
        self.temporary.new_file()
        mock_NamedTemporaryFile.assert_called_once_with(
            dir='/var/tmp', prefix='kiwi_'
        )

    @patch('kiwi.utils.temporary.TemporaryDirectory')
    def test_new_dir(self, mock_TemporaryDirectory):
        self.temporary.new_dir()
        mock_TemporaryDirectory.assert_called_once_with(
            dir='/var/tmp', prefix='kiwi_'
        )
