
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):
    def setup(self):
        self.docker = ContainerImageDocker('root_dir')

    @patch('kiwi.container.docker.ArchiveTar')
    def test_create(self, mock_archive):
        archive = mock.Mock()
        mock_archive.return_value = archive
        self.docker.create('result.tar.xz')
        mock_archive.assert_called_once_with('result.tar')
        archive.create_xz_compressed.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', 'boot', 'var/cache/kiwi'
            ], source_dir='root_dir'
        )
