from unittest.mock import patch
from pytest import raises

from kiwi.container.setup import ContainerSetup

from kiwi.exceptions import KiwiContainerSetupError


class TestContainerSetup:
    def test_container_not_implemented(self):
        with raises(KiwiContainerSetupError):
            ContainerSetup.new('foo', 'root_dir')

    @patch('kiwi.container.setup.docker.ContainerSetupDocker')
    def test_container_docker(self, mock_docker):
        ContainerSetup.new('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.oci.ContainerSetupOCI')
    def test_container_oci(self, mock_oci):
        ContainerSetup.new('oci', 'root_dir')
        mock_oci.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.appx.ContainerSetupAppx')
    def test_container_appx(self, mock_appx):
        ContainerSetup.new('appx', 'root_dir')
        mock_appx.assert_called_once_with('root_dir', None)
