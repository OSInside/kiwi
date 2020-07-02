from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiBootLoaderZiplInstallError
from kiwi.bootloader.install.zipl import BootLoaderInstallZipl


class TestBootLoaderInstallZipl:
    @patch('kiwi.bootloader.install.zipl.MountManager')
    def setup(self, mock_mount):
        custom_args = {
            'boot_device': '/dev/mapper/loop0p1'
        }
        boot_mount = Mock()
        boot_mount.device = custom_args['boot_device']
        boot_mount.mountpoint = 'tmp_boot'

        mock_mount.return_value = boot_mount

        device_provider = Mock()
        device_provider.get_device = Mock(
            return_value='/dev/some-device'
        )
        self.bootloader = BootLoaderInstallZipl(
            'root_dir', device_provider, custom_args
        )

    def test_post_init_missing_boot_mount_path(self):
        with raises(KiwiBootLoaderZiplInstallError):
            self.bootloader.post_init(None)

    def test_install_required(self):
        assert self.bootloader.install_required() is True

    @patch('kiwi.bootloader.install.zipl.Command.run')
    def test_install(self, mock_Command_run):
        self.bootloader.install()
        self.bootloader.boot_mount.mount.assert_called_once_with()
        mock_Command_run.assert_called_once_with(
            ['bash', '-c', 'cd root_dir/boot && zipl -V -c zipl/config -m menu']
        )

    def test_destructor(self):
        self.bootloader.__del__()
        self.bootloader.boot_mount.umount.assert_called_once_with()
