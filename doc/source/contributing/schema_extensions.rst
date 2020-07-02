Extending {kiwi} with Custom Operations
========================================

.. note:: **Abstract**

   Users building images with {kiwi} need to implement their
   own infrastructure if the image description does not
   provide a way to embed custom information which is
   outside of the scope of the general schema as it is
   provided by {kiwi} today.

   This document describes how to create an extension plugin
   for the {kiwi} schema to add and validate additional information
   in the {kiwi} image description.

   Such a schema extension can be used in an additional {kiwi}
   task plugin to provide a new subcommand for {kiwi}.
   As of today there is no other plugin interface except for
   providing additional {kiwi} commands implemented.

   Depending on the demand for custom plugins, the interface
   to hook in code into other parts of the {kiwi} processing
   needs to be extended.

   This description applies for version |version|.

The <extension> Section
-----------------------

The main {kiwi} schema supports an extension section which allows
to specify any XML structure and attributes as long as they are
connected to a namespace. According to this any custom XML
structure can be implemented like the following example shows:

.. code:: bash

    <image>
        ...
        <extension xmlns:my_plugin="http://www.my_plugin.com">
            <my_plugin:my_feature>
                <my_plugin:title name="cool stuff"/>
            </my_plugin:my_feature>
        </extension>
    </image>

* Any toplevel namespace must exist only once
* Multiple different toplevel namespaces are allowed,
  e.g my_plugin_a, my_plugin_b

RELAX NG Schema for the Extension
---------------------------------

If an extension section is found, {kiwi} looks up its namespace and asks
the main XML catalog for the schema file to validate the extension data.
The schema file must be a RELAX NG schema in the .rng format. We recommend
to place the schema as :file:`/usr/share/xml/kiwi/my_plugin.rng`

For the above example the RELAX NG Schema in the compressed format
:file:`my_plugin.rnc` would look like this:

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

Extension Schema in XML catalog
-------------------------------

As mentioned above the mapping from the extension namespace to the
correct RELAX NG schema file is handled by a XML catalog file. The
XML catalog for the example use here looks like this:

.. code:: bash

    <?xml version="1.0"?>
    <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
        <system
            systemId="http://www.my_plugin.com"
            uri="file:////usr/share/xml/kiwi/my_plugin.rng"/>
    </catalog>

For resolving the catalog {kiwi} uses the :command:`xmlcatalog` command
and the main XML catalog from the system which is :file:`/etc/xml/catalog`.

.. note::

    It depends on the distribution and its version how the main catalog
    gets informed about the existence of the {kiwi} extension catalog file.
    Please consult the distribution manual about adding XML catalogs.

If the following command provides the information to the correct
RELAX NG schema file you are ready for a first test:

.. code:: bash

    $ xmlcatalog /etc/xml/catalog http://www.my_plugin.com

Using the Extension
-------------------

In order to test your extension place the example extension section
from the beginning of this document into one of your image description's
:file:`config.xml` file

The following example will read the name attribute from the title
section of the my_feature root element and prints it:

.. code:: python

    import logging

    from kiwi.xml_description import XMLDescription

    description = XMLDescription('path/to/kiwi/XML/config.xml')
    description.load()

    my_plugin = description.get_extension_xml_data('my_plugin')

    print(my_plugin.getroot()[0].get('name'))
