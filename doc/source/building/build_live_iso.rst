.. _hybrid_iso:

Build an ISO Hybrid Live Image
==============================

.. sidebar:: Abstract

   This page explains how to build a live image. It contains:

   * how to build an ISO image
   * how to run it with QEMU

A Live ISO image is a system on a removable media, e.g CD/DVD or USB stick.
Once built and deployed it boots off from this media without interfering
with other system storage components making it a useful pocket system for
testing and demo- and debugging-purposes.

To add a live ISO build to your appliance, create a `type` element with
`image` set to `iso` in your :file:`config.xml` (see
:ref:`xml-description-build-types`) as shown below:

.. code-block:: xml

   <?xml version="1.0" encoding="utf-8"?>

   <image schemaversion="6.9" name="JeOS-Tumbleweed">
     <!-- snip -->

     <preferences>
       <type image="iso" primary="true" flags="overlay" hybrid="true" hybridpersistent_filesystem="ext4" hybridpersistent="true"/>
       <!-- additional preferences -->
     </preferences>

     <!-- snip -->
   </image>

The following attributes of the `type` element are relevant when building
live ISO images:

- `flags`: Specifies the live ISO technology and dracut module to use, can
  be set to `overlay` or to `dmsquash`.

  If set to `overlay` the kiwi-live dracut module will be used to support a
  live iso system based on squashfs+overlayfs.
  If set to `dmsquash` the dracut standard dmsquash-live module will be used
  to support a live ISO system based on squashfs and the device
  mapper. Please note both modules support a different set of live
  features.

.. no clue what this is: hybrid="true"
- `hybridpersistent`: Accepts `true` or `false`, if set to `true`
  then the resulting image will be created with a COW file to keep data
  persistent over a reboot

- `hybridpersistent_filesystem`: The filesystem which will be used for the
  COW file. Possible values are `ext4` or `xfs`, with `ext4` being the
  default.


With the appropriate settings present in :file:`config.xml` KIWI can now
build the image:

.. code:: bash

   $ sudo kiwi-ng --type iso system build \
         --description path/to/description/directory \
         --target-dir /tmp/myimage

The resulting image can be found in the folder :file:`/tmp/myimage` and can
be tested with QEMU:

.. code:: bash

   $ qemu -cdrom LimeJeOS-Leap-42.3.x86_64-1.42.3.iso -m 4096

The image is now complete and ready to use. See :ref:`iso_to_usb_stick` and
:ref:`iso_as_file_to_usb_stick` for further information concerning
deployment.
