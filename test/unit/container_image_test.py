from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.container_image import ContainerImage


class TestContainerImage(object):
    @raises(KiwiContainerImageSetupError)
    def test_container_image_not_implemented(self):
        ContainerImage('foo', 'root_dir')

    @patch('kiwi.container_image.ContainerImageDocker')
    def test_container_image_docker(self, mock_docker):
        ContainerImage('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir')
