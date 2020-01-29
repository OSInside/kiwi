# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import importlib
import logging
from collections import namedtuple
from xml.etree import ElementTree
from xml.dom import minidom

# project
from kiwi.exceptions import (
    KiwiSatSolverPluginError,
    KiwiSatSolverJobError,
    KiwiSatSolverJobProblems
)

log = logging.getLogger('kiwi')


class Sat:
    """
    **Sat Solver class to run package solver operations**

    The class uses SUSE's libsolv sat plugin
    """
    def __init__(self):
        """
        An instance of Sat auto loads the python solv plugin which is a
        python binding to the libsolv C library. An exception is raised
        if the module failed to load. On success a new solver pool is
        initialized for this instance

        :raises KiwiSatSolverPluginError: if libsolv module can't be loaded
        """
        try:
            self.solv = importlib.import_module('solv')
        except Exception as e:
            raise KiwiSatSolverPluginError(
                '{0}: {1}'.format(type(e).__name__, format(e))
            )

        self.pool = self.solv.Pool()
        self.pool.setarch()

    def add_repository(self, solver_repository):
        """
        Add a repository solvable to the pool. This basically add the
        required repository metadata which is needed to run a solver
        operation later.

        :param object solver_repository: Instance of :class:`SolverRepository`
        """
        solvable = solver_repository.create_repository_solvable()
        pool_repository = self.pool.add_repo(solver_repository.uri.uri)
        pool_repository.add_solv(solvable)
        self.pool.addfileprovides()
        self.pool.createwhatprovides()

    def solve(self, job_names, skip_missing=False, ignore_recommended=True):
        """
        Solve dependencies for the given job list. The list is allowed
        to contain element names of the following format:

        * name
          describes a package name

        * pattern:name
          describes a package collection name whose metadata type
          is called 'pattern' and stored as such in the repository
          metadata. Usually SUSE repos uses that

        * group:name
          describes a package collection name whose metadata type
          is called 'group' and stored as such in the repository
          metadata. Usually RHEL/CentOS/Fedora repos uses that

        :param list job_names: list of strings
        :param bool skip_missing: skip job if not found
        :param bool ignore_recommended: do not include recommended packages

        :raises KiwiSatSolverJobProblems: if solver reports solving problems
        :return: Transaction result information

        :rtype: dict
        """
        solver = self.pool.Solver()
        if ignore_recommended:
            solver.set_flag(self.solv.Solver.SOLVER_FLAG_IGNORE_RECOMMENDED, 1)

        solver_problems = solver.solve(
            self._setup_jobs(job_names, skip_missing)
        )
        solver_problem_info = self._evaluate_solver_problems(
            solver_problems
        )
        if solver_problem_info:
            raise KiwiSatSolverJobProblems(solver_problem_info)

        solver_transaction = solver.transaction()
        return self._evaluate_solver_result(
            solver_transaction
        )

    def _evaluate_solver_problems(self, solver_problems):
        """
        Iterate over solver problems and their solutions

        The method creates a pretty print XML information
        and returns that as a UTF-8 encoded string

        :param object solver_problems: result of :class:`Pool::Solver::solve()`

        :return: solver problem info and solutions

        :rtype: str
        """
        if solver_problems:
            problems = ElementTree.Element('problems')
            for problem in solver_problems:
                problem_detail = ElementTree.SubElement(
                    problems, 'problem', id=format(problem.id),
                    message=problem.findproblemrule().info().problemstr()
                )
                for solution in problem.solutions():
                    solution_detail = ElementTree.SubElement(
                        problem_detail, 'solution', id=format(solution.id)
                    )
                    for option in solution.elements(1):
                        solution_option = ElementTree.SubElement(
                            solution_detail, 'option'
                        )
                        solution_option.text = option.str()

            xml_data_unformatted = ElementTree.tostring(
                problems, 'utf-8'
            )
            xml_data_domtree = minidom.parseString(xml_data_unformatted)
            return xml_data_domtree.toprettyxml(indent="    ")

    def _evaluate_solver_result(self, solver_transaction):
        """
        Iterate over solver result and return a data dictionary

        :param object solver_transaction: result of :class:`Pool::Solver::transaction()`

        :return: dict of packages and their details

        :rtype: dict
        """
        result_type = namedtuple(
            'result_type', [
                'uri', 'installsize_bytes', 'arch', 'version', 'checksum'
            ]
        )
        result = {}
        for solvable in solver_transaction.newpackages():
            name = solvable.lookup_str(self.solv.SOLVABLE_NAME)
            result[name] = result_type(
                uri=solvable.repo.name,
                installsize_bytes=solvable.lookup_num(
                    self.solv.SOLVABLE_INSTALLSIZE
                ),
                arch=solvable.lookup_str(
                    self.solv.SOLVABLE_ARCH
                ),
                version=solvable.lookup_str(
                    self.solv.SOLVABLE_EVR
                ),
                checksum=solvable.lookup_checksum(
                    self.solv.SOLVABLE_CHECKSUM
                )
            )
        return result

    def _setup_jobs(self, job_names, skip_missing):
        """
        Create a solver job list from given list of job names

        :param list job_names: list of package,pattern,group names
        :param bool skip_missing: continue or raise if job selection failed

        :return: list of :class:`Pool.selection()` objects

        :rtype: list
        """
        jobs = []
        for job_name in job_names:
            selection_name = self.solv.Selection.SELECTION_NAME
            selection_provides = self.solv.Selection.SELECTION_PROVIDES
            selection = self.pool.select(
                job_name, selection_name | selection_provides
            )
            if selection.flags & self.solv.Selection.SELECTION_PROVIDES:
                log.info('--> Using capability match for {0}'.format(job_name))
            if selection.isempty():
                if skip_missing:
                    log.info(
                        '--> Package {0} not found: skipped'.format(job_name)
                    )
                else:
                    raise KiwiSatSolverJobError(
                        'Package {0} not found'.format(job_name)
                    )
            else:
                jobs += selection.jobs(self.solv.Job.SOLVER_INSTALL)

        return jobs
