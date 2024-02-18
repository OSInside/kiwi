from unittest.mock import patch, call

import unittest.mock as mock

from lxml import etree

from kiwi.solver.repository.rpm_md import SolverRepositoryRpmMd
from kiwi.solver.repository.base import SolverRepositoryBase


class TestSolverRepositoryRpmMd:
    def setup(self):
        self.xml_data = etree.parse('../data/repomd.xml')
        self.uri = mock.Mock()
        self.uri.uri = 'http://example.org/some/path'
        self.solver = SolverRepositoryRpmMd(self.uri)

    def setup_method(self, cls):
        self.setup()

    @patch.object(SolverRepositoryBase, 'download_from_repository')
    @patch.object(SolverRepositoryBase, '_create_solvables')
    @patch.object(SolverRepositoryBase, '_create_temporary_metadata_dir')
    @patch.object(SolverRepositoryBase, '_get_repomd_xml')
    def test__setup_repository_metadata(
        self, mock_xml, mock_mkdtemp, mock_create_solvables,
        mock_download_from_repository
    ):
        mock_mkdtemp.return_value = 'metadata_dir.XX'
        mock_xml.return_value = self.xml_data
        self.solver._setup_repository_metadata()

        assert mock_download_from_repository.call_args_list == [
            call(
                'repodata/55f95a93-primary.xml.gz',
                'metadata_dir.XX/55f95a93-primary.xml.gz'
            ),
            call(
                'repodata/0815-other.xml.gz',
                'metadata_dir.XX/0815-other.xml.gz'
            )
        ]
        assert mock_create_solvables.call_args_list == [
            call('metadata_dir.XX', 'rpmmd2solv'),
            call('metadata_dir.XX', 'comps2solv')
        ]

    @patch.object(SolverRepositoryBase, '_get_repomd_xml')
    def test_timestamp(self, mock_xml):
        mock_xml.return_value = self.xml_data
        assert self.solver.timestamp() == '1478352191'
