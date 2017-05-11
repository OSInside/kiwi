Using KIWI NG in a Python Project
=================================

.. hint:: **Abstract**

   KIWI is provided as python module under the **kiwi** namespace.
   It is available for the python 2 and 3 versions. The following
   description applies for KIWI version |version|.

KIWI NG can also function as a module for other Python projects.
The following example demonstrates how to read an existing image
description, add a new repository definition and export the
modified description on stdout.

.. code:: python

    import sys
    import logging

    from kiwi.xml_description import XMLDescription
    from kiwi.xml_state import XMLState

    # Import of log handler only needed if default logging
    # setup is not appropriate for the project
    # from kiwi.logger import log

    # By default the logging level is set to DEBUG, which
    # can be changed by the following call
    # log.setLogLevel(logging.INFO)

    # Logging can also be disabled completely
    # log.disabled = True

    description = XMLDescription('path/to/kiwi/XML/config.xml')

    xml_data = description.load()

    xml_state = XMLState(
        xml_data=xml_data, profiles=[], build_type='iso'
    )

    xml_state.add_repository(
        repo_source='http://repo',
        repo_type='rpm-md',
        repo_alias='myrepo',
        repo_prio=99
    )

    xml_data.export(
        outfile=sys.stdout, level=0
    )

All classes are written in a way to care for a single responsibility
in order to allow for re-use on other use cases. Therefore it is possible
to use KIWI NG outside of the main image building scope to manage e.g
the setup of loop devices, filesystems, partitions, etc...
