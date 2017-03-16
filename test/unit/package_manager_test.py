from mock import patch

import mock

from .test_helper import raises

from kiwi.package_manager import PackageManager

from kiwi.exceptions import KiwiPackageManagerSetupError


class TestPackageManager(object):
    @raises(KiwiPackageManagerSetupError)
    def test_package_manager_not_implemented(self):
        PackageManager('repository', 'ms-manager')

    @patch('kiwi.package_manager.PackageManagerZypper')
    def test_manager_zypper(self, mock_manager):
        repository = mock.Mock()
        PackageManager(repository, 'zypper')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerYum')
    def test_manager_yum(self, mock_manager):
        repository = mock.Mock()
        PackageManager(repository, 'yum')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerDnf')
    def test_manager_dnf(self, mock_manager):
        repository = mock.Mock()
        PackageManager(repository, 'dnf')
        mock_manager.assert_called_once_with(repository, None)

    @patch('kiwi.package_manager.PackageManagerApt')
    def test_manager_apt(self, mock_manager):
        repository = mock.Mock()
        PackageManager(repository, 'apt-get')
        mock_manager.assert_called_once_with(repository, None)
