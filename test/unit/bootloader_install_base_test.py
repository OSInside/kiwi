from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install_base import BootLoaderInstallBase


class TestBootLoaderInstallBase(object):
    def setup(self):
        self.bootloader = BootLoaderInstallBase(
            'source_dir', mock.Mock()
        )

    @raises(NotImplementedError)
    def test_install(self):
        self.bootloader.install()
