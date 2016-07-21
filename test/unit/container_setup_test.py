
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container.setup import ContainerSetup


class TestContainerSetup(object):
    @raises(KiwiContainerSetupError)
    def test_container_not_implemented(self):
        ContainerSetup('foo', 'root_dir')

    @patch('kiwi.container.setup.ContainerSetupDocker')
    def test_container_docker(self, mock_docker):
        ContainerSetup('docker', 'root_dir')
        mock_docker.assert_called_once_with('root_dir', None)

    @patch('kiwi.container.setup.ContainerSetupLxd')
    def test_container_lxd(self, mock_lxd):
        ContainerSetup('lxd', 'root_dir')
        mock_lxd.assert_called_once_with('root_dir', None)
