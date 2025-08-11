.. _building_wsl_build:

Build a WSL Container Image
===========================

.. sidebar:: Abstract

   This page explains how to build a WSL/Appx container image. WSL stands for
   Windows Subsystem Linux, and it is a zip-based container format consumable by
   Windows 10 with WSL enabled.


{kiwi} can build WSL images using the :command:`appx`
utility. Make sure you have installed the package that provides
the command on your build host.

Once the build host has the :command:`appx` installed, the
following image type setup is required in the XML description
:file:`config.xml`:

.. code:: xml

   <type image="appx" metadata_path="/meta/data"/>

The :file:`/meta/data` path specifies a path that provides
additional information required for the :command:`WSL-DistroLauncher`.
This component consists out of a Windows(`exe`) executable file and
an :file:`AppxManifest.xml` file that references other files,
like icons and resource configurations for the startup of the
container under Windows.

.. note:: **/meta/data**

   Except for the root filesystem tarball {kiwi} is not
   responsible for providing the meta data required for
   the :command:`WSL-DistroLauncher`. It is expected that
   the given metadata path contains all the needed information.
   Typically this information is delivered in a package
   provided by the distribution, and it is installed on the
   build host.


Setup of the WSL-DistroLauncher
-------------------------------

The contents of the :file:`AppxManifest.xml` is changed by {kiwi}
if the :file:`containerconfig` section is provided in the XML description.
In the context of a WSL image, the following container configuration
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

All information provided here, including the entire section, is optional. If the
information is not specified, the existing :file:`AppxManifest.xml` is left
untouched.

created_by
  Specifies the name of a publisher organization. An appx container
  must to be signed off with a digital signature. If the image is
  build in the Open Build Service (OBS), this is done automatically.
  Outside of OBS, you must o make sure that the given publisher organization
  name matches the certificate used for signing.

author
  Provides the name of the author and maintainer of this container.

application_id
  Specifies an ID name for the container. The name must start with
  a letter, and only alphanumeric characters are allowed. {kiwi} doesn not
  validate the specified name string, because there is no common criteria
  for various the container architectures.

package_version
  Specifies the version identification for the container. {kiwi}
  validates it against the `Microsoft Package Version Numbering
  <https://docs.microsoft.com/en-us/windows/uwp/publish/package-version-numbering>`_ rules.

launcher
  Specifies the binary file name of the launcher :file:`.exe` file.

.. warning::

   {kiwi} does not check the configuration in :file:`AppxManifest.xml`
   ifor validity or completeness.

The following example shows how to build a WSL image based on
openSUSE Tumbleweed:

1. Check the example image descriptions,
   see :ref:`example-descriptions`.

#. Include the ``Virtualization/WSL`` repository to the list ((replace `<DIST>`
   with the desired distribution)):

   .. code:: bash

      $ zypper addrepo http://download.opensuse.org/repositories/Virtualization:/WSL/<DIST> WSL

#. Install :command:`fb-util-for-appx` utility and the package that
   provides the :command:`WSL-DistroLauncher` metadata. See the
   previous note on :file:`/meta/data`.

   .. code:: bash

      $ zypper in fb-util-for-appx DISTRO_APPX_METADATA_PACKAGE

   .. note::

      When building images with the Open Build Servic,e make sure
      to add the packages from the zypper command above to the
      project configuration via :command:`osc meta -e prjconf` along with
      the line :file:`support: PACKAGE_NAME` for
      each package that needs to be installed on the Open Build
      Service worker that runs the {kiwi} build process.

#. Configure the image type:

   Add the following type and container configuration to
   :file:`kiwi/build-tests/{exc_description_wsl}/appliance.kiwi`:

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

      If the configured metadata path does not exist, the build will fail.
      Furthermore, {kiwi} does not check whether the metadata is complete or is
      valid according to the requirements of the :command:`WSL-DistroLauncher`

#. Build the image with {kiwi}:

   .. code:: bash

      $ sudo kiwi-ng system build \
          --description kiwi/build-tests/{exc_description_wsl} \
          --set-repo {exc_repo_tumbleweed} \
          --target-dir /tmp/myimage

Testing the WSL image
---------------------

For testing the image, you need a Windows 10 system. Before you proceed, enable
the optional feature named :file:`Microsoft-Windows-Subsystem-Linux`. For
further details on how to setup the Windows machine, see: `Windows Subsystem for Linux
<https://docs.microsoft.com/en-us/windows/wsl/about>`__
