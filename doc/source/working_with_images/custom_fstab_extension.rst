.. _custom_fstab_extension:

Add or Update the Fstab File
============================

.. sidebar:: Abstract

   This page provides further information for customizing
   the `/etc/fstab` file which controls the mounting of
   filesystems at boot time.

In {kiwi}, all major filesystems that were created at image
build time are handled by {kiwi} itself and setup in `/etc/fstab`.
Thus there is usually no need to add entries or change the
ones added by {kiwi}. However depending on where the image is
deployed later it might be required to pre-populate fstab
entries that are unknown at the time the image is build.

Possible use cases are for example:

* Adding NFS locations that should be mounted at boot time.
  Using autofs would be an alternative to avoid additional
  entries to fstab. The information about the NFS location
  will make this image specific to the target network. This
  will be independent of the mount method, either fstab or
  the automount map has to provide it.
 
* Adding or changing entries in a read-only root system
  which becomes effective on first boot but can't be added
  at that time because of the read-only characteristics.

.. note::

   Modifications to the fstab file are a critical change. If
   done wrongly the risk exists that the system will not boot.
   In addition this type of modification makes the image
   specific to its target and creates a dependency to the
   target hardware, network, etc... Thus this feature should
   be used with care.

The optimal way to provide custom fstab information is through a
package. If this can't be done the files can also be provided via
the overlay file tree of the image description.

{kiwi} supports three ways to modify the contents of the `/etc/fstab`
file:

Providing an `/etc/fstab.append` file
  If that file exists in the image root tree, {kiwi} will take its
  contents and append it to the existing `/etc/fstab` file. The
  provided `/etc/fstab.append` file will be deleted after successful
  modification.

Providing an `/etc/fstab.patch` file
  The `/etc/fstab.patch` represents a patch file that will be
  applied to `/etc/fstab` using the `patch` program. This method
  also allows to change the existing contents of `/etc/fstab`.
  On success `/etc/fstab.patch` will be deleted.

Providing an `/etc/fstab.script` file
  The `/etc/fstab.script` represents an executable which is called
  as chrooted process. This method is the most flexible one and
  allows to apply any change. On success `/etc/fstab.script` will be
  deleted.

.. note::

   All three variants to handle the fstab file can be used together.
   Appending happens first, patching afterwards and the script call
   is last. When using the script call, there is no validation that
   checks if the script actually handles fstab or any other
   file in the image rootfs.
