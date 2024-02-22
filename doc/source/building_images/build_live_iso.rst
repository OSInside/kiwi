.. _hybrid_iso:

Build an ISO Hybrid Live Image
==============================

.. sidebar:: Abstract

   This page explains how to build a live image. It covers the following topics:

   * how to build an ISO image
   * how to run the image with QEMU

A Live ISO image is a system on a removable media, for example a CD/DVD or a USB
stick. Booting a Live ISO image does not interfere
with other system storage components, making it a useful portable system for
demonstration, testing, and debugging.

To add a Live ISO build to your appliance, create a `type` element with
`image` set to `iso` in the :file:`config.xml` file as shown below:

.. code:: xml

   <image schemaversion="{schema_version}" name="Tumbleweed_appliance">
     <!-- snip -->
     <preferences>
       <type image="iso" primary="true" flags="overlay" hybridpersistent_filesystem="ext4" hybridpersistent="true"/>
       <!-- additional preferences -->
     </preferences>
     <!-- snip -->
   </image>

The following attributes of the `type` element are relevant when building
Live ISO images:

- `flags`: Specifies the dracut module to use.

  If set to `overlay`, the kiwi-live dracut module supplied by {kiwi} is used
  for booting.

  If set to `dmsquash`, the dracut-supplied dmsquash-live module is
  used for booting.

  Both modules support a different set of live features.
  For details see :ref:`live_features`

- `filesystem`: Specifies the root filesystem for the live system.

  If set to `squashfs`, the root filesystem is written into a squashfs image.
  This option is not compatible with device-mapper specific features of the
  dmsquash-live dracut module. In that case, use overayfs.

  If set to a value different from `squashfs`, the root filesystem is written
  into a filesystem image of the specified type, and the filesystem image
  written into a squashfs image for compression.

  The default value of this option is `ext4`.

- `hybridpersistent`: Accepts `true` or `false`, if set to `true`, the
  resulting image is created with a COW file to keep data persistent
  over a reboot.

- `hybridpersistent_filesystem`: The filesystem used for the COW
  file. Valid values are `ext4` or `xfs`, with `ext4` being the default.


With the appropriate settings specified in :file:`config.xml`, you can build an
image using {kiwi}:

.. code:: bash

   $ sudo kiwi-ng system build \
         --description kiwi/build-tests/{exc_description_live} \
         --set-repo {exc_repo_leap} \
         --target-dir /tmp/myimage

The resulting image is saved in :file:`/tmp/myimage`, and the image can
be tested with QEMU:

.. code:: bash

   $ sudo qemu -cdrom \
         {exc_image_base_name_live}.x86_64-{exc_image_version}.iso \
         -m 4096 -serial stdio

The image is now complete and ready to use. See :ref:`iso_to_usb_stick` and
:ref:`iso_as_file_to_usb_stick` for further information concerning
deployment.

.. _live_features:

`overlay` or `dmsquash`
----------------------------------

Whether you choose the `overlay` or `dmsquash` dracut module depends on the
features you intend to use. The `overlay` module supports only overlayfs
based overlays, but with automatic creation of a writable layer for
persistence. The `dmsquash` module supports overlayfs as well as
device-mapper based overlays.

The following list describes important Live ISO features and their support
status in the `overlay` and `dmsquash` modules.

ISO scan
  Usable in the same way with both dracut modules. This feature allows
  to boot the Live ISO as a file from a grub loopback configured bootloader.
  The `live-grub-stick` tool is one example that uses this feature.
  For details how to setup ISO scan with the `overlay` module see
  :ref:`iso_as_file_to_usb_stick`

ISO in RAM completely
  Usable with the `dmsquash` module through `rd.live.ram`. The `overlay`
  module does not support this mode, while {kiwi} supports RAM only systems
  as OEM deployment into RAM from an install ISO media. For details how
  to setup RAM only deployments in {kiwi} see: :ref:`ramdisk_deployment`

Overlay based on overlayfs
  Usable with both dracut modules. The readonly root filesystem is
  overlaid with a readwrite filesystem using the kernel overlayfs
  filesystem.

Overlay based on device mapper snapshots
  Usable with the `dmsquash` module. A squashfs compressed readonly root
  is overlaid with a readwrite filesystem using a device mapper
  snapshot.

Media Checksum Verification
  Boot the Live iso only for ISO checksum verification. This is possible with
  both modules but the `overlay` module uses the `checkmedia` tool, whereas the
  upstream `dmsquash` module uses `checkisomd5`. The verification process is
  triggered by passing the kernel option `mediacheck` for the `overlay` module
  and `rd.live.check` for the `dmsquash` module.

Live ISO through PXE boot
  Boot the Live image via the network. This is possible with both
  modules, but it uses different technologies. The `overlay` module supports
  network boot only in combination with the AoE (Ata Over Ethernet) protocol.
  For details see :ref:`network_live_boot`. The `dmsquash` module supports
  network boot by fetching the ISO image into memory from `root=live:<url>`
  using the `livenet` module.

Persistent Data
  Keep new data persistent on a writable storage device. This can be done
  with both modules but in different ways. The `overlay` module activates
  persistency with the kernel boot parameter `rd.live.overlay.persistent`.
  If the persistent setup cannot be created the fallback to the non persistent
  mode applies automatically. The `overlay` module auto detects if it is
  used on a disk or ISO scan loop booted from a file. If booted as disk,
  persistency is setup on a new partition of that disk. If loop booted
  from file, persistency is setup on a new cow file. The cow file/partition
  setup can be influenced with the kernel boot parameters:
  `rd.live.overlay.cowfs` and `rd.live.cowfile.mbsize`. The `dmsquash`
  module configures persistency through the `rd.live.overlay` option
  exclusively and does not support the automatic creation of a write
  partition in disk mode.

.. admonition:: dmsquash documentation

   Documentation for the upstream `dmsquash` module can be found
   `here <http://man7.org/linux/man-pages/man7/dracut.cmdline.7.html>`_.
   Options to setup `dmsquash` are marked with `rd.live`
