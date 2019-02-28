Building in the Open Build Service
==================================

.. hint:: **Abstract**

   This document gives a brief overview how to build images with
   KIWI in version |version| inside of the Open Build Service.
   A tutorial on the Open Buildservice itself can be found here:
   https://en.opensuse.org/openSUSE:Build_Service_Tutorial


The next generation KIWI is fully integrated with the Open Build Service.
In order to start it's best to checkout one of the integration test
image build projects from the base Testing project
`Virtualization:Appliances:Images:Testing_$ARCH` at:

https://build.opensuse.org

For example the test images for x86 can be found `here
<https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86>`__.


Advantages of using the Open Build Service (OBS)
------------------------------------------------

The Open Build Service offers multiple advantages over running KIWI
locally:

* OBS will host the latest successful build for you without having to setup
  a server yourself.

* As KIWI is fully integrated into OBS, OBS will automatically rebuild your
  images if one of the included packages or one of its dependencies or KIWI
  itself get updated.

* The builds will no longer have to be executed on your own machine, but
  will run on OBS, thereby saving you resources. Nevertheless, if a build
  fails, you get a notification via email (if enabled in your user's
  preferences).


Differences Between Building Locally and on OBS
-----------------------------------------------

Note, there is a number of differences when building images with KIWI using
the Open Build Service. Your image that build locally just fine, might not
build without modifications.

The notable differences to running KIWI locally include:

* OBS will pick the KIWI package from the available repositories that you
  specified in :file:`config.xml`/:file:`config.kiwi`. This means, that you
  will be very likely building with a different KIWI version in the Open
  Build Service.
  This is especially relevant when building images for older versions like
  SUSE Linux Enterprise. Therefore, include the custom appliances
  repository as described in the following section:
  :ref:`obs-recommended-settings`.

* When KIWI runs on OBS, OBS will extract the list of packages from
  :file:`config.xml` and use it to create a build root. In contrast to a
  local build (where your distributions package manager will resolve the
  dependencies and install the packages), OBS will **not** build your image
  if there are multiple packages that could be chosen to satisfy the
  dependencies of your packages. This manifests as errors like this:

  .. code:: bash

     unresolvable: have choice for SOMEPACKAGE: SOMEPAKAGE_1 SOMEPACKAGE_2

  This can be solved by explicitly specifying one of the two packages in
  the project configuration via the following setting:

  .. code:: bash

     Prefer: SOMEPACKAGE_1

  Place the above line into the project configuration, which can be
  accessed either via the web interface (click on the tab ``Project
  Config`` on your project's main page) or via ``osc meta -e prjconf``.

* OBS can only build a single image type, for example it cannot build a VMX
  disk and a live ISO from one :file:`config.xml`. A configuration file
  that contains multiple image types will therefore not work in the Open
  Build Service.
  Split the configuration file into two (or more) :file:`.kiwi` files and
  provide them as separate packages inside your project.

* OBS projects do not support subfolders, thus you must provide the overlay
  files packed as an archive called :file:`root.tar.gz`.

* OBS projects do not support the use of the ``namedCollection`` section.

  A specification of ``<namedCollection name="collection_name"/>`` is used
  to pass the information to install a collection of packages to the used
  package manager. The package manager can resolve that information only if
  the repository metadata contains the information about that collection
  and its packages. If the Open Build Service builds the image, it resolves
  the given package list using its own SAT based solver. That result is
  used by the Open Build Service to create temporary repositories of the
  same names as they got configured in the KIWI XML description. Those
  repositories don't contain the metadata to resolve collections.

  Even though KIWI uses the package manager to register the repositories,
  one should keep in mind that the repositories the Open Build Service
  creates, contain just a subset of the data that the real repositories
  provide.

  Furthermore, the Open Build Service applies a different dependency
  resolution mechanism to create the repositories before KIWI is
  called. The differences compared to the dependency resolution of the
  selected package manager when KIWI calls it are:

  * In the Open Build Service the order of repositories in the XML description
    matters
  * In the Open Build Service package dependencies from file provides are not
    resolved

  Because of this reason an image build that resolves well outside of the
  Open Build Service might no longer do so on OBS.


.. _obs-recommended-settings:

Recommendations
---------------

Working with OBS
^^^^^^^^^^^^^^^^

Although OBS is an online service, it is not necessary to test every change
by uploading it. OBS will use the same process as ``osc build`` does, so if
your image builds locally via ``osc build`` it should also build online on
OBS.


Repository Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

We strongly encourage everyone to include the following repository in the
KIWI :file:`config.xml` configuration file:

.. code:: xml

  <repository type="rpm-md" alias="kiwi-next-generation">
      <source path="obs://Virtualization:Appliances:Builder/$DISTRO"/>
  </repository>

Replace ``$DISTRO`` with the appropriate name for the distribution that you
are currently building. This repository contains the latest stable build of
KIWI (which is in fact the same repository that was recommended to be added
in :ref:`kiwi-installation`) and will ensure that OBS will use the most up
to date version of KIWI when building your appliance, thereby reducing the
possible differences to a local build.


Project Configuration
^^^^^^^^^^^^^^^^^^^^^

When setting up the project enable the ``images`` repository: it can be
found at the bottom of the selection screen that appears when clicking
``Add from a Distribution`` in the ``Repositories`` tab. Or specify it
manually in the project configuration (it can be accessed via ``osc meta -e
prj``):

.. code:: xml

  <repository name="images">
    <arch>x86_64</arch>
  </repository>


Due to the nature of OBS' dependency resolution mechanism a lot of
``Prefer:``, ``Substitute:``, ``Preinstall:`` and ``Support:`` directives
are required for an image to build successfully without having choices or
conflicts for packages. We therefore recommend to initially copy the
current project configuration of the testing project
`Virtualization:Appliances:Images:Testing_$ARCH` into your own project as a
start and tweak it from there instead of starting from scratch.

The Open Build Service will by default create the same output file as KIWI
when run locally, but with a custom filename ending (that is unfortunately
unpredictable). This has the consequence that the download URL of your
image will change with every rebuild (and thus break automated
scripts). This behavior can be deactivated by adding the following line
into the project's configuration:

.. code:: bash

   Repotype: staticlinks

Furthermore, if you are building images of openSUSE Leap 15 the above
setting is not sufficient. The following additional line is required:

.. code:: bash

   Release: <CI_CNT>.<B_CNT>
