Using {kiwi} in a Python Project
=================================

.. note:: **Abstract**

   {kiwi} is provided as a Python module under the **kiwi** namespace.
   It is available for the Python 3 version. The following
   description applies for {kiwi} version |version|.

{kiwi} can also function as a module for other Python projects.
The following example demonstrates how to read an existing image
description, add a new repository definition, and export the
modified description on stdout.

.. code:: python

    import sys
    import logging

    from kiwi.xml_description import XMLDescription
    from kiwi.xml_state import XMLState

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

Each class in the example is responsible for a single tasks, so they can be
reused in other user cases. Therefore it is possible to use {kiwi} beyond the
main image building scope, for example to manage setup of loop devices,
filesystems, partitions, etc.

This means {kiwi} offers a way to describe a system, but you can choose whether
you want to use the {kiwi} description format or not. The following example
shows how to use {kiwi} to create a simple filesystem image which contains your
host `tmp` directory.

.. code:: python

    import logging

    from kiwi.storage.loop_device import LoopDevice
    from kiwi.filesystem import FileSystem

    with LoopDevice(
        filename='my_tmp.ext4', filesize_mbytes=100
    ) as loop_provider:
        loop_provider.create()

        filesystem = FileSystem.new(
            'ext4', loop_provider, '/tmp/'
        )
        filesystem.create_on_device(
            label='TMP'
        )
        filesystem.sync_data()
