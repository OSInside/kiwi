from mock import Mock
from pytest import raises

from kiwi.bootloader.install.base import BootLoaderInstallBase


class TestBootLoaderInstallBase:
    def setup(self):
        self.bootloader = BootLoaderInstallBase(
            'root_dir', Mock()
        )

    def test_install(self):
        with raises(NotImplementedError):
            self.bootloader.install()

    def test_install_required(self):
        with raises(NotImplementedError):
            self.bootloader.install_required()
