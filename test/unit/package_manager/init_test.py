from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.package_manager import PackageManager

from kiwi.exceptions import KiwiPackageManagerSetupError


class TestPackageManager:
    def test_package_manager_not_implemented(self):
        with raises(KiwiPackageManagerSetupError):
            PackageManager('repository', 'ms-manager')

    @patch('kiwi.package_manager.PackageManagerZypper')
    def test_manager_zypper(self, mock_manager):
        repository = Mock()
        PackageManager(repository, 'zypper')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerDnf')
    def test_manager_dnf(self, mock_manager):
        repository = Mock()
        PackageManager(repository, 'dnf')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerDnf')
    def test_manager_yum(self, mock_manager):
        repository = Mock()
        PackageManager(repository, 'yum')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerApt')
    def test_manager_apt(self, mock_manager):
        repository = Mock()
        PackageManager(repository, 'apt-get')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerPacman')
    def test_manager_pacman(self, mock_manager):
        repository = Mock()
        PackageManager(repository, 'pacman')
        mock_manager.assert_called_once_with(repository, None)
