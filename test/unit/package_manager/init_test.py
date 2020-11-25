from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.package_manager import PackageManager

from kiwi.exceptions import KiwiPackageManagerSetupError


class TestPackageManager:
    def test_package_manager_not_implemented(self):
        with raises(KiwiPackageManagerSetupError):
            PackageManager.new('repository', 'ms-manager')

    @patch('kiwi.package_manager.zypper.PackageManagerZypper')
    def test_manager_zypper(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'zypper')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.dnf.PackageManagerDnf')
    def test_manager_dnf(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'dnf')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.dnf.PackageManagerDnf')
    def test_manager_yum(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'yum')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.microdnf.PackageManagerMicroDnf')
    def test_manager_microdnf(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'microdnf')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.apt.PackageManagerApt')
    def test_manager_apt(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'apt-get')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.pacman.PackageManagerPacman')
    def test_manager_pacman(self, mock_manager):
        repository = Mock()
        PackageManager.new(repository, 'pacman')
        mock_manager.assert_called_once_with(repository, None)
