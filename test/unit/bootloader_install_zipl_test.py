from nose.tools import *
from mock import patch
from mock import call

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.bootloader_install_zipl import BootLoaderInstallZipl


class TestBootLoaderInstallZipl(object):
    def setup(self):
        device_provider = mock.Mock()
        device_provider.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        self.bootloader = BootLoaderInstallZipl(
            'root_dir', device_provider, {'boot_mount_path': '/tmp/boot_zipl'}
        )
        assert self.bootloader.zipl_boot_mount_path == '/tmp/boot_zipl'

    @raises(KiwiBootLoaderZiplInstallError)
    def test_post_init_missing_boot_mount_path(self):
        self.bootloader.post_init(None)

    @patch('kiwi.bootloader_install_zipl.Command.run')
    def test_install(self, mock_command):
        self.bootloader.install()
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                'cd /tmp/boot_zipl && zipl -V -c /tmp/boot_zipl/config -m menu'
            ]
        )
