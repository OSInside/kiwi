from mock import patch

from .test_helper import raises

from kiwi.exceptions import KiwiContainerSetupError

from kiwi.container.setup import ContainerSetup


class TestContainerSetup(object):
    @raises(KiwiContainerSetupError)
    def test_container_not_implemented(self):
        ContainerSetup('foo', 'root_dir')

    @patch('kiwi.container.setup.ContainerSetupDocker')
    def test_container_docker(self, mock_docker):
        ContainerSetup('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.ContainerSetupOCI')
    def test_container_oci(self, mock_oci):
        ContainerSetup('oci', 'root_dir')
        mock_oci.assert_called_once_with('root_dir', None)
