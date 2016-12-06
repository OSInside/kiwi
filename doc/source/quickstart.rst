Quick Start
===========

.. hint:: **Abstract**

   This document describes how to start with KIWI, an OS appliance builder.
   This description applies for version |version|.

Installation
------------

Packages for the new KIWI version are provided at the `openSUSE
buildservice <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__.

Add the repository with :command:`zypper ar` (see following code) and replace
the distribution placeholder. The best approach is to click on the
desired distribution from the build service link above and there follow
the **Go to download repository** link.

.. code:: bash

    $ sudo zypper ar -f \
        http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>
    $ sudo zypper in python3-kiwi


Compatibility
-------------

The legacy KIWI version can be installed and used together with the next
generation KIWI.

.. note:: Automatic Link Creation for :command:`kiwi` Command

   Note the python3-kiwi package uses the alternatives mechanism to
   setup a symbolic link named :command:`kiwi` to the real executable
   named :command:`kiwi-ng`. If the link target :file:`/usr/bin/kiwi`
   already exists on your system, the alternative setup will skip the
   creation of the link target because it already exists.

From an appliance description perspective, both KIWI versions are fully
compatible. Users can build their appliances with both versions and the
same appliance description. If the appliance description uses features
the next generation KIWI does not provide, the build will fail with an
exception early. If the appliance description uses next generation
features like the selection of the initrd system, it's not possible to
build that with the legacy KIWI, unless the appliance description
properly encapsulates the differences into a profile.

The next generation KIWI also provides the `--compat` option and
the :command:`kiwicompat` tool to be able to use the same commandline
as provided with the legacy KIWI version.

Example Appliance Descriptions
------------------------------

For use with the next generation KIWI there is also a GitHub project
hosting example appliance descriptions. Users who need an example to
start with should checkout the project as follows:

.. code:: bash

    $ git clone https://github.com/SUSE/kiwi-descriptions

Example Image Build on Host System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install python3-kiwi as explained above and build as follows:

.. code:: bash

    $ sudo kiwi-ng --type vmx system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.raw` below :file:`/tmp/myimage`.

Example Image Build in Container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install `dice <https://github.com/SUSE/dice>`__ and build as follows:

.. code:: bash

    $ dice build kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS
    $ dice status kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS

Find the image in a tarball displayed by the :command:`status` command.

In order to run your image build, call :command:`qemu` as follows:

.. code:: bash

    $ qemu -drive \
        file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio

Using KIWI NG from Build Service
--------------------------------

The next generation KIWI is fully integrated with the build service. As
an example you can find the integration testing system in the
buildservice project `Virtualization:Appliances:Images:Testing_<arch>` at:

https://build.opensuse.org

In order to use the next generation KIWI to build an appliance in the
build service it is only required to add the Builder project as
repository to the KIWI XML configuration like in the following example:

.. code:: xml

 <repository type="rpm-md" alias="kiwi-next-generation">
     <source path="obs://Virtualization:Appliances:Builder/Factory"/>
 </repository>

The Builder project configuration in the build service is setup to prefer
the next generation KIWI over the legacy version. Thus adding the
Builder repository inherits this project setup and activates building
with the next generation KIWI.

Using KIWI NG in a Python Project
----------------------------------

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
