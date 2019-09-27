from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderInstallSetupError
from kiwi.bootloader.install import BootLoaderInstall


class TestBootLoaderInstall:
    def test_bootloader_install_not_implemented(self):
        with raises(KiwiBootLoaderInstallSetupError):
            BootLoaderInstall('foo', 'root_dir', Mock())

    @patch('kiwi.bootloader.install.BootLoaderInstallGrub2')
    def test_bootloader_install_grub2(self, mock_grub2):
        device_provider = Mock()
        BootLoaderInstall('grub2', 'root_dir', device_provider)
        mock_grub2.assert_called_once_with('root_dir', device_provider, None)

    @patch('kiwi.bootloader.install.BootLoaderInstallZipl')
    def test_bootloader_install_zipl(self, mock_zipl):
        device_provider = Mock()
        BootLoaderInstall('grub2_s390x_emu', 'root_dir', device_provider)
        mock_zipl.assert_called_once_with('root_dir', device_provider, None)
