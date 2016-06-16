
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container import ContainerImage


class TestContainerImage(object):
    @raises(KiwiContainerImageSetupError)
    def test_container_image_not_implemented(self):
        ContainerImage('foo', 'root_dir')

    @patch('kiwi.container.ContainerImageDocker')
    def test_container_image_docker(self, mock_docker):
        ContainerImage('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir')

    @patch('kiwi.container.ContainerImageLxd')
    def test_container_image_lxd(self, mock_lxd):
        ContainerImage('lxd', 'root_dir')
        mock_lxd.assert_called_once_with('root_dir')
