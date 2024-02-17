from unittest.mock import (
    patch, Mock
)
from kiwi.solver.repository.deb import SolverRepositoryDeb
from kiwi.solver.repository.base import SolverRepositoryBase


class TestSolverRepositoryDeb:
    def setup(self):
        self.uri = Mock()
        self.uri.uri = 'http://example.org/some/path'
        self.solver = SolverRepositoryDeb(self.uri)

    def setup_method(self, cls):
        self.setup()

    @patch.object(SolverRepositoryBase, '_get_deb_packages')
    @patch.object(SolverRepositoryBase, '_create_solvables')
    @patch.object(SolverRepositoryBase, '_create_temporary_metadata_dir')
    def test__setup_repository_metadata(
        self, mock_mkdtemp, mock_create_solvables, mock_get_deb_packages
    ):
        mock_mkdtemp.return_value = 'metadata_dir.XX'
        self.solver._setup_repository_metadata()
        mock_get_deb_packages.assert_called_once_with(
            download_dir='metadata_dir.XX'
        )
        mock_create_solvables.assert_called_once_with(
            'metadata_dir.XX', 'deb2solv'
        )
