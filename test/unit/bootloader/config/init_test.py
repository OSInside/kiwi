from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderConfigSetupError
from kiwi.bootloader.config import create_boot_loader_config


class TestBootLoaderConfig:
    def test_bootloader_config_not_implemented(self):
        with raises(KiwiBootLoaderConfigSetupError):
            create_boot_loader_config(
                name='foo', xml_state=Mock(), root_dir='root_dir'
            )

    @patch('kiwi.bootloader.config.grub2.BootLoaderConfigGrub2')
    def test_bootloader_config_grub2(self, mock_grub2):
        xml_state = Mock()
        for name in ("grub2", "grub2_s390x_emu"):
            create_boot_loader_config(
                name=name, xml_state=xml_state, root_dir='root_dir'
            )
            mock_grub2.assert_called_once_with(
                xml_state, 'root_dir', None, None
            )
            mock_grub2.reset_mock()

    @patch('kiwi.bootloader.config.systemd_boot.BootLoaderSystemdBoot')
    def test_bootloader_config_systemd_boot(self, mock_systemd_boot):
        xml_state = Mock()
        create_boot_loader_config(
            name='systemd_boot', xml_state=xml_state,
            root_dir='root_dir', boot_dir='boot_dir'
        )
        mock_systemd_boot.assert_called_once_with(
            xml_state, 'root_dir', 'boot_dir', None
        )

    @patch('kiwi.bootloader.config.zipl.BootLoaderZipl')
    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def test_bootloader_config_zipl(self, mock_FirmWare, mock_zipl):
        xml_state = Mock()
        create_boot_loader_config(
            name='zipl', xml_state=xml_state,
            root_dir='root_dir', boot_dir='boot_dir'
        )
        mock_zipl.assert_called_once_with(
            xml_state, 'root_dir', 'boot_dir', None
        )

    @patch('kiwi.bootloader.config.custom.BootLoaderConfigCustom')
    def test_bootloader_config_custom(self, mock_custom):
        xml_state = Mock()
        create_boot_loader_config(
            name='custom', xml_state=xml_state, root_dir='root_dir'
        )
        mock_custom.assert_called_once_with(
            xml_state, 'root_dir', None, None
        )
