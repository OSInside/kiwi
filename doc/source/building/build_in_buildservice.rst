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

* OBS will pick the KIWI package from the repositories configured in your
  project, which will most likely not be the same version that you are
  running locally.
  This is especially relevant when building images for older versions like
  SUSE Linux Enterprise. Therefore, include the custom appliances
  repository as described in the following section:
  :ref:`obs-recommended-settings`.

* When KIWI runs on OBS, OBS will extract the list of packages from
  :file:`config.xml` and use it to create a build root. In contrast to a
  local build (where your distributions package manager will resolve the
  dependencies and install the packages), OBS will **not** build your image
  if there are multiple packages that could be chosen to satisfy the
  dependencies of your packages [#f1]_. This shows errors like this:

  .. code:: bash

     unresolvable: have choice for SOMEPACKAGE: SOMEPAKAGE_1 SOMEPACKAGE_2

  This can be solved by explicitly specifying one of the two packages in
  the project configuration via the following setting:

  .. code:: bash

     Prefer: SOMEPACKAGE_1

  Place the above line into the project configuration, which can be
  accessed either via the web interface (click on the tab ``Project
  Config`` on your project's main page) or via ``osc meta -e prjconf``.

  .. warning:: We strongly encourage you to remove your repositories from
     :file:`config.xml` and move them to the repository configuration in
     your project's settings. This usually prevents the issue of having the
     choice for multiple package version and results in a much smoother
     experience when using OBS.

* OBS will by default only build a single image type. If your appliance
  contains the multiple build types or uses profiles, use the `multibuild
  <https://openbuildservice.org/help/manuals/obs-reference-guide/cha.obs.multibuild.html>`_ feature.

* Subfolders in OBS projects are ignored by default by :file:`osc` and must
  be explicitly added via `osc add $FOLDER` [#f2]_. Bear that in mind when
  adding the overlay files inside the :file:`root/` directory to your
  project.


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

When setting up the project, enable the `images` repository: the `images`
repository's checkbox can be found at the bottom of the selection screen
that appears when clicking `Add from a Distribution` in the `Repositories`
tab. Or specify it manually in the project configuration (it can be
accessed via ``osc meta -e prj``):

.. code-block:: xml

  <repository name="images">
    <arch>x86_64</arch>
  </repository>

Furthermore, OBS requires additional repositories from which it obtains
your dependent packages. These repositories can be provided in two ways:

#. Add the repositories to the project configuration on OBS and omit them
   from :file:`config.xml`. Provide only the following repository inside
   the image description:

   .. code-block:: xml

      <repository type="rpm-md">
        <source path="obsrepositories:/"/>
      </repository>

   This instructs OBS to inject the repositories from your project into
   your appliance.

   Additional repositories can be added by invoking ``osc meta -e prj`` and
   adding a line of the following form as a child of ``<repository
   name="images">``:

   .. code-block:: xml

      <path project="$OBS_PROJECT" repository="$REPOSITORY_NAME"/>

   Don't forget to add the repository from the
   `Virtualization:Appliances:Builder` project, providing the latest stable
   version of KIWI (which you are very likely using for your local builds).

   The following example repository configuration [#f3]_ adds the
   repositories from the `Virtualization:Appliances:Builder` project and
   those from the latest snapshot of openSUSE Tumbleweed:

   .. code-block:: xml

      <project name="Virtualization:Appliances:Images:openSUSE-Tumbleweed">
        <title>JeOS for Tumbleweed </title>
        <description>Host JeOS images for Tumbleweed</description>
        <repository name="images">
          <path project="Virtualization:Appliances:Builder" repository="Factory"/>
          <path project="openSUSE:Factory" repository="snapshot"/>
          <arch>x86_64</arch>
        </repository>
      </project>


#. Keep the repositories in your :file:`config.xml` configuration
   file. If you have installed KIWI as described in
   :ref:`kiwi-installation` then you should add the following repository to
   your :file:`config.xml`, so that OBS will pick the latest stable KIWI
   version too:

   .. code-block:: xml

      <repository type="rpm-md" alias="kiwi-next-generation">
        <source path="obs://Virtualization:Appliances:Builder/$DISTRO"/>
      </repository>

   Replace ``$DISTRO`` with the appropriate name for the distribution that
   you are currently building.


We recommend to use the first method, as it integrates better into
OBS. Note however, that you will be unable to build images for different
distributions from the same OBS project when adding repositories to your
project's configuration (method 1.). The problem is, that all your image
builds share the same repositories. This will result in dependency
conflicts for different distributions. On the other hand this approach
requires a lot less workarounds in the project configuration then adding
the repositories via the :file:`config.xml`.


Project Configuration
^^^^^^^^^^^^^^^^^^^^^

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

If build Vagrant images (see :ref:`setup_vagrant`) add the repository-type
`vagrant`. OBS creates a `boxes/` subdirectory in your download
repositories, which contains JSON files for Vagrant [#f4]_.


If you have added your repositories to :file:`config.xml`, you probably see
errors of the following type:

.. code:: bash

   unresolvable: have choice for SOMEPACKAGE: SOMEPAKAGE_1 SOMEPACKAGE_2

Instead of starting from scratch and manually adding ``Prefer:`` statements
to the project configuration, we recommend to copy the current project
configuration of the testing project
`Virtualization:Appliances:Images:Testing_$ARCH` into your own project.
It provides a good starting point and can be adapted to your OBS project.


.. [#f1] This is a design decision made by OBS: as it's purpose is to build
   packages in a reproducible fashion it cannot make a decision which
   package to choose from multiple available ones. A package manager build
   for end-users on the other hand **must** make an a choice, as it would
   be otherwise hardly usable.

.. [#f2] :file:`osc` compresses added folders into a `cpio
   <https://en.wikipedia.org/wiki/Cpio>`_ archive and decompresses it
   before running your builds. The only downside of this is, that the
   contents of your overlay is not conveniently visible via the web
   interface.

.. [#f3] Taken from the project
   `Virtualization:Appliances:Images:openSUSE-Tumbleweed
   <https://build.opensuse.org/project/show/Virtualization:Appliances:Images:openSUSE-Tumbleweed>`_

.. [#f4] Vagrant uses these JSON files for automatic updates of your
   Vagrant boxes.
