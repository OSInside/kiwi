from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.repository import Repository
from kiwi.exceptions import *


class TestRepository(object):
    @raises(KiwiRepositorySetupError)
    def test_repository_manager_not_implemented(self):
        Repository.new('root_bind', 'ms-manager')

    @patch('kiwi.repository.RepositoryZypper')
    def test_repository_zypper_new(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'zypper')
        mock_manager.assert_called_once_with(root_bind, None)
