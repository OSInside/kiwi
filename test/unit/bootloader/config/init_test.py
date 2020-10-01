from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderConfigSetupError
from kiwi.bootloader.config import BootLoaderConfig


class TestBootLoaderConfig:
    def test_bootloader_config_not_implemented(self):
        with raises(KiwiBootLoaderConfigSetupError):
            BootLoaderConfig.new('foo', Mock(), 'root_dir')

    @patch('kiwi.bootloader.config.grub2.BootLoaderConfigGrub2')
    def test_bootloader_config_grub2(self, mock_grub2):
        xml_state = Mock()
        BootLoaderConfig.new('grub2', xml_state, 'root_dir')
        mock_grub2.assert_called_once_with(xml_state, 'root_dir', None, None)

    @patch('kiwi.bootloader.config.isolinux.BootLoaderConfigIsoLinux')
    def test_bootloader_config_isolinux(self, mock_isolinux):
        xml_state = Mock()
        BootLoaderConfig.new('isolinux', xml_state, 'root_dir', 'boot_dir')
        mock_isolinux.assert_called_once_with(
            xml_state, 'root_dir', 'boot_dir', None
        )
