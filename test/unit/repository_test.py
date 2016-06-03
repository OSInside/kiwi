
from mock import patch

import mock

from .test_helper import *

from kiwi.repository import Repository
from kiwi.exceptions import *


class TestRepository(object):
    @raises(KiwiRepositorySetupError)
    def test_repository_manager_not_implemented(self):
        Repository('root_bind', 'ms-manager')

    @patch('kiwi.repository.RepositoryZypper')
    def test_repository_zypper(self, mock_manager):
        root_bind = mock.Mock()
        Repository(root_bind, 'zypper')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.RepositoryYum')
    def test_repository_yum(self, mock_manager):
        root_bind = mock.Mock()
        Repository(root_bind, 'yum')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.RepositoryApt')
    def test_repository_apt(self, mock_manager):
        root_bind = mock.Mock()
        Repository(root_bind, 'apt-get')
        mock_manager.assert_called_once_with(root_bind, None)
