from mock import patch
import mock

from .test_helper import raises

from kiwi.solver.sat import Sat
from kiwi.exceptions import (
    KiwiSatSolverPluginError,
    KiwiSatSolverJobProblems,
    KiwiSatSolverJobError
)


class TestSat(object):
    @patch('importlib.import_module')
    def setup(self, mock_import_module):
        self.sat = Sat()
        self.solver = mock.MagicMock()
        self.transaction = mock.Mock()
        self.transaction.newpackages = mock.Mock(
            return_value=[mock.Mock()]
        )
        self.selection = mock.Mock()
        self.solver.transaction = mock.Mock(
            return_value=self.transaction
        )
        self.sat.pool.Solver = mock.Mock(
            return_value=self.solver
        )
        self.sat.pool.select = mock.Mock(
            return_value=self.selection
        )
        mock_import_module.assert_called_once_with('solv')

    @patch('importlib.import_module')
    @raises(KiwiSatSolverPluginError)
    def test_setup_no_sat_plugin(self, mock_import_module):
        mock_import_module.side_effect = Exception
        Sat()

    def test_add_repository(self):
        solver_repository = mock.Mock()
        solver_repository.uri.uri = 'some-uri'
        solvable = mock.Mock()
        solver_repository.create_repository_solvable.return_value = solvable
        pool_repository = mock.Mock()
        self.sat.pool.add_repo.return_value = pool_repository

        self.sat.add_repository(solver_repository)

        solver_repository.create_repository_solvable.assert_called_once_with()
        self.sat.pool.add_repo.assert_called_once_with('some-uri')
        pool_repository.add_solv.assert_called_once_with(solvable)
        self.sat.pool.addfileprovides.assert_called_once_with()
        self.sat.pool.createwhatprovides.assert_called_once_with()

    @raises(KiwiSatSolverJobProblems)
    @patch.object(Sat, '_setup_jobs')
    def test_solve_has_problems(self, mock_setup_jobs):
        packages = ['vim']
        problem = mock.Mock()
        problem.id = 42
        info = mock.Mock()
        info.problemstr = mock.Mock(
            return_value='some-problem'
        )
        findproblemrule = mock.Mock()
        findproblemrule.info = mock.Mock(
            return_value=info
        )
        problem.findproblemrule.return_value = findproblemrule

        option = mock.Mock()
        option.str = mock.Mock(
            return_value='some-option'
        )
        solution = mock.Mock()
        solution.id = 42
        solution.elements = mock.Mock(
            return_value=[option]
        )
        problem.solutions.return_value = [solution]
        self.solver.solve = mock.Mock(
            return_value=[problem]
        )
        self.sat.solve(packages)

    @patch('kiwi.logger.log.info')
    def test_solve_package_not_found_and_skipped(self, mock_log_info):
        packages = ['vim']
        self.solver.solve = mock.Mock(
            return_value=None
        )
        self.sat.solv.Selection.SELECTION_PROVIDES = 0
        self.selection.flags = mock.Mock(
            return_value=0
        )
        self.selection.isempty = mock.Mock(
            return_value=True
        )
        self.sat.solve(packages, skip_missing=True)
        mock_log_info.assert_called_once_with(
            '--> Package vim not found: skipped'
        )

    @raises(KiwiSatSolverJobError)
    def test_solve_package_not_found_raises(self):
        packages = ['vim']
        self.solver.solve = mock.Mock(
            return_value=None
        )
        self.selection.isempty = mock.Mock(
            return_value=True
        )
        self.sat.solve(packages)

    def test_solve(self):
        packages = ['vim']
        self.solver.solve = mock.Mock(
            return_value=None
        )
        self.selection.isempty = mock.Mock(
            return_value=False
        )
        self.selection.jobs = mock.Mock(
            return_value=packages
        )
        self.sat.solve(packages)
        self.solver.solve.assert_called_once_with(['vim'])
        self.solver.transaction.assert_called_once_with()

    @patch('kiwi.logger.log.info')
    def test_solve_with_capabilities(self, mock_log_info):
        packages = ['kernel-base']
        self.solver.solve = mock.Mock(
            return_value=None
        )
        self.sat.solv.Selection.SELECTION_PROVIDES = 1
        self.selection.flags = mock.Mock(
            return_value=1
        )
        self.selection.isempty = mock.Mock(
            return_value=False
        )
        self.selection.jobs = mock.Mock(
            return_value=packages
        )
        self.sat.solve(packages)
        mock_log_info.assert_called_once_with(
            '--> Using capability match for kernel-base'
        )
