from mock import patch
from pytest import raises
import mock

from kiwi.repository import Repository
from kiwi.exceptions import KiwiRepositorySetupError


class TestRepository:
    def test_repository_manager_not_implemented(self):
        with raises(KiwiRepositorySetupError):
            Repository.new('root_bind', 'ms-manager')

    @patch('kiwi.repository.zypper.RepositoryZypper')
    def test_repository_zypper(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'zypper')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.dnf.RepositoryDnf')
    def test_repository_dnf(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'dnf')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.dnf.RepositoryDnf')
    def test_repository_microdnf(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'microdnf')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.dnf.RepositoryDnf')
    def test_repository_yum(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'yum')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.apt.RepositoryApt')
    def test_repository_apt(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'apt-get')
        mock_manager.assert_called_once_with(root_bind, None)

    @patch('kiwi.repository.pacman.RepositoryPacman')
    def test_repository_pacman(self, mock_manager):
        root_bind = mock.Mock()
        Repository.new(root_bind, 'pacman')
        mock_manager.assert_called_once_with(root_bind, None)
