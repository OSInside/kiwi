from mock import patch

import mock

from lxml import etree

from kiwi.solver.repository.suse import SolverRepositorySUSE
from kiwi.solver.repository.base import SolverRepositoryBase


class TestSolverRepositorySUSE(object):
    def setup(self):
        self.xml_data = etree.parse('../data/repomd.xml')
        self.uri = mock.Mock()
        self.solver = SolverRepositorySUSE(self.uri)

    @patch.object(SolverRepositoryBase, 'download_from_repository')
    @patch.object(SolverRepositoryBase, '_create_solvables')
    @patch.object(SolverRepositoryBase, '_create_temporary_metadata_dir')
    @patch.object(SolverRepositoryBase, '_get_repomd_xml')
    def test__setup_repository_metadata_online(
        self, mock_xml, mock_mkdtemp, mock_create_solvables,
        mock_download_from_repository
    ):
        mock_mkdtemp.return_value = 'metadata_dir.XX'
        mock_xml.return_value = self.xml_data
        self.solver._setup_repository_metadata()
        mock_download_from_repository.assert_called_once_with(
            'suse/repodata/55f95a93-primary.xml.gz',
            'metadata_dir.XX/55f95a93-primary.xml.gz'
        )
        mock_create_solvables.assert_called_once_with(
            'metadata_dir.XX', 'rpmmd2solv'
        )

    @patch.object(SolverRepositoryBase, 'download_from_repository')
    @patch.object(SolverRepositoryBase, '_create_solvables')
    @patch.object(SolverRepositoryBase, '_get_repomd_xml')
    @patch.object(SolverRepositoryBase, '_create_temporary_metadata_dir')
    def test__setup_repository_metadata_media(
        self, mock_mkdtemp, mock_xml, mock_create_solvables,
        mock_download_from_repository
    ):
        mock_xml.side_effect = Exception
        mock_mkdtemp.return_value = 'metadata_dir.XX'
        self.solver._setup_repository_metadata()
        mock_download_from_repository.assert_called_once_with(
            'suse/setup/descr/packages.gz', 'metadata_dir.XX/packages.gz'
        )
        mock_create_solvables.assert_called_once_with(
            'metadata_dir.XX', 'susetags2solv'
        )
