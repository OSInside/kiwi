from mock import patch
from pytest import raises

from kiwi.container import ContainerImage

from kiwi.exceptions import KiwiContainerImageSetupError


class TestContainerImage:
    def test_container_image_not_implemented(self):
        with raises(KiwiContainerImageSetupError):
            ContainerImage('foo', 'root_dir')

    @patch('kiwi.container.ContainerImageOCI')
    def test_container_image_docker(self, mock_docker):
        ContainerImage('docker', 'root_dir')
        mock_docker.assert_called_once_with(
            'root_dir', 'docker-archive', custom_args=None
        )

    @patch('kiwi.container.ContainerImageOCI')
    def test_container_image_oci(self, mock_oci):
        ContainerImage('oci', 'root_dir')
        mock_oci.assert_called_once_with(
            'root_dir', 'oci-archive', custom_args=None
        )

    @patch('kiwi.container.ContainerImageAppx')
    def test_container_image_appx(self, mock_appx):
        ContainerImage('appx', 'root_dir')
        mock_appx.assert_called_once_with(
            'root_dir', custom_args=None
        )
