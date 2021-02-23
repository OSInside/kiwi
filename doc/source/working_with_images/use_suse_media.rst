.. _suse_media:

Using SUSE Product ISO To Build
===============================

.. sidebar:: Abstract

    This page provides information how to use the SUSE
    media ISO with {kiwi}

When building an image with {kiwi}, the image description usually
points to a number of public/private package source repositories
from which the new image root tree will be created. Alternatively
the vendor provided product ISO image(s) can be used. The contents
of the ISO (DVD) media also provides package source repositories
but organized in a vendor specific structure. As a user it's
important to know about this structure such that the {kiwi}
image description can consume it.

To use a SUSE product media the following steps are required:

1. Mount the ISO media from file or DVD drive:

.. code:: bash

    $ sudo mount Product_ISO_file.iso|DVD_drive /media/suse

2. Lookup all `Product` and `Module` directories:

   Below `/media/suse` there is a directory structure which
   provides package repositories in directories starting
   with `Product-XXX` and `Module-XXX`. It depends on the
   package list in the {kiwi} image description from which
   location a package or a dependency of the package is
   taken. Therefore it is best practice to browse through
   all the directories and create a `<repository>` definition
   for each of them in the {kiwi} image description like
   the following example shows:

   .. code:: xml

       <repository alias="DVD-1-Product-SLES">
           <source path="file:///media/suse/Product-SLES"/>
       </repository>

       <repository alias="DVD-1-Module-Basesystem">
           <source path="file:///media/suse/Module-Basesystem"/>
       </repository>

Once all the individual product and module repos has been created
in the {kiwi} image description, the build process can be started
as usual.

.. note::

    Because of the manual mount process the `/media/suse` location
    stays busy after {kiwi} has created the image. The cleanup of
    this resource is a responsibility of the user and not done
    by {kiwi}
