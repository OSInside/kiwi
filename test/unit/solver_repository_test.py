from mock import patch

import mock

from .test_helper import raises

from kiwi.solver.repository import SolverRepository
from kiwi.exceptions import KiwiSolverRepositorySetupError


class TestSolverRepository(object):
    def setup(self):
        self.uri = mock.Mock()
        self.uri.repo_type = 'some-unknown-type'

    @raises(KiwiSolverRepositorySetupError)
    def test_solver_repository_type_not_implemented(self):
        SolverRepository(self.uri)

    @patch('kiwi.solver.repository.SolverRepositorySUSE')
    def test_solver_repository_suse(self, mock_suse):
        self.uri.repo_type = 'yast2'
        SolverRepository(self.uri)
        mock_suse.assert_called_once_with(self.uri, None, None)

    @patch('kiwi.solver.repository.SolverRepositoryRpmMd')
    def test_solver_repository_rpm_md(self, mock_rpm_md):
        self.uri.repo_type = 'rpm-md'
        SolverRepository(self.uri)
        mock_rpm_md.assert_called_once_with(self.uri, None, None)

    @patch('kiwi.solver.repository.SolverRepositoryRpmDir')
    def test_solver_repository_rpm_dir(self, mock_rpm_dir):
        self.uri.repo_type = 'rpm-dir'
        SolverRepository(self.uri)
        mock_rpm_dir.assert_called_once_with(self.uri, None, None)
