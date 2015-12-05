from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.package_manager import PackageManager
from kiwi.exceptions import *


class TestPackageManager(object):
    @raises(KiwiPackageManagerSetupError)
    def test_package_manager_not_implemented(self):
        PackageManager.new('repository', 'ms-manager')

    @patch('kiwi.package_manager.PackageManagerZypper')
    def test_manager_zypper_new(self, mock_manager):
        repository = mock.Mock()
        PackageManager.new(repository, 'zypper')
        mock_manager.assert_called_once_with(repository, None)
