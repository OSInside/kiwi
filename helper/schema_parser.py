#!/usr/bin/env python
"""
Usage: schema_parser.py SCHEMA [--output=ARG]

Arguments:
    SCHEMA  Kiwi RelaxNG schema file to parse

Options:
     --output This is output file (stdout used if not present)
"""

import docopt
from lxml import etree
from collections import namedtuple
import os.path
import logging
import sys

logging.basicConfig(level=logging.WARNING)


class SchemaNode(object):

    Child = namedtuple('Child', ['node', 'properties'])

    @classmethod
    def is_type(self, node):
        pass

    def __init__(self, node, namespaces):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.node = node
        self.namespaces = namespaces
        ref = node.xpath(
            '(./parent::rng:define[@name])[1]',
            namespaces=namespaces
        )
        if len(ref):
            self.reference = ref[0].attrib['name']
        else:
            self.reference = None
        self.documentation = None
        self.paths = []

        element_tree = node.getroottree()
        path = element_tree.getelementpath(node)
        self.x_path = path.replace('{%s}' % namespaces['rng'], 'rng:')
        self.properties = ['optional', 'oneOrMore', 'zeroOrMore']

    def get_documentation(self):
        for candidate in self.node:
            if candidate.tag.endswith('documentation'):
                self.documentation = candidate.text.replace('\n', ' ')
        if self.documentation is None:
            self.documentation = ''
            self.logger.warning(
                'Node %s has no documentation in schema', self.name
            )
        return self.documentation

    def query(self, query, ret_type=None):
        nodes = []
        for node in self.node.xpath(query, namespaces=self.namespaces):
            if ret_type is None:
                nodes.append(SchemaNode(node, self.namespaces))
            else:
                nodes.append(ret_type(node, self.namespaces))
        return nodes

    def get_children_by_type(self, ret_type, stop_types=None):
        if stop_types is None:
            stop_types = []

        # Gets direct children of this node in its tree
        children = self.children_in_tree(ret_type, stop_types)

        # Follow references that are defined somewhere else in tree
        s_types = [ret_type] + stop_types
        for reference in self.children_in_tree(Reference, s_types):
            if not reference.node.name.endswith('any'):
                children += reference.node.resolve_reference(
                    ret_type, stop_types, reference.properties
                )
        return children

    def children_in_tree(self, ret_type, stop_types, properties=None):
        if properties is None:
            properties = []
        children = []
        for child in self.node:
            if self._is_in_types(child, stop_types):
                continue
            if ret_type.is_type(child):
                children.append(SchemaNode.Child(
                    node=ret_type(child, self.namespaces),
                    properties=self._get_properties(child, properties)
                ))
            else:
                children += SchemaNode(child, self.namespaces).children_in_tree(
                    ret_type, stop_types, self._get_properties(child, properties)
                )
        return children

    def _get_properties(self, node, properties):
        props = []
        for prop in self.properties:
            if node.tag.endswith(prop):
                props = [prop]
                break
        return props + properties

    def _is_in_types(self, node, types):
        for t in types:
            if t.is_type(node):
                return True
        return False


class Reference(SchemaNode):

    @classmethod
    def is_type(self, node):
        if 'name' in node.attrib and node.tag.endswith('ref'):
            return True
        return False

    def __init__(self, node, namespaces):
        super(Reference, self).__init__(node, namespaces)
        if not self.is_type(node):
            raise Exception('The given node is not a reference')
        self.name = self.node.attrib['name']

    def resolve_reference(self, ret_type, stop_types, properties):
        define = self._find_define()
        if define is None:
            return []

        # Gets direct children of this node in its tree
        nodes = define.children_in_tree(ret_type, stop_types, properties)

        # Follow references that are defined somewhere else in tree
        s_types = stop_types + [ret_type]
        for reference in define.children_in_tree(
            Reference, s_types, properties
        ):
            nodes += reference.node.resolve_reference(
                ret_type, stop_types, reference.properties
            )
        return nodes

    def _find_define(self):
        node = self.query(
            '//rng:define[@name=\'%s\']' % self.name
        )
        if len(node):
            return node[0]


class Attribute(SchemaNode):

    @classmethod
    def is_type(self, node):
        if 'name' in node.attrib and node.tag.endswith('attribute'):
            return True
        return False

    def __init__(self, node, namespaces):
        super(Attribute, self).__init__(node, namespaces)
        if not self.is_type(node):
            raise Exception('The given node is not an attribute')
        self.documentation = None
        self.name = self.node.attrib['name']


class Element(SchemaNode):

    Child = namedtuple('Child', ['x_path', 'properties'])

    @classmethod
    def is_type(self, node):
        if 'name' in node.attrib and node.tag.endswith('element'):
            return True
        return False

    def __init__(self, node, namespaces):
        super(Element, self).__init__(node, namespaces)
        if not self.is_type(node):
            raise Exception('The given node is not an element')
        self.children = None
        self.name = self.node.attrib['name']
        self.attributes = self.get_children_by_type(Attribute, [Element])

    def get_parent_paths(self):
        parents = []
        for path in filter(lambda x: '.' in x, self.paths):
            parent = path.rsplit('.' + self.get_name(), 1)[0]
            if len(parent):
                parents.append(parent)
        return parents

    def get_children(self):
        if self.children is None:
            self.find_children()
        return self.children

    def find_children(self):
        self.children = []
        elements = []
        for child in self.get_children_by_type(Element, [Attribute]):
            self.children.append(Element.Child(
                x_path=child.node.x_path,
                properties=child.properties
            ))
            elements.append(child.node)

        return elements


class RNGSchemaParser(object):

    def __init__(self, schema):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.schema_tree = etree.parse(schema)
        etree.strip_tags(self.schema_tree, etree.Comment)
        self.nspaces = self.schema_tree.getroot().nsmap
        self.nspaces.pop(None)

        if 'rng' not in self.nspaces:
            raise Exception('\'rng:\' namespace must be defined in namespaces map')

        self.root_nodes = []
        for start in self.schema_tree.xpath('//rng:start', namespaces=self.nspaces):
            self.root_nodes += SchemaNode(start, self.nspaces).get_children_by_type(
                Element, [Attribute]
            )

        if not self.root_nodes:
            raise Exception('Not valid RelaxNG start tag')

        self.elements = dict()
        for root_node in self.root_nodes:
            self._find_elements(root_node.node, None)

    def x_path_query(self, query):
        return self.schema_tree.xpath(query, namespaces=self.nspaces)

    def write_element_doc(self, element, current_path, output):
        if current_path is None:
            current_path = []
        element_path = '.'.join(current_path + [element.name])
        level = element_path.count('.')
        titles = '-_.,:;#~<>^*'
        doc = '.. _k.%s:\n\n' % element_path
        doc += '%s\n' % element.name
        doc += titles[level] * len(element.name) + '\n\n'

        if len(element.get_documentation()):
            doc += '%s\n\n' % element.get_documentation()

        parents = []
        for path in [x for x in element.paths if len(x) > 1]:
            parents.append(':ref:`k.%s`' % '.'.join(path[:-1]))
        if len(parents):
            doc += 'Parents:\n'
            doc += '   These elements contain ``%s``: ' % element.name
            doc += ', '.join(parents)
            doc += '\n\n'

        children = []
        for child in element.get_children():
            children.append(':ref:`%s <k.%s>` %s' % (
                self.elements[child.x_path].name,
                '.'.join([element_path, self.elements[child.x_path].name]),
                self._properties_to_doc(child.properties)
            ))
        if len(children):
            doc += 'Children:\n'
            doc += '   The following elements occur in ``%s``: ' % element.name
            doc += ', '.join(children)
            doc += '\n\n'

        if len(element.attributes):
            doc += 'List of attributes for ``%s``:\n\n' % element.name
        for attribute in element.attributes:
            doc += '* ``%s`` %s: %s\n' % (
                attribute.node.name,
                self._properties_to_doc(attribute.properties),
                attribute.node.get_documentation()
            )

        doc += '\n'

        if output:
            with open(output, 'a') as f:
                f.write(doc)
        else:
            sys.stdout.write(doc)

        for child in element.get_children():
            self.write_element_doc(
                self.elements[child.x_path],
                current_path + [element.name], output
            )

    def legend(self):
        doc = '.. hint:: **Element quantifiers**\n\n'\
            '    * **Optional** elements are qualified with _`[?]`\n'\
            '    * Elements that occur **one or more** times are qualified with _`[+]`\n'\
            '    * Elements that occur **zero or more** times are qualified with _`[*]`\n'\
            '    * Required elements are not qualified\n\n'
        return doc

    def _properties_to_doc(self, properties):
        if not properties:
            return ''
        if properties[0] == 'optional':
            return '`[?]`_'
        elif properties[0] == 'oneOrMore':
            return '`[+]`_'
        elif properties[0] == 'zeroOrMore':
            return '`[*]`_'
        return ''

    def _find_elements(self, element, path):
        if path is None:
            path = []
        if element.x_path not in self.elements:
            self.elements[element.x_path] = element
            for child in element.find_children():
                self._find_elements(child, path + [element.name])

        self.elements[element.x_path].paths.append(path + [element.name])


if __name__ == "__main__":
    try:
        logger = logging.getLogger(__name__)
        arguments = docopt.docopt(__doc__)
        ofile = arguments['--output']

        if os.path.splitext(arguments['SCHEMA'])[-1] == '.rnc':
            raise OSError("Need RNG instead of RNC")

        if ofile and os.path.isfile(ofile):
            logger.warning('Output file %s will be overwritten', ofile)

        if os.path.isfile(arguments['SCHEMA']):
            parser = RNGSchemaParser(arguments['SCHEMA'])
            value = parser.x_path_query(
                '(//rng:attribute[@name=\'schemaversion\']/rng:value)[1]'
            )
            if value:
                version = value[0].text
            else:
                raise Exception('Schema version not found!')
            title_label = '.. _schema-docs:\n\n'
            title = 'Schema Documentation %s\n' % version
            title += '=' * len(title) + '\n\n'
            title = title_label + title
            if ofile:
                with open(ofile, 'w') as f:
                    f.write(title)
                    f.write(parser.legend())
            else:
                sys.stdout.write(title)
            for element in parser.root_nodes:
                parser.write_element_doc(
                    parser.elements[element.node.x_path], None, ofile
                )
        else:
            raise Exception('File not found: %s' % arguments['SCHEMA'])
    except Exception as e:
        logger.error('Schema parser failed', exc_info=True)
        exit(2)
