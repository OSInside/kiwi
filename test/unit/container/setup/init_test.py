from mock import patch
from pytest import raises

from kiwi.container.setup import ContainerSetup

from kiwi.exceptions import KiwiContainerSetupError


class TestContainerSetup:
    def test_container_not_implemented(self):
        with raises(KiwiContainerSetupError):
            ContainerSetup('foo', 'root_dir')

    @patch('kiwi.container.setup.ContainerSetupDocker')
    def test_container_docker(self, mock_docker):
        ContainerSetup('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.ContainerSetupOCI')
    def test_container_oci(self, mock_oci):
        ContainerSetup('oci', 'root_dir')
        mock_oci.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.ContainerSetupAppx')
    def test_container_appx(self, mock_appx):
        ContainerSetup('appx', 'root_dir')
        mock_appx.assert_called_once_with('root_dir', None)
