Building Build Tests
====================

{kiwi} provides a collection of integration test images for
different architectures and distributions. The test descriptions
covers a number of appliance features that can be build with {kiwi}.
The test descriptions are stored in a directory structure of the
following layout: `build-tests/ARCH/DISTRIBUTION/test-image-NAME`.
To build integration test image(s), the script `build-tests.sh`
exists.

The implementation of `build-tests.sh` calls kiwi's `boxbuild`
command in container mode, which allows calling the script on
actually any host system that allows to run container instances
via `podman`.

.. warning:: **Architectures**

   Cross architecture image building is possible and also supported
   via boxbuild, but the performance impact is big even in containers
   using qemu-binfmt and even bigger in full qemu arch emulation.
   This would slow down building the integration tests a lot and
   therefore `build-tests.sh` requires the host architecture to
   match with the image target architecture.

Prior calling `build-tests.sh` the following requirements must be met:

``Tools``

  Install the packages providing the following tools:

  * tree
  * git
  * xmllint
  * podman
  * pip

``Source Checkout``

  Checkout the kiwi git repo which provides the test descriptions
  as well as the `build-tests.sh` script

  .. code:: bash

     $ git clone https://github.com/OSInside/kiwi.git

``kiwi-boxed-plugin``

  Fetch the kiwi-boxed-plugin from pip. It provides the boxbuild
  command used by build-tests.sh

  .. code:: bash

     $ pip install --upgrade kiwi-boxed-plugin

  .. warning::

     Make sure to be able to execute `kiwi-ng`. In case there was no {kiwi}
     installed on your host you will get notified by the kiwi-boxed-plugin
     installation to update your path to `export PATH:~/.local/bin/kiwi-ng:$PATH`.
     If in doubt about all this just install kiwi from pip too.
     `pip install --upgrade kiwi`

Building a specific integration test can be done as follows:

.. code:: bash

   $ cd kiwi
   $ ./build-tests.sh \
         --test-dir build-tests/x86/tumbleweed/ \
         --test-name test-image-disk

Building all integration tests for a specific arch and distribution
can be done as follows:

.. code:: bash

   $ cd kiwi
   $ ./build-tests.sh \
         --test-dir build-tests/x86/tumbleweed/

.. note::

   Building all integration tests can take some time and depends
   on the number of tests provided as well as on the build power
   of the host system. In general the tests can also run in
   parallel or distributed to multiple hosts
