.. _building_wsl_build:

Build a WSL Container Image
===========================

.. sidebar:: Abstract

   This page explains how to build a WSL/Appx container image.
   WSL stands for Windows Subsystem Linux and is a zip based
   container format consumable by Windows 10 with enabled
   WSL functionality.


{kiwi} is capable of building WSL images using the :command:`appx`
utility. Make sure you have installed a package that provides
this command on your build host.

Once the build host has the :command:`appx` installed, the
following image type setup is required in the XML description
:file:`config.xml`:

.. code:: xml

   <type image="appx" metadata_path="/meta/data"/>

The :file:`/meta/data` path specifies a path that provides
additional information required for the :command:`WSL-DistroLauncher`.
This component consists out of a Windows(`exe`) executable file and
an :file:`AppxManifest.xml` file which references other files
like icons and resource configurations for the startup of the
container under Windows.

.. note:: **/meta/data**

   Except for the root filesystem tarball {kiwi} is not
   responsible for providing the meta data required for
   the :command:`WSL-DistroLauncher`. It is expected that
   the given metadata path contains all the needed information.
   Typically this information is delivered in a package
   provided by the Distribution and installed on the
   build host


Setup of the WSL-DistroLauncher
-------------------------------

The contents of the :file:`AppxManifest.xml` will be changed by {kiwi}
if a :file:`containerconfig` section is provided in the XML description.
In the context of a WSL image the following container configuration
parameters are taken into account:

.. code:: xml

   <containerconfig name="my-wsl-container">
       <history
           created_by="Organisation"
           author="Name"
           application_id="AppIdentification"
           package_version="https://docs.microsoft.com/en-us/windows/uwp/publish/package-version-numbering"
           launcher="WSL-DistroLauncher-exe-file"
       >Container Description Text</history>
   </containerconfig>

All information provided here including the entire section is optional.
If not provided the existing :file:`AppxManifest.xml` stays untouched.

created_by
  Provides the name of a publisher organisation. An appx container
  needs to be signed off with a digital signature. If the image is
  build in the Open Build Service (OBS) this happens automatically.
  Outside of OBS one needs to make sure the given publisher organisation
  name matches the certificate used for signing.

author
  Provides the name of the author and maintainer of this container

application_id
  Provides an ID name for the container. The name must start with
  a letter and only allows alphanumeric characters. {kiwi} will not
  validate the given name string because there is no common criteria
  between the container architectures. {kiwi} just accepts any text.

package_version
  Provides the version identification for the container. {kiwi}
  validates this against the `Microsoft Package Version Numbering
  <https://docs.microsoft.com/en-us/windows/uwp/publish/package-version-numbering>`_ rules.

launcher
  Provides the binary file name of the launcher :file:`.exe` file.

.. warning::

   There is no validation by {kiwi} if the contents of :file:`AppxManifest.xml`
   are valid or complete to run the container. Users will find out at
   call time, not before

The following example shows how to build a WSL image based on
openSUSE TW:

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

#. Include the ``Virtualization/WSL`` repository to your list:

   .. code:: bash

      $ zypper addrepo http://download.opensuse.org/repositories/Virtualization:/WSL/<DIST> WSL

   where the placeholder `<DIST>` is the preferred distribution.

#. Install :command:`fb-util-for-appx` utility and a package that
   provides the :command:`WSL-DistroLauncher` metadata. See the
   above note about :file:`/meta/data`

   .. code:: bash

      $ zypper in fb-util-for-appx DISTRO_APPX_METADATA_PACKAGE

   .. note::

      If you are building in the Open Build Service make sure
      to add the packages from the zypper call above to your
      project config via :command:`osc meta -e prjconf` and
      a line of the form :file:`support: PACKAGE_NAME` for
      each package that needs to be installed on the Open Build
      Service worker that runs the {kiwi} build process.

#. Setup the image type:

   Edit the XML description file:
   :file:`kiwi/build-tests/{exc_description_wsl}/appliance.kiwi`
   and add the following type and containerconfig:

   .. code:: xml

      <type image="appx" metadata_path="/meta/data">
          <containerconfig name="Tumbleweed">
              <history
                  created_by="SUSE"
                  author="KIWI-Team"
                  application_id="tumbleweed"
                  package_version="2003.12.0.0"
                  launcher="openSUSE-Tumbleweed.exe"
              >Tumbleweed Appliance text based</history>
          </containerconfig>
      </type>

   .. warning::

      If the configured metadata path does not exist the build
      will fail. Furthermore there is no validation by {kiwi}
      that the contents of the metadata path are valid or
      complete with respect to the requirements of the
      :command:`WSL-DistroLauncher`

#. Build the image with {kiwi}:

   .. code:: bash

      $ sudo kiwi-ng system build \
          --description kiwi/build-tests/{exc_description_wsl} \
          --set-repo {exc_repo_tumbleweed} \
          --target-dir /tmp/myimage

Testing the WSL image
---------------------

For testing the image a Windows 10 system is required. As a first step
the optional feature named :file:`Microsoft-Windows-Subsystem-Linux`
must be enabled. For further details on how to setup the Windows machine
see the following documentation:
`Windows Subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/about>`__
