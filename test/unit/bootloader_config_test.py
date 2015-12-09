from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_config import BootLoaderConfig


class TestBootLoaderConfig(object):
    @raises(KiwiBootLoaderConfigSetupError)
    def test_bootloader_config_not_implemented(self):
        BootLoaderConfig.new('foo', mock.Mock(), 'source_dir')

    @patch('kiwi.bootloader_config.BootLoaderConfigGrub2')
    def test_bootloader_config_grub2(self, mock_grub2):
        xml_state = mock.Mock()
        BootLoaderConfig.new('grub2', xml_state, 'source_dir')
        mock_grub2.assert_called_once_with(xml_state, 'source_dir')

    @patch('kiwi.bootloader_config.BootLoaderConfigIsoLinux')
    def test_bootloader_config_isolinux(self, mock_isolinux):
        xml_state = mock.Mock()
        BootLoaderConfig.new('isolinux', xml_state, 'source_dir')
        mock_isolinux.assert_called_once_with(xml_state, 'source_dir')
