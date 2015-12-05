from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install import BootLoaderInstall


class TestBootLoaderInstall(object):
    @raises(KiwiBootLoaderInstallSetupError)
    def test_bootloader_install_not_implemented(self):
        BootLoaderInstall.new('foo', 'source_dir', mock.Mock())

    @patch('kiwi.bootloader_install.BootLoaderInstallGrub2')
    def test_bootloader_install_grub2(self, mock_grub2):
        device_provider = mock.Mock()
        BootLoaderInstall.new('grub2', 'source_dir', device_provider)
        mock_grub2.assert_called_once_with('source_dir', device_provider)
