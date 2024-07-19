Extending {kiwi} with Custom Operations
========================================

.. note:: **Abstract**

    Extension plugins in {kiwi} offer a mechanism for adding information outside the standard {kiwi} schema.

   This document describes how to create an extension plugin for the {kiwi}
   schema as well as how to add and validate additional information in the
   {kiwi} image description.

   The described schema extension can be used in an additional {kiwi} task
   plugin to provide a new subcommand for {kiwi}. At the present moment, there
   is no other plugin interface except for providing additional {kiwi} commands.

   Depending on the demand for custom plugins, the interface
   to hook in code into other parts of the {kiwi} processing
   needs to be extended.

   This description applies for version |version|.

The <extension> Section
-----------------------

The main {kiwi} schema supports an extension section that allows you
to specify any XML structure and attributes, as long as they are
attached to a namespace. This means that any custom XML
structure can be implemented similar to the the example below:

.. code:: bash

    <image>
        ...
        <extension xmlns:my_plugin="http://www.my_plugin.com">
            <my_plugin:my_feature>
                <my_plugin:title name="cool stuff"/>
            </my_plugin:my_feature>
        </extension>
    </image>

* Any toplevel namespace must be unique
* Multiple different toplevel namespaces are allowed,
  for example: my_plugin_a, my_plugin_b

RELAX NG Schema for the Extension
---------------------------------

If an extension section is found, {kiwi} looks up its namespace and uses
the main XML catalog for the schema file to validate the extension data.
The schema file must be a RELAX NG schema in the .rng format. We recommend
to save the schema as :file:`/usr/share/xml/kiwi/my_plugin.rng`

For the example above, the RELAX NG Schema in the compressed format
:file:`my_plugin.rnc` looks as follows:

.. there is no rnc syntax highlighting, try cpp
.. code:: cpp

    namespace my_plugin = "http://www.my_plugin.com"

    start =
        k.my_feature

    div {
        k.my_feature.attlist = empty
        k.my_feature =
            element my_plugin:my_feature {
                k.my_feature.attlist &
                k.title
            }
    }

    div {
        k.title.name.attribute =
            attribute name { text }
        k.title.attlist = k.title.name.attribute
        k.title =
            element my_plugin:title {
                k.title.attlist
            }
    }

In order to convert this schema to the .rng format just call:

.. code:: bash

    $ trang -I rnc -O rng my_plugin.rnc /usr/share/xml/kiwi/my_plugin.rng

Extension schema in XML catalog
-------------------------------

As mentioned above, the mapping from the extension namespace to the
correct RELAX NG schema file is handled by a XML catalog file. The
XML catalog for the example is as follows:

.. code:: bash

    <?xml version="1.0"?>
    <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
        <system
            systemId="http://www.my_plugin.com"
            uri="file:////usr/share/xml/kiwi/my_plugin.rng"/>
    </catalog>

For resolving the catalog, {kiwi} uses the :command:`xmlcatalog` command
and the main XML catalog from the system :file:`/etc/xml/catalog`.

.. note::

    How the main catalog is informed about the existence of the {kiwi} extension
    catalog file depends on the distribution and its version. Refer to the
    distribution documentation for information on adding XML catalogs.

If the following command provides the information to the correct
RELAX NG schema file, you are ready for a first test:

.. code:: bash

    $ xmlcatalog /etc/xml/catalog http://www.my_plugin.com

Using the extension
-------------------

In order to test the extension, insert the example extension into one of your
image description's :file:`config.xml` file.

The following example reads the name attribute from the title
section of the my_feature root element and prints it:

.. code:: python

    import logging

    from kiwi.xml_description import XMLDescription

    description = XMLDescription('path/to/kiwi/XML/config.xml')
    description.load()

    my_plugin = description.get_extension_xml_data('my_plugin')

    print(my_plugin.getroot()[0].get('name'))
