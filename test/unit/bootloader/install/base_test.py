from unittest.mock import Mock
from pytest import raises

from kiwi.bootloader.install.base import BootLoaderInstallBase


class TestBootLoaderInstallBase:
    def setup(self):
        self.bootloader = BootLoaderInstallBase(
            Mock(), 'root_dir', Mock()
        )

    def setup_method(self, cls):
        self.setup()

    def test_install(self):
        with raises(NotImplementedError):
            self.bootloader.install()

    def test_install_required(self):
        with raises(NotImplementedError):
            self.bootloader.install_required()

    def test_secure_boot_install(self):
        with raises(NotImplementedError):
            self.bootloader.secure_boot_install()
