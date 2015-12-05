from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import (
    KiwiSchemaImportError,
    KiwiValidationError,
    KiwiDescriptionInvalid,
    KiwiDataStructureError
)
from kiwi.xml_description import XMLDescription


class TestSchema(object):
    def setup(self):
        self.description = XMLDescription('description')

    @raises(KiwiSchemaImportError)
    @patch('lxml.etree.RelaxNG')
    @patch('kiwi.command.Command.run')
    def test_load_schema_import_error(self, mock_xslt, mock_relax):
        mock_relax.side_effect = KiwiSchemaImportError(
            'ImportError'
        )
        self.description.load()

    @raises(KiwiValidationError)
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.command.Command.run')
    def test_load_schema_validation_error(
        self, mock_xslt, mock_parse, mock_relax
    ):
        mock_validate = mock.Mock()
        mock_validate.validate.side_effect = KiwiValidationError(
            'ValidationError'
        )
        mock_relax.return_value = mock_validate
        self.description.load()

    @raises(KiwiDescriptionInvalid)
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.command.Command.run')
    def test_load_schema_description_invalid(
        self, mock_xslt, mock_parse, mock_relax
    ):
        mock_validate = mock.Mock()
        mock_validate.validate = mock.Mock(
            return_value=False
        )
        mock_relax.return_value = mock_validate
        self.description.load()

    @raises(KiwiDataStructureError)
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.xml_parse.parse')
    @patch('kiwi.command.Command.run')
    def test_load_data_structure_error(
        self, mock_xslt, mock_xml_parse, mock_etree_parse, mock_relax
    ):
        mock_validate = mock.Mock()
        mock_validate.validate = mock.Mock(
            return_value=True
        )
        mock_relax.return_value = mock_validate
        mock_xml_parse.side_effect = KiwiDataStructureError(
            'DataStructureError'
        )
        self.description.load()
