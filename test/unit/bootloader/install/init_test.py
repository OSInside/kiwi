from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderInstallSetupError
from kiwi.bootloader.install import BootLoaderInstall


class TestBootLoaderInstall:
    def test_bootloader_install_not_implemented(self):
        with raises(KiwiBootLoaderInstallSetupError):
            BootLoaderInstall.new('foo', Mock(), 'root_dir', Mock())

    @patch('kiwi.bootloader.install.grub2.BootLoaderInstallGrub2')
    def test_bootloader_install_grub2(self, mock_grub2):
        device_provider = Mock()
        xml_state = Mock()
        BootLoaderInstall.new('grub2', xml_state, 'root_dir', device_provider)
        mock_grub2.assert_called_once_with(
            xml_state, 'root_dir', device_provider, None
        )
