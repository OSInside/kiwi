.. _building_images:

Building Images
===============

.. sidebar:: Abstract

   This chapter explains how {kiwi} |version| builds an image and what
   the build creates, how to set up the host that builds it, and how to
   define the content and the behavior of the image in the image
   description.

.. toctree::
   :hidden:

   building_images/build_process
   building_images/build_results
   building_images/build_host
   building_images/repositories
   building_images/packages
   building_images/users
   building_images/profiles
   building_images/scripts
   building_images/boot_process

The chapter follows the order in which an image is usually set up. For
the components of an image description, see
:ref:`description_components`.

.. rubric:: The Build

:doc:`building_images/build_process`
   What {kiwi} does in the prepare and the create step, and how to
   modify the root tree between them.

:doc:`building_images/build_results`
   The image types, the files a build creates, and how to bundle them
   for a release.

:doc:`building_images/build_host`
   The tools the build host needs for the different image types, and
   the runtime configuration file of {kiwi}.

.. rubric:: The Image Description

:doc:`building_images/repositories`
   The repositories the packages are installed from.

:doc:`building_images/packages`
   The packages to install into the image, and to remove from it.

:doc:`building_images/users`
   The user accounts of the image.

:doc:`building_images/profiles`
   Variants of an image built from one image description.

:doc:`building_images/scripts`
   Scripts which customize the image beyond the image description.

:doc:`building_images/boot_process`
   The initrd of the image, its {kiwi} modules and boot parameters.
