from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.solver.repository import SolverRepository

from kiwi.exceptions import KiwiSolverRepositorySetupError


class TestSolverRepository:
    def setup(self):
        self.uri = Mock()
        self.uri.repo_type = 'some-unknown-type'

    def test_solver_repository_type_not_implemented(self):
        with raises(KiwiSolverRepositorySetupError):
            SolverRepository.new(self.uri)

    @patch('kiwi.solver.repository.suse.SolverRepositorySUSE')
    def test_solver_repository_suse(self, mock_suse):
        self.uri.repo_type = 'yast2'
        SolverRepository.new(self.uri)
        mock_suse.assert_called_once_with(self.uri, None, None)

    @patch('kiwi.solver.repository.rpm_md.SolverRepositoryRpmMd')
    def test_solver_repository_rpm_md(self, mock_rpm_md):
        self.uri.repo_type = 'rpm-md'
        SolverRepository.new(self.uri)
        mock_rpm_md.assert_called_once_with(self.uri, None, None)

    @patch('kiwi.solver.repository.rpm_dir.SolverRepositoryRpmDir')
    def test_solver_repository_rpm_dir(self, mock_rpm_dir):
        self.uri.repo_type = 'rpm-dir'
        SolverRepository.new(self.uri)
        mock_rpm_dir.assert_called_once_with(self.uri, None, None)

    @patch('kiwi.solver.repository.deb.SolverRepositoryDeb')
    def test_solver_repository_apt(self, mock_deb):
        self.uri.repo_type = 'apt-deb'
        SolverRepository.new(self.uri)
        mock_deb.assert_called_once_with(self.uri, None, None)
