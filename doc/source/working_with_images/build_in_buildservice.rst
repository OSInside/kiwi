Building in the Open Build Service
==================================

.. note:: **Abstract**

   This document gives a brief overview how to build images with
   {kiwi} in version |version| inside of the Open Build Service.
   A tutorial on the Open Buildservice itself can be found here:
   https://en.opensuse.org/openSUSE:Build_Service_Tutorial


The next generation {kiwi} is fully integrated with the Open Build Service.
In order to start it's best to checkout one of the integration test
image build projects from the base Testing project
`Virtualization:Appliances:Images:Testing_$ARCH:$DISTRO` at:

https://build.opensuse.org

For example the test images for SUSE on x86 can be found `here
<https://build.opensuse.org/project/show/Virtualization:Appliances:Images:Testing_x86:leap>`__.


Advantages of using the Open Build Service (OBS)
------------------------------------------------

The Open Build Service offers multiple advantages over running {kiwi}
locally:

* OBS will host the latest successful build for you without having to setup
  a server yourself.

* As {kiwi} is fully integrated into OBS, OBS will automatically rebuild your
  images if one of the included packages or one of its dependencies or {kiwi}
  itself get updated.

* The builds will no longer have to be executed on your own machine, but
  will run on OBS, thereby saving you resources. Nevertheless, if a build
  fails, you get a notification via email (if enabled in your user's
  preferences).


Differences Between Building Locally and on OBS
-----------------------------------------------

Note, there is a number of differences when building images with {kiwi} using
the Open Build Service. Your image that build locally just fine, might not
build without modifications.

The notable differences to running {kiwi} locally include:

* OBS will pick the {kiwi} package from the repositories configured in your
  project, which will most likely not be the same version that you are
  running locally.
  This is especially relevant when building images for older versions like
  SUSE Linux Enterprise. Therefore, include the custom appliances
  repository as described in the following section:
  :ref:`obs-recommended-settings`.

* When {kiwi} runs on OBS, OBS will extract the list of packages from
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

* By default, OBS builds only a single build type and the default
  profile. If your appliance uses multiple build types, put
  each build type into a profile, as OBS cannot handle multiple build
  types.

  There are two options to build multiple profiles on OBS:

  1. Use the `<image>` element and add it bellow the XML
     declaration (`<?xml ..?>`):

     .. code:: xml

        <?xml version="1.0" encoding="utf-8"?>

        <!-- OBS-Profiles: foo_profile bar_profile -->

        <image schemaversion="{schema_version}" name="openSUSE-Leap-15.1">
          <!-- image description with the profiles foo_profile and bar_profile
        </image>

  2. Use the `multibuild <https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.multibuild.html>`_ feature.

  The first option is simpler to use, but has the disadvantage that your
  appliances are built sequentially. The `multibuild` feature allows to
  build each profile as a single package, thereby enabling parallel execution,
  but requires an additional :file:`_multibuild` file. For the above example
  :file:`config.xml` would have to be adapted as follows:

  .. code:: xml

     <?xml version="1.0" encoding="utf-8"?>

     <!-- OBS-Profiles: @BUILD_FLAVOR@ -->

     <image schemaversion="{schema_version}" name="openSUSE-Leap-15.1">
       <!-- image description with the profiles foo_profile and bar_profile
     </image>

  The file :file:`_multibuild` would have the following contents:

  .. code:: xml

     <multibuild>
       <flavor>foo_profile</flavor>
       <flavor>bar_profile</flavor>
     </multibuild>


* Subfolders in OBS projects are ignored by default by :command:`osc` and
  must be explicitly added via :command:`osc add $FOLDER` [#f2]_. Bear that
  in mind when adding the overlay files inside the :file:`root/` directory
  to your project.

* OBS ignores file permissions. Therefore :file:`config.sh` and
  :file:`images.sh` will **always** be executed through BASH (see also:
  :ref:`working-with-kiwi-user-defined-scripts`).

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

.. code:: xml

  <repository name="images">
    <arch>x86_64</arch>
  </repository>

Furthermore, OBS requires additional repositories from which it obtains
your dependent packages. These repositories can be provided in two ways:

#. Add the repositories to the project configuration on OBS and omit them
   from :file:`config.xml`. Provide only the following repository inside
   the image description:

   .. code:: xml

      <repository type="rpm-md">
        <source path="obsrepositories:/"/>
      </repository>

   This instructs OBS to inject the repositories from your project into
   your appliance.

   Additional repositories can be added by invoking ``osc meta -e prj`` and
   adding a line of the following form as a child of ``<repository
   name="images">``:

   .. code:: xml

      <path project="$OBS_PROJECT" repository="$REPOSITORY_NAME"/>

   The order in which you add repositories matters: if a package is present
   in multiple repositories, then it is taken from the **first**
   repository. The **last** repository is subject to path expansion: its
   repository paths are included as well.

   Don't forget to add the repository from the
   `Virtualization:Appliances:Builder` project, providing the latest stable
   version of {kiwi} (which you are very likely using for your local builds).

   The following example repository configuration [#f3]_ adds the
   repositories from the `Virtualization:Appliances:Builder` project and
   those from the latest snapshot of openSUSE Tumbleweed:

   .. code:: xml

      <project name="Virtualization:Appliances:Images:openSUSE-Tumbleweed">
        <title>Tumbleweed JeOS images</title>
        <description>Host JeOS images for Tumbleweed</description>
        <repository name="images">
          <path project="Virtualization:Appliances:Builder" repository="Factory"/>
          <path project="openSUSE:Factory" repository="snapshot"/>
          <arch>x86_64</arch>
        </repository>
      </project>

   The above can be simplified further using the path expansion of the last
   repository to:

   .. code:: xml

      <project name="Virtualization:Appliances:Images:openSUSE-Tumbleweed">
        <title>Tumbleweed JeOS images</title>
        <description>Host JeOS images for Tumbleweed</description>
        <repository name="images">
          <path project="Virtualization:Appliances:Builder" repository="Factory"/>
          <arch>x86_64</arch>
        </repository>
      </project>

   Now `Virtualization:Appliances:Builder` is the last repository, which'
   repositories are included into the search path. As
   `openSUSE:Factory/snapshot` is among these, it can be omitted from the
   repository list.

#. Keep the repositories in your :file:`config.xml` configuration file. If
   you have installed the latest stable {kiwi} as described in
   :ref:`kiwi-installation` then you should add the following repository to
   your projects configuration (accessible via :command:`osc meta -e
   prjconf`), so that OBS will pick the latest stable {kiwi} version too:

   .. code:: xml

      <repository name="images">
        <path project="Virtualization:Appliances:Builder" repository="$DISTRO"/>
        <arch>x86_64</arch>
      </repository>

   Replace ``$DISTRO`` with the appropriate name for the distribution that
   you are currently building and optionally adjust the architecture.


We recommend to use the first method, as it integrates better into
OBS. Note that your image description will then no longer build outside of
OBS though. If building locally is required, use the second method.

.. warning::

   Adding the repositories to project's configuration makes it impossible
   to build images for different distributions from the same project.

   Since the repositories are added for every package in your project, all
   your image builds will share the same repositories, thereby resulting in
   conflicts for different distributions.

   We recommend to create a separate project for each distribution. If that
   is impossible, you can keep all your repositories (including
   `Virtualization:Appliances:Builder`) in :file:`config.xml`. That however
   usually requires a large number of workarounds via `Prefer:` settings in
   the project configuration and is thus **not** recommended.


Project Configuration
^^^^^^^^^^^^^^^^^^^^^

The Open Build Service will by default create the same output file as {kiwi}
when run locally, but with a custom filename ending (that is unfortunately
unpredictable). This has the consequence that the download URL of your
image will change with every rebuild (and thus break automated
scripts). OBS can create symbolic links with static names to the latest
build by adding the following line to the project configuration:

.. code:: bash

   Repotype: staticlinks

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
`Virtualization:Appliances:Images:Testing_$ARCH:$DISTRO` into your own project.
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
