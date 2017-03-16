
from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiBootLoaderInstallSetupError
from kiwi.bootloader.install import BootLoaderInstall


class TestBootLoaderInstall(object):
    @raises(KiwiBootLoaderInstallSetupError)
    def test_bootloader_install_not_implemented(self):
        BootLoaderInstall('foo', 'root_dir', mock.Mock())

    @patch('kiwi.bootloader.install.BootLoaderInstallGrub2')
    def test_bootloader_install_grub2(self, mock_grub2):
        device_provider = mock.Mock()
        BootLoaderInstall('grub2', 'root_dir', device_provider)
        mock_grub2.assert_called_once_with('root_dir', device_provider, None)

    @patch('kiwi.bootloader.install.BootLoaderInstallZipl')
    def test_bootloader_install_zipl(self, mock_zipl):
        device_provider = mock.Mock()
        BootLoaderInstall('grub2_s390x_emu', 'root_dir', device_provider)
        mock_zipl.assert_called_once_with('root_dir', device_provider, None)
