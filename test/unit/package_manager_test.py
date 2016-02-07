from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.package_manager import PackageManager
from kiwi.exceptions import *


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
