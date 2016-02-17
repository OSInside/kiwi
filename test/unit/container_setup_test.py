from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.container_setup import ContainerSetup


class TestContainerSetup(object):
    @raises(KiwiContainerSetupError)
    def test_container_not_implemented(self):
        ContainerSetup('foo', 'root_dir')

    @patch('kiwi.container_setup.ContainerSetupDocker')
    def test_container_docker(self, mock_docker):
        ContainerSetup('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir', None)
