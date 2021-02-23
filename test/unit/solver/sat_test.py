import logging
from mock import (
    patch, Mock, MagicMock
)
from pytest import (
    raises, fixture
)

from kiwi.solver.sat import Sat

from kiwi.exceptions import (
    KiwiSatSolverPluginError,
    KiwiSatSolverJobProblems,
    KiwiSatSolverJobError
)


class TestSat:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('importlib.import_module')
    def setup(self, mock_import_module):
        self.sat = Sat()
        self.solver = MagicMock()
        self.transaction = Mock()
        self.transaction.newpackages = Mock(
            return_value=[Mock()]
        )
        self.selection = Mock()
        self.solver.transaction = Mock(
            return_value=self.transaction
        )
        self.sat.pool.Solver = Mock(
            return_value=self.solver
        )
        self.sat.pool.select = Mock(
            return_value=self.selection
        )
        mock_import_module.assert_called_once_with('solv')
        self.solv = mock_import_module.return_value
        self.sat.pool.setarch.assert_called_once_with()
        self.sat.pool.setarch.reset_mock()

    @patch('importlib.import_module')
    def test_setup_no_sat_plugin(self, mock_import_module):
        mock_import_module.side_effect = Exception
        with raises(KiwiSatSolverPluginError):
            Sat()

    @patch('platform.machine')
    def test_set_dist_type_raises(self, mock_platform_machine):
        mock_platform_machine.return_value = 'x86_64'
        self.sat.pool.setdisttype.return_value = -1
        with raises(KiwiSatSolverPluginError):
            self.sat.set_dist_type('deb')

    @patch('platform.machine')
    def test_set_dist_type_deb(self, mock_platform_machine):
        mock_platform_machine.return_value = 'x86_64'
        self.sat.pool.setdisttype.return_value = 0
        self.sat.set_dist_type('deb')
        self.sat.pool.setdisttype.assert_called_once_with(
            self.solv.Pool.DISTTYPE_DEB
        )
        self.sat.pool.setarch.assert_called_once_with(
            'amd64'
        )

    def test_add_repository(self):
        solver_repository = Mock()
        solver_repository.uri.uri = 'some-uri'
        solvable = Mock()
        solver_repository.create_repository_solvable.return_value = solvable
        pool_repository = Mock()
        self.sat.pool.add_repo.return_value = pool_repository

        self.sat.add_repository(solver_repository)

        solver_repository.create_repository_solvable.assert_called_once_with()
        self.sat.pool.add_repo.assert_called_once_with('some-uri')
        pool_repository.add_solv.assert_called_once_with(solvable)
        self.sat.pool.addfileprovides.assert_called_once_with()
        self.sat.pool.createwhatprovides.assert_called_once_with()

    @patch.object(Sat, '_setup_jobs')
    def test_solve_has_problems(self, mock_setup_jobs):
        packages = ['vim']
        problem = Mock()
        problem.id = 42
        info = Mock()
        info.problemstr = Mock(
            return_value='some-problem'
        )
        findproblemrule = Mock()
        findproblemrule.info = Mock(
            return_value=info
        )
        problem.findproblemrule.return_value = findproblemrule

        option = Mock()
        option.str = Mock(
            return_value='some-option'
        )
        solution = Mock()
        solution.id = 42
        solution.elements = Mock(
            return_value=[option]
        )
        problem.solutions.return_value = [solution]
        self.solver.solve = Mock(
            return_value=[problem]
        )
        with raises(KiwiSatSolverJobProblems):
            self.sat.solve(packages)

    def test_solve_package_not_found_and_skipped(self):
        packages = ['vim']
        self.solver.solve = Mock(
            return_value=None
        )
        self.sat.solv.Selection.SELECTION_PROVIDES = 0
        self.selection.flags = 0
        self.selection.isempty = Mock(
            return_value=True
        )
        with self._caplog.at_level(logging.INFO):
            self.sat.solve(packages, skip_missing=True)
            assert '--> Package vim not found: skipped' in self._caplog.text

    def test_solve_package_not_found_raises(self):
        packages = ['vim']
        self.solver.solve = Mock(
            return_value=None
        )
        self.selection.isempty = Mock(
            return_value=True
        )
        with raises(KiwiSatSolverJobError):
            self.sat.solve(packages)

    def test_solve_apt_get(self):
        # There is a special handling for apt-get. In kiwi the
        # package manager for debian based distros is selected
        # by the name apt-get. That name is added to the package
        # list, but apt-get does not really exist in Debian based
        # distros. The name of the package manager from a packaging
        # perspective is just: apt not apt-get. We should change
        # this in the schema and code in kiwi. But so far we
        # have the hack here
        packages = ['apt-get']
        self.solver.solve = Mock(
            return_value=None
        )
        self.selection.isempty = Mock(
            return_value=False
        )
        self.selection.jobs = Mock(
            return_value=packages
        )
        self.sat.solve(packages)
        selection_name = self.solv.Selection.SELECTION_NAME
        selection_provides = self.solv.Selection.SELECTION_PROVIDES
        self.sat.pool.select.assert_called_once_with(
            'apt', selection_name | selection_provides
        )

    def test_solve(self):
        packages = ['vim']
        self.solver.solve = Mock(
            return_value=None
        )
        self.selection.isempty = Mock(
            return_value=False
        )
        self.selection.jobs = Mock(
            return_value=packages
        )
        self.sat.solve(packages)
        self.solver.solve.assert_called_once_with(['vim'])
        self.solver.transaction.assert_called_once_with()

    def test_solve_with_capabilities(self):
        packages = ['kernel-base']
        self.solver.solve = Mock(
            return_value=None
        )
        self.sat.solv.Selection.SELECTION_PROVIDES = 1
        self.selection.flags = 1
        self.selection.isempty = Mock(
            return_value=False
        )
        self.selection.jobs = Mock(
            return_value=packages
        )
        with self._caplog.at_level(logging.INFO):
            self.sat.solve(packages)
            assert '--> Using capability match for kernel-base' in \
                self._caplog.text
