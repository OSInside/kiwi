from mock import patch
from pytest import raises

from kiwi.container import ContainerImage

from kiwi.exceptions import KiwiContainerImageSetupError


class TestContainerImage:
    def test_container_image_not_implemented(self):
        with raises(KiwiContainerImageSetupError):
            ContainerImage.new('foo', 'root_dir')

    @patch('kiwi.container.oci.ContainerImageOCI')
    def test_container_image_docker(self, mock_docker):
        ContainerImage.new('docker', 'root_dir')
        mock_docker.assert_called_once_with(
            'root_dir', 'docker-archive', None
        )

    @patch('kiwi.container.oci.ContainerImageOCI')
    def test_container_image_oci(self, mock_oci):
        ContainerImage.new('oci', 'root_dir')
        mock_oci.assert_called_once_with(
            'root_dir', 'oci-archive', None
        )

    @patch('kiwi.container.appx.ContainerImageAppx')
    def test_container_image_appx(self, mock_appx):
        ContainerImage.new('appx', 'root_dir')
        mock_appx.assert_called_once_with(
            'root_dir', None
        )
