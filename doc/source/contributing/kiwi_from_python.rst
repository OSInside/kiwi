Using {kiwi} in a Python Project
=================================

.. note:: **Abstract**

   {kiwi} is provided as python module under the **kiwi** namespace.
   It is available for the python 3 version. The following
   description applies for {kiwi} version |version|.

{kiwi} can also function as a module for other Python projects.
The following example demonstrates how to read an existing image
description, add a new repository definition and export the
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

All classes are written in a way to care for a single responsibility
in order to allow for re-use on other use cases. Therefore it is possible
to use {kiwi} outside of the main image building scope to manage e.g
the setup of loop devices, filesystems, partitions, etc...

This means {kiwi} provides you a way to describe a system but you are
free to make use of the kiwi description format or not. The following
example shows how to use kiwi to create a simple filesystem image
which contains your host `tmp` directory.

.. code:: python

    import logging

    from kiwi.storage.loop_device import LoopDevice
    from kiwi.filesystem import FileSystem

    loop_provider = LoopDevice(
        filename='my_tmp.ext4', filesize_mbytes=100
    )
    loop_provider.create()

    filesystem = FileSystem.new(
        'ext4', loop_provider, '/tmp/'
    )
    filesystem.create_on_device(
        label='TMP'
    )
    filesystem.sync_data()
