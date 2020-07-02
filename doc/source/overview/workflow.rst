Basic Workflow
==============

.. note:: **Abstract**

    Installation of a Linux system generally occurs by booting the target
    system from an installation source such as an installation CD/DVD, a live
    CD/DVD, or a network boot environment (PXE). The installation process is
    often driven by an installer that interacts with the user to collect
    information about the installation. This information generally includes the
    *software to be installed*, the *timezone*, system *user* data, and
    other information. Once all the information is collected, the installer
    installs the software onto the target system using packages from the
    software sources (repositories) available. After the installation is
    complete the system usually reboots and enters a configuration procedure
    upon start-up. The configuration may be fully automatic or it may include
    user interaction.

    This description applies for version |version|.

A system image (usually called "image"), is a *complete installation* of a Linux
system within a file. The image represents an operational system and,
optionally, contains the "final" configuration.

The behavior of the image upon deployment varies depending on the image type
and the image configuration since {kiwi} allows you to completely customize
the initial start-up behavior of the image. Among others, this includes
images that:

* can be deployed inside an existing virtual environment without requiring
  configuration at start-up.
* automatically configure themselves in a known target environment.
* prompt the user for an interactive system configuration.

The image creation process with {kiwi} is automated and does not require any
user interaction. The information required for the image creation process is
provided by the primary configuration file named :file:`config.xml`.
This file is validated against the schema documented in:
:ref:`image-description`.

In addition, the image can optionally be customized
using the :file:`config.sh` and :file:`images.sh` scripts
and by using an *overlay tree (directory)* called :file:`root`.
See :ref:`description_components` section for further details.

.. note:: Previous Knowledge

    This documentation assumes that you are familiar with the general
    concepts of Linux, including the boot process, and distribution concepts
    such as package management.

.. _description_components:

Components of an Image Description
----------------------------------

A {kiwi} image description can composed by several parts. The main part is
the {kiwi} description file itself (named :file:`config.xml` or an arbitrary
name plus the :file:`*.kiwi` extension). The configuration XML is the
only required component, others are optional.

These are the optional components of an image description:

#. ``config.sh`` shell script

   Is the configuration shell script that runs and the end of the
   :ref:`prepare step <prepare-step>` if present. It can be used to
   fine tune the unpacked image.

   Note that the script is directly invoked by the operating system if its
   executable bit is set. Otherwise it is called by :file:`bash` instead.

#. ``images.sh`` shell script

   Is the configuration shell script that runs at the beginning of the
   create step. So it is expected to be used to handle image type specific
   tasks. It is called in a similar fashion as ``config.sh``

#. Overlay tree directory

   The *overlay tree* is a folder (called :file:`root`)
   or a tarball file (called :file:`root.tar.gz`) that contains
   files and directories that will be copied to the target image build tree
   during the :ref:`prepare step <prepare-step>`. It is executed
   after all the packages included in the :file:`config.xml` file
   have been installed. Any already present file is overwritten.

#. CD root user data

   For live ISO images and install ISO images an optional cdroot archive
   is supported. This is a tar archive matching the name
   :file:`config-cdroot.tar[.compression_postfix]`. If present it will
   be unpacked as user data on the ISO image. This is mostly useful to
   add e.g license files or user documentation on the CD/DVD which
   can be read directly without booting from the media.

#. Archives included in the :file:`config.xml` file.

   The archives that are included in the `<packages>` using the `<archive>`
   subsection:

   .. code:: xml

      <packages type="image">
          <archive name="custom-archive.tgz"/>
      </packages>
