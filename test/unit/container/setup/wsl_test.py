from pytest import raises
from unittest.mock import patch

from kiwi.container.setup.wsl import ContainerSetupWsl
from kiwi.exceptions import KiwiContainerSetupError


class TestContainerSetupAppx:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        self.wsl = ContainerSetupWsl('root_dir')

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('os.path.exists')
    def test_setup(self, mock_exists):

        def exists(path):
            if path == path_to_fail:
                return False
            return True

        mock_exists.side_effect = exists

        path_to_fail = 'root_dir/etc/wsl-distribution.conf'
        with raises(KiwiContainerSetupError):
            self.wsl.setup()

        path_to_fail = 'root_dir/etc/wsl.conf'
        with raises(KiwiContainerSetupError):
            self.wsl.setup()
