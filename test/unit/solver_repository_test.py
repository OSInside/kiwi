from mock import patch

import mock

from .test_helper import raises

from kiwi.solver.repository import SolverRepository
from kiwi.exceptions import KiwiSolverRepositorySetupError


class TestSolverRepository(object):
    @raises(KiwiSolverRepositorySetupError)
    def test_solver_repository_type_not_implemented(self):
        SolverRepository('some-unknown-type', mock.Mock())

    @patch('kiwi.solver.repository.SolverRepositorySUSE')
    def test_solver_repository_suse(self, mock_suse):
        uri = mock.Mock()
        SolverRepository('yast2', uri)
        mock_suse.assert_called_once_with(uri)

    @patch('kiwi.solver.repository.SolverRepositoryRpmMd')
    def test_solver_repository_rpm_md(self, mock_rpm_md):
        uri = mock.Mock()
        SolverRepository('rpm-md', uri)
        mock_rpm_md.assert_called_once_with(uri)

    @patch('kiwi.solver.repository.SolverRepositoryRpmDir')
    def test_solver_repository_rpm_dir(self, mock_rpm_dir):
        uri = mock.Mock()
        SolverRepository('rpm-dir', uri)
        mock_rpm_dir.assert_called_once_with(uri)
