import logging
from unittest.mock import patch
import unittest.mock as mock
from builtins import bytes
from lxml import etree
from pytest import raises
from collections import namedtuple
from kiwi.utils.temporary import Temporary
from pytest import fixture

from kiwi.xml_description import XMLDescription

from kiwi.exceptions import (
    KiwiCommandError,
    KiwiSchemaImportError,
    KiwiValidationError,
    KiwiDescriptionInvalid,
    KiwiDataStructureError,
    KiwiCommandNotFound,
    KiwiExtensionError
)


class TestSchema:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        test_xml = bytes(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <image schemaversion="7.4" name="bob">
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
            <image schemaversion="7.4" name="bob">
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
            <image schemaversion="7.4" name="bob">
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
            <image schemaversion="7.4" name="bob">
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
        self.description_from_file = XMLDescription(
            description='../data/example_config.xml'
        )
        test_xml_file = Temporary().new_file()
        with open(test_xml_file.name, 'wb') as description:
            description.write(test_xml)
        self.description_from_data = XMLDescription(test_xml_file.name)

        test_xml_extension_file = Temporary().new_file()
        with open(test_xml_extension_file.name, 'wb') as description:
            description.write(test_xml_extension)
        self.extension_description_from_data = XMLDescription(
            test_xml_extension_file.name
        )

        test_xml_extension_not_unique_file = Temporary().new_file()
        with open(test_xml_extension_not_unique_file.name, 'wb') as description:
            description.write(test_xml_extension_not_unique)
        self.extension_multiple_toplevel_description_from_data = XMLDescription(
            test_xml_extension_not_unique_file.name
        )

        test_xml_extension_invalid_file = Temporary().new_file()
        with open(test_xml_extension_invalid_file.name, 'wb') as description:
            description.write(test_xml_extension_invalid)
        self.extension_invalid_description_from_data = XMLDescription(
            test_xml_extension_invalid_file.name
        )

    def setup_method(self, cls):
        self.setup()

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

    @patch('lxml.etree.RelaxNG')
    def test_load_schema_import_error(self, mock_relax):
        mock_relax.side_effect = KiwiSchemaImportError(
            'ImportError'
        )
        with raises(KiwiSchemaImportError):
            self.description_from_file.load()

    @patch('kiwi.xml_description.Defaults.get_schematron_module_name')
    def test_load_schema_from_xml_content_skipping_isoschematron(
        self, mock_get_schematron_module_name
    ):
        mock_get_schematron_module_name.return_value = 'bogus'
        with self._caplog.at_level(logging.WARNING):
            self.description_from_data.load()
            assert 'schematron validation skipped:' in self._caplog.text

    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    def test_load_schema_validation_error_from_file(
        self, mock_parse, mock_relax, mock_schematron
    ):
        mock_validate = mock.Mock()
        mock_validate.validate.side_effect = KiwiValidationError(
            'ValidationError'
        )
        mock_relax.return_value = mock_validate
        mock_schematron.return_value = mock_validate
        with raises(KiwiValidationError):
            self.description_from_file.load()

    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    def test_load_schema_description_from_file_invalid(
        self, mock_command, mock_parse, mock_relax, mock_schematron
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
        mock_command.side_effect = KiwiCommandError('jing output')
        with raises(KiwiDescriptionInvalid):
            self.description_from_file.load()

    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    def test_load_schema_description_from_data_invalid(
        self, mock_command, mock_parse, mock_relax, mock_schematron
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
        with raises(KiwiDescriptionInvalid):
            self.description_from_data.load()

    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.system.setup.Command.run')
    def test_load_schema_description_from_data_invalid_no_jing(
        self, mock_command, mock_parse, mock_relax, mock_schematron
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
        with raises(KiwiDescriptionInvalid):
            self.description_from_data.load()

    @patch('lxml.isoschematron.Schematron')
    @patch('lxml.etree.RelaxNG')
    @patch('lxml.etree.parse')
    @patch('kiwi.xml_parse.parse')
    def test_load_data_structure_error(
        self, mock_xml_parse, mock_etree_parse, mock_relax, mock_schematron
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
        with raises(KiwiDataStructureError):
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

    def test_load_extension_multiple_toplevel_error(self):
        with raises(KiwiExtensionError):
            self.extension_multiple_toplevel_description_from_data.load()

    @patch('kiwi.xml_description.Command.run')
    def test_load_extension_schema_error(self, mock_command):
        mock_command.side_effect = Exception
        with raises(KiwiExtensionError):
            self.extension_description_from_data.load()

    @patch('kiwi.xml_description.Command.run')
    def test_load_extension_validation_error(self, mock_command):
        command_output = mock.Mock()
        command_output.output = 'file://../data/my_plugin.rng'
        mock_command.return_value = command_output
        with raises(KiwiExtensionError):
            self.extension_invalid_description_from_data.load()
