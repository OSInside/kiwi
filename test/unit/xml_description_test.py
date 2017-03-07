from mock import patch
import mock
from builtins import bytes
from lxml import etree

from .test_helper import raises
from collections import namedtuple

from kiwi.exceptions import (
    KiwiSchemaImportError,
    KiwiValidationError,
    KiwiDescriptionInvalid,
    KiwiDataStructureError,
    KiwiDescriptionConflict,
    KiwiCommandNotFound,
    KiwiExtensionError
)
from kiwi.xml_description import XMLDescription


class TestSchema(object):
    def setup(self):
        test_xml = bytes(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <image schemaversion="1.4" name="bob">
                <description type="system">
                    <author>John Doe</author>
                    <contact>john@example.com</contact>
                    <specification>
                        say hello
                    </specification>
                </description>
                <preferences>
                    <packagemanager>zypper</packagemanager>
                    <version>1.1.1</version>
                    <type image="ext3"/>
                </preferences>
                <repository type="rpm-md">
                    <source path="repo"/>
                </repository>
            </image>"""
        )
        test_xml_extension = bytes(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <image schemaversion="1.4" name="bob">
                <description type="system">
                    <author>John Doe</author>
                    <contact>john@example.com</contact>
                    <specification>
                        say hello
                    </specification>
                </description>
                <preferences>
                    <packagemanager>zypper</packagemanager>
                    <version>1.1.1</version>
                    <type image="ext3"/>
                </preferences>
                <repository type="rpm-md">
                    <source path="repo"/>
                </repository>
                <extension xmlns:my_plugin="http://www.my_plugin.com">
                    <my_plugin:my_feature>
                        <my_plugin:title name="cool stuff"/>
                    </my_plugin:my_feature>
                </extension>
            </image>"""
        )
        test_xml_extension_not_unique = bytes(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <image schemaversion="1.4" name="bob">
                <description type="system">
                    <author>John Doe</author>
                    <contact>john@example.com</contact>
                    <specification>
                        say hello
                    </specification>
                </description>
                <preferences>
                    <packagemanager>zypper</packagemanager>
                    <version>1.1.1</version>
                    <type image="ext3"/>
                </preferences>
                <repository type="rpm-md">
                    <source path="repo"/>
                </repository>
                <extension xmlns:my_plugin="http://www.my_plugin.com">
                    <my_plugin:toplevel_a/>
                    <my_plugin:toplevel_b/>
                </extension>
            </image>"""
        )
        test_xml_extension_invalid = bytes(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <image schemaversion="1.4" name="bob">
                <description type="system">
                    <author>John Doe</author>
                    <contact>john@example.com</contact>
                    <specification>
                        say hello
                    </specification>
                </description>
                <preferences>
                    <packagemanager>zypper</packagemanager>
                    <version>1.1.1</version>
                    <type image="ext3"/>
                </preferences>
                <repository type="rpm-md">
                    <source path="repo"/>
                </repository>
                <extension xmlns:my_plugin="http://www.my_plugin.com">
                    <my_plugin:my_feature>
                        <my_plugin:title name="cool stuff" unknown_attr="foo"/>
                    </my_plugin:my_feature>
                </extension>
            </image>"""
        )
        self.description_from_file = XMLDescription(description='description')
        self.description_from_data = XMLDescription(xml_content=test_xml)
        self.extension_description_from_data = XMLDescription(
            xml_content=test_xml_extension
        )
        self.extension_multiple_toplevel_description_from_data = XMLDescription(
            xml_content=test_xml_extension_not_unique
        )
        self.extension_invalid_description_from_data = XMLDescription(
            xml_content=test_xml_extension_invalid
        )

    @raises(KiwiDescriptionConflict)
    def test_constructor_conflict(self):
        XMLDescription(description='description', xml_content='content')

    def test_load_schema_from_xml_content(self):
        schema = etree.parse('../../kiwi/schema/kiwi.rng')
        lookup = '{http://relaxng.org/ns/structure/1.0}attribute'
        for attribute in schema.iter(lookup):
            if attribute.get('name') == 'schemaversion':
                schemaversion = attribute.find(
                    '{http://relaxng.org/ns/structure/1.0}value'
                ).text
        parsed = self.description_from_data.load()
        assert parsed.get_schemaversion() == schemaversion

    @raises(KiwiSchemaImportError)
    @patch('lxml.etree.RelaxNG')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_schema_import_error(self, mock_xslt, mock_relax):
        mock_relax.side_effect = KiwiSchemaImportError(
            'ImportError'
        )
        self.description_from_file.load()

    @raises(KiwiValidationError)
    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_schema_validation_error_from_file(
        self, mock_xslt, mock_parse, mock_relax, mock_schematron
    ):
        mock_validate = mock.Mock()
        mock_validate.validate.side_effect = KiwiValidationError(
            'ValidationError'
        )
        mock_relax.return_value = mock_validate
        mock_schematron.return_value = mock_validate
        self.description_from_file.load()

    @raises(KiwiDescriptionInvalid)
    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_schema_description_from_file_invalid(
        self, mock_xslt, mock_command, mock_parse, mock_relax, mock_schematron
    ):
        mock_rng_validate = mock.Mock()
        mock_rng_validate.validate = mock.Mock(
            return_value=False
        )

        mock_sch_validate = mock.Mock()
        mock_sch_validate.validate = mock.Mock(
            return_value=False
        )

        validation_report = namedtuple(
            'report', ['text']
        )
        name_spaces = namedtuple(
            'nspaces', ['nsmap']
        )
        mock_validation_report = mock.Mock()
        mock_validation_report.getroot = mock.Mock(
            return_value=name_spaces(nsmap="")
        )
        mock_validation_report.xpath = mock.Mock(
            return_value=[
                validation_report(text='wrong attribute 1'),
                validation_report(text='wrong attribute 2')
            ]
        )
        mock_sch_validate.validation_report = mock_validation_report

        mock_relax.return_value = mock_rng_validate
        mock_schematron.return_value = mock_sch_validate
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_command.return_value = command_run(
            output='jing output\n',
            error='',
            returncode=1
        )
        self.description_from_file.load()

    @raises(KiwiDescriptionInvalid)
    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_schema_description_from_data_invalid(
        self, mock_xslt, mock_command, mock_parse, mock_relax, mock_schematron
    ):
        mock_rng_validate = mock.Mock()
        mock_rng_validate.validate = mock.Mock(
            return_value=False
        )

        mock_sch_validate = mock.Mock()
        mock_sch_validate.validate = mock.Mock(
            return_value=False
        )

        validation_report = namedtuple(
            'report', ['text']
        )
        name_spaces = namedtuple(
            'nspaces', ['nsmap']
        )
        mock_validation_report = mock.Mock()
        mock_validation_report.getroot = mock.Mock(
            return_value=name_spaces(nsmap="")
        )
        mock_validation_report.xpath = mock.Mock(
            return_value=[
                validation_report(text='wrong attribute 1'),
                validation_report(text='wrong attribute 2')
            ]
        )
        mock_sch_validate.validation_report = mock_validation_report

        mock_relax.return_value = mock_rng_validate
        mock_schematron.return_value = mock_sch_validate
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_command.return_value = command_run(
            output='jing output\n',
            error='',
            returncode=1
        )
        self.description_from_data.load()

    @raises(KiwiDescriptionInvalid)
    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_schema_description_from_data_invalid_no_jing(
        self, mock_xslt, mock_command, mock_parse, mock_relax, mock_schematron
    ):
        mock_rng_validate = mock.Mock()
        mock_rng_validate.validate = mock.Mock(
            return_value=False
        )

        mock_sch_validate = mock.Mock()
        mock_sch_validate.validate = mock.Mock(
            return_value=True
        )

        mock_relax.return_value = mock_rng_validate
        mock_schematron.return_value = mock_sch_validate
        mock_command.side_effect = KiwiCommandNotFound('No jing command')
        self.description_from_data.load()

    @raises(KiwiDataStructureError)
    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.xml_parse.parse')
    @patch.object(XMLDescription, '_xsltproc')
    def test_load_data_structure_error(
        self, mock_xsltproc, mock_xml_parse,
        mock_etree_parse, mock_relax, mock_schematron
    ):
        mock_rng_validate = mock.Mock()
        mock_rng_validate.validate = mock.Mock(
            return_value=True
        )
        mock_sch_validate = mock.Mock()
        mock_sch_validate.validate = mock.Mock(
            return_value=True
        )
        mock_relax.return_value = mock_rng_validate
        mock_schematron.return_value = mock_sch_validate
        mock_xml_parse.side_effect = KiwiDataStructureError(
            'DataStructureError'
        )
        self.description_from_file.load()

    @patch('kiwi.xml_description.Command.run')
    def test_load_extension(self, mock_command):
        command_output = mock.Mock()
        command_output.output = 'file://../data/my_plugin.rng'
        mock_command.return_value = command_output
        self.extension_description_from_data.load()
        mock_command.assert_called_once_with(
            ['xmlcatalog', '/etc/xml/catalog', 'http://www.my_plugin.com']
        )
        xml_data = self.extension_description_from_data.get_extension_xml_data(
            'my_plugin'
        )
        assert xml_data.getroot()[0].get('name') == 'cool stuff'

    @raises(KiwiExtensionError)
    def test_load_extension_multiple_toplevel_error(self):
        self.extension_multiple_toplevel_description_from_data.load()

    @raises(KiwiExtensionError)
    @patch('kiwi.xml_description.Command.run')
    def test_load_extension_schema_error(self, mock_command):
        mock_command.side_effect = Exception
        self.extension_description_from_data.load()

    @patch('kiwi.xml_description.Command.run')
    @raises(KiwiExtensionError)
    def test_load_extension_validation_error(self, mock_command):
        command_output = mock.Mock()
        command_output.output = 'file://../data/my_plugin.rng'
        mock_command.return_value = command_output
        self.extension_invalid_description_from_data.load()
