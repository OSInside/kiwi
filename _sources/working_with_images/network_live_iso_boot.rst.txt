.. _network_live_boot:

Booting a Live ISO Image from Network
=====================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with {kiwi} and references the following
   articles:

   * :ref:`hybrid_iso`

In {kiwi}, live ISO images can be configured to boot via the
PXE boot protocol. This functionality requires a network boot
server setup on the system. Details how to setup such a server
can be found in :ref:`network-boot-server`.

After the live ISO was built as shown in :ref:`hybrid_iso`,
the following configuration steps are required to boot from
the network:

1. Extract initrd/kernel From Live ISO

   The PXE boot process loads the configured kernel and initrd from
   the PXE server. For this reason, those two files must be extracted
   from the live ISO image and copied to the PXE server as follows:
   
   .. code:: bash

      $ mount {exc_image_base_name_live}.x86_64-{exc_image_version}.iso /mnt
      $ cp /mnt/boot/x86_64/loader/initrd /srv/tftpboot/boot/initrd
      $ cp /mnt/boot/x86_64/loader/linux /srv/tftpboot/boot/linux
      $ umount /mnt

   .. note::

      This step must be repeated with any new build of the live ISO image

2. Export Live ISO To The Network

   Access to the live ISO file must be provided by either `ftp`,
   `http`, `https` or `dolly`. The most simple method is to setup a FTP server
   e.g. `vsftpd` and copy the live ISO file to the data directory:

   .. code:: bash

       $ mkdir -p /srv/ftp/image
       $ cp {exc_image_base_name_live}.x86_64-{exc_image_version}.iso /srv/ftp/image

   .. note::

       Check if the image can be downloaded via:
       `wget ftp://IP/image/{exc_image_base_name_live}.x86_64-{exc_image_version}.iso`
       before the next step.

3. Setup live ISO boot entry in PXE configuration

   .. note::

      The following step assumes that the pxelinux.0 loader
      has been configured on the boot server to boot up network
      clients

   Edit the file :file:`/srv/tftpboot/pxelinux.cfg/default` and create
   a boot entry of the form:

   .. code:: bash

      LABEL Live-Boot
          kernel boot/linux
          append initrd=boot/initrd ip=dhcp root=live:ftp://IP/image/{exc_image_base_name_live}.x86_64-{exc_image_version}.iso

   * The `ip=` parameter controls how the dracut network module sets up
     the network. Several options exists to control how the network
     interface should be setup. Please consult the dracut manual
     for further information.

   * The boot parameter `root=live:PROTOCOL://IP/PATH...` specifies the
     remote endpoint and protocol to find the live ISO file. So far
     `ftp`, `http`, `https` and `dolly` are supported.

4. Boot from the Network

   Within the network which has access to the PXE server and the
   IP in the root= option, any network client can now boot the
   live system. A test based on QEMU is done as follows:

   .. code:: bash

      $ qemu -boot n

Available Remote Boot Options
-----------------------------

There are the following kernel boot options available to control
the behavior of the remote boot process.

rd.kiwi.live.curl_options=
  Options passed along to the curl call

rd.kiwi.live.dolly_options=
  Options passed along to the dolly call

rd.kiwi.live.system=
  Block device to use for the system. By default this is set to `/dev/ram0`

ramdisk_size=bytes
  Size of the ramdisk in bytes. By default this is set to 2097152 (2G)

rd.kiwi.live.reset
  Force reset of the live system. This option only makes sense if
  the live system device (rd.kiwi.live.system) points to a persistent
  storage device. In this case {kiwi} loads the system only once
  and does not overwrite it unless a reset is requested.

Persistent Live System
----------------------

The remote boot process of a live ISO image, places the ISO file
into a ramdisk by default. This means all data lives in memory and
is not persistent. In order to boot up the live system from a remote
location and keep it on a persistent storage, it's required to
pass the `rd.kiwi.live.system` boot option with the device name
pointing to that persistent storage.

.. warning::

    All data on the device given via `rd.kiwi.live.system` will be wiped

A test based on QEMU is done as follows:

Edit the file :file:`/srv/tftpboot/pxelinux.cfg/default` and create
a boot entry of the form:

.. code:: bash

   LABEL Live-Boot
       kernel boot/linux
       append initrd=boot/initrd ip=dhcp root=live:ftp://IP/image/{exc_image_base_name_live}.x86_64-{exc_image_version}.iso ramdisk_size=3545728 rd.kiwi.live.system=/dev/sda rd.live.overlay.persistent rd.live.overlay.cowfs=xfs

* The `rd.live.overlay.persistent` and `rd.live.overlay.cowfs=xfs`
  options are standard {kiwi} live ISO options to control if and how a
  persistent write partition should be created. The options only take
  an effect when booting into a persistent storage device.

Next create a persistent storage disk of 3G and attach it to the
QEMU instance.

.. code:: bash

   $ qemu-img create mydisk.raw 3G
   $ qemu -boot n -hda mydisk.raw

The live system will be deployed once to the locally attached disk and
boots from it. Any subsequent boot process will not modify the local
disk unless `rd.kiwi.live.reset` is passed on the kernel command line.
If deployed there is also no need for the network anymore and the
system could also boot standalone.
