.. _quick-start:

Quick Start
===========

.. note:: **Abstract**

   This document describes how to start working with {kiwi},
   an OS appliance builder. This description applies for
   version |version|.

Before you start
----------------

1. Install {kiwi} first, either via your distributions' package manager (see
   :ref:`kiwi-installation`) or via:

   .. code:: bash

      $ sudo pip install kiwi

2. Clone the {kiwi} repository containing example appliances (see
   :ref:`example-descriptions`):

   .. code:: bash

      $ git clone https://github.com/OSInside/kiwi

.. note:: 

   In case the following procedure causes any trouble
   please take a look at the :ref:`troubleshooting` chapter
   and/or reach out at: :ref:`contact`

Choose a First Image
--------------------

Find example appliance descriptions in the {kiwi} repository checkout
as follows:

    .. code:: bash

       $ tree -L 3 kiwi/build-tests

Take a look which images are available in the example appliances repository
and select one that matches your desired image as close as possible. Or
just use the one given in the examples below.

Build your First Image
----------------------

Your first image will be a simple system disk image which can run
in any full virtualization system like QEMU. Invoke the following {kiwi}
command in order to build it:

.. code:: bash

    $ sudo kiwi-ng system build \
        --description kiwi/build-tests/{exc_description_disk} \
        --set-repo {exc_repo_leap} \
        --target-dir /tmp/myimage

The resulting image will be placed into the folder :file:`/tmp/myimage`
with the suffix :file:`.raw`.

If you don't wish to create a openSUSE Leap {exc_os_version} image,
substitute the folder following the ``--description`` option with another
folder that contains the image description which you selected.

Run your Image
--------------

Running an image actually means booting the operating system. In order to
do that attach the disk image to a virtual system. In this example we use
QEMU and boot it as follows:

.. code:: bash

    $ sudo qemu -boot c \
        -drive file={exc_image_base_name_disk}.x86_64-{exc_image_version}.raw,format=raw,if=virtio \
        -m 4096 -serial stdio

Tweak and Customize your Image
------------------------------

Now that you have successfully built and started your first image, you can
start tweaking it to match your needs.
