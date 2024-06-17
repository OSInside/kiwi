from unittest.mock import Mock
from pytest import raises

from kiwi.bootloader.install.systemd_boot import BootLoaderInstallSystemdBoot


class TestBootLoaderInstallSystemdBoot:
    def setup(self):
        self.bootloader = BootLoaderInstallSystemdBoot(
            Mock(), 'root_dir', Mock()
        )

    def setup_method(self, cls):
        self.setup()

    def test_install(self):
        with raises(NotImplementedError):
            self.bootloader.install()

    def test_install_required(self):
        assert self.bootloader.install_required() is False

    def test_secure_boot_install(self):
        # just pass
        self.bootloader.secure_boot_install()
