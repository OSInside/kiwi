from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.solver.repository.rpm_dir import SolverRepositoryRpmDir
from kiwi.solver.repository.base import SolverRepositoryBase

from kiwi.exceptions import KiwiRpmDirNotRemoteError


class TestSolverRepositoryRpmDir:
    def setup(self):
        self.uri = Mock()
        self.uri.uri = 'http://example.org/some/path'
        self.solver = SolverRepositoryRpmDir(self.uri)

    def setup_method(self, cls):
        self.setup()

    def test__setup_repository_metadata_raises(self):
        with raises(KiwiRpmDirNotRemoteError):
            self.solver._setup_repository_metadata()

    @patch.object(SolverRepositoryBase, 'download_from_repository')
    @patch.object(SolverRepositoryBase, '_create_solvables')
    @patch.object(SolverRepositoryBase, '_create_temporary_metadata_dir')
    @patch('kiwi.solver.repository.rpm_dir.glob.iglob')
    def test__setup_repository_metadata(
        self, mock_iglob, mock_mkdtemp, mock_create_solvables,
        mock_download_from_repository
    ):
        self.uri.is_remote.return_value = False
        self.uri.translate.return_value = '/some/local/repo'
        mock_iglob.return_value = ['some-package.rpm']
        mock_mkdtemp.return_value = 'metadata_dir.XX'
        self.solver._setup_repository_metadata()
        mock_download_from_repository.assert_called_once_with(
            'some-package.rpm', 'metadata_dir.XX/some-package.rpm'
        )
        mock_create_solvables.assert_called_once_with(
            'metadata_dir.XX', 'rpms2solv'
        )
