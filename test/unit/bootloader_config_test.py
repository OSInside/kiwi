from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderConfigSetupError
from kiwi.bootloader.config import BootLoaderConfig


class TestBootLoaderConfig:
    def test_bootloader_config_not_implemented(self):
        with raises(KiwiBootLoaderConfigSetupError):
            BootLoaderConfig('foo', Mock(), 'root_dir')

    @patch('kiwi.bootloader.config.BootLoaderConfigGrub2')
    def test_bootloader_config_grub2(self, mock_grub2):
        xml_state = Mock()
        BootLoaderConfig('grub2', xml_state, 'root_dir')
        mock_grub2.assert_called_once_with(xml_state, 'root_dir', None, None)

    @patch('kiwi.bootloader.config.BootLoaderConfigIsoLinux')
    def test_bootloader_config_isolinux(self, mock_isolinux):
        xml_state = Mock()
        BootLoaderConfig('isolinux', xml_state, 'root_dir', 'boot_dir')
        mock_isolinux.assert_called_once_with(
            xml_state, 'root_dir', 'boot_dir', None
        )

    @patch('kiwi.bootloader.config.BootLoaderConfigZipl')
    def test_bootloader_config_zipl(self, mock_zipl):
        xml_state = Mock()
        BootLoaderConfig('grub2_s390x_emu', xml_state, 'root_dir')
        mock_zipl.assert_called_once_with(xml_state, 'root_dir', None, None)
