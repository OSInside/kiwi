.. _build_legacy_pxe:

Build PXE Root Filesystem Image for the legacy netboot infrastructure
======================================================================

.. _PXE: https://en.wikipedia.org/wiki/Preboot_Execution_Environment
.. _TFTP: https://en.wikipedia.org/wiki/Trivial_File_Transfer_Protocol
.. _NBD: https://en.wikipedia.org/wiki/Network_block_device
.. _AoE: https://en.wikipedia.org/wiki/ATA_over_Ethernet


.. sidebar:: Abstract

   This page explains how to build a filesystem image for use with
   {kiwi}'s PXE boot infrastructure. It contains:

   * how to build a PXE filesystem image
   * how to set up the PXE filesystem image on the PXE server
   * how to run it with QEMU

`PXE`_ is a network boot protocol that is shipped with most BIOS
implementations. The protocol sends a DHCP request to get an IP
address. When an IP address is assigned, it uses the `TFTP`_ protocol
to download a Kernel and boot instructions. Contrary to other images
built with {kiwi}, a PXE image consists of separate boot, kernel, and root
filesystem images, since these images need to be made available in
different locations on the PXE boot server.

A root filesystem image that can be deployed via {kiwi}'s PXE
netboot infrastructure represents the system's rootfs in a Linux
filesystem. A user could loop mount the image and access the
contents of the root filesystem. The image does not contain
any information about the system disk, its partitions, or the
bootloader setup. All of this information is provided by a
client configuration file on the PXE server, which controls
how the root filesystem image should be deployed.

Many different deployment strategies are possible, e.g., root over
`NBD`_ (network block device), `AoE`_ (ATA over Ethernet), or
NFS for diskless and diskful clients. This particular
example shows how to build an overlayfs-based union system based
on openSUSE Leap for a diskless client that receives the squashfs-
compressed root filesystem image in a ramdisk overlayed via
overlayfs and writes new data into another ramdisk on the same
system. As a diskless client, a QEMU virtual machine is used.

.. compound:: **Things to know before**

   * To use the image, all image parts need to be copied to the PXE boot
     server. If you have not set up such a server, refer to
     :ref:`network-boot-server` for instructions.

   * The following example assumes you will create the PXE image
     on the PXE boot server itself (if not, use `scp` to copy the files
     to the remote host).

   * To let QEMU connect to the network, we recommend setting up
     a network bridge on the host system and letting QEMU connect
     to it via a custom :file:`/etc/qemu-ifup`. For details, see
     https://en.wikibooks.org/wiki/QEMU/Networking

   * The PXE root filesystem image approach is considered a
     legacy setup. The required netboot initrd code will be maintained
     outside of the {kiwi} appliance builder code base. If possible,
     we recommend switching to the OEM disk image deployment via
     PXE.

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Build the image with {kiwi}:

   .. code:: bash

       $ sudo kiwi-ng --profile Flat system build \
           --description kiwi/build-tests/{exc_description_pxe} \
           --set-repo {exc_repo_tumbleweed} \
           --target-dir /tmp/mypxe-result

3. Change into the build directory:

   .. code:: bash

       $ cd /tmp/mypxe-result

4. Copy the initrd and the kernel to :file:`/srv/tftpboot/boot`:

   .. code:: bash

       $ cp *.initrd /srv/tftpboot/boot/initrd
       $ cp *.kernel /srv/tftpboot/boot/linux

5. Copy the system image and its SHA256 sum to :file:`/srv/tftpboot/image`:

   .. code:: bash

       $ cp {exc_image_base_name_pxe}.x86_64-{exc_image_version} /srv/tftpboot/image
       $ cp {exc_image_base_name_pxe}.x86_64-{exc_image_version}.sha256 /srv/tftpboot/image

6. Adjust the PXE configuration file.
   The configuration file controls which kernel and initrd is
   loaded and which kernel parameters are set. A template has been installed
   at :file:`/srv/tftpboot/pxelinux.cfg/default` from the ``kiwi-pxeboot``
   package. The minimal configuration required to boot the example image
   looks like the following:

   .. code:: bash

       DEFAULT KIWI-Boot

       LABEL KIWI-Boot
           kernel boot/linux
           append initrd=boot/initrd
           IPAPPEND 2

7. Create the image client configuration file:

   .. code:: bash

       $ vi /srv/tftpboot/KIWI/config.default

       IMAGE=/dev/ram1;{exc_image_base_name_pxe}.x86_64;{exc_image_version};192.168.100.2;4096
       UNIONFS_CONFIG=/dev/ram2,/dev/ram1,overlay

   All PXE boot-based deployment methods are controlled by a client
   configuration file. The above configuration tells the client where
   to find the image and how to activate it. In this case, the image
   will be deployed into a ramdisk (`ram1`) and overlay mounted such
   that all write operations will land in another ramdisk (`ram2`).
   {kiwi} supports a variety of different deployment strategies based
   on the rootfs image created beforehand. For details, refer
   to :ref:`pxe_legacy_client_config`

8. Connect the client to the network and boot. This can also be done
   in a virtualized environment using QEMU as follows:

   .. code:: bash

       $ sudo qemu -boot n -m 4096

.. _pxe_legacy_client_config:

PXE Client Setup Configuration
------------------------------

All PXE boot-based deployment methods are controlled by configuration files
located in :file:`/srv/tftpboot/KIWI` on the PXE server. Such a configuration
file can either be client-specific (config.MAC_ADDRESS, for example
config.00.AB.F3.11.73.C8), or generic (config.default).

In an environment
with heterogeneous clients, this allows for a default configuration
suitable for the majority of clients, configurations suitable
for a group of clients (for example, machines with similar or identical
hardware), and individual configurations for selected machines.

The configuration file contains data about the image and about
configuration, synchronization, and partition parameters.
The configuration file has the following general format:

.. code:: bash

    IMAGE="device;name;version;srvip;bsize;compressed,...,"

    DISK="device"
    PART="size;id;Mount,...,size;id;Mount"
    RAID="raid-level;device1;device2;..."

    AOEROOT=ro-device[,rw-device]
    NBDROOT="ip-address;export-name;device;swap-export-name;swap-device;write-export-name;write-device"
    NFSROOT="ip-address;path"

    UNIONFS_CONFIGURATION="rw-partition,compressed-partition,overlayfs"

    CONF="src;dest;srvip;bsize;[hash],...,src;dest;srvip;bsize;[hash]"

    KIWI_BOOT_TIMEOUT="seconds"
    KIWI_KERNEL_OPTIONS="opt1 opt2 ..."

    REBOOT_IMAGE=1
    RELOAD_CONFIG=1
    RELOAD_IMAGE=1

.. note:: Quoting the Values

   The configuration file is sourced by Bash, so the same quoting
   rules as for Bash apply.

Not all configuration options need to be specified. It depends on the
setup of the client which configuration values are required. The
following is a collection of client setup examples that cover all
supported PXE client configurations.

Setup Client with Remote Root
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To serve the image from a remote location and redirect all
write operations to a tmpfs, the following setup is required:

.. code:: bash

   # When using AoE, see vblade toolchain for image export

   AOEROOT=/dev/etherd/e0.1
   UNIONFS_CONFIG=tmpfs,aoe,overlay

   # When using NFS, see exports manual page for image export

   NFSROOT="192.168.100.2;/srv/tftpboot/image/root"
   UNIONFS_CONFIG=tmpfs,nfs,overlay

   # When using NBD, see nbd-server manual page for image export

   NBDROOT=192.168.100.2;root_export;/dev/nbd0
   UNIONFS_CONFIG=tmpfs,nbd,overlay

The above setup shows the most common use case where the image built
with {kiwi} is populated over the network using either AoE, NBD, or NFS
in combination with overlayfs, which redirects all write operations
to be local to the client. In any case, a setup of either AoE, NBD, or
NFS on the image server is required beforehand.

Setup Client with System on Local Disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the image on a local disk, the following setup
is required:

.. note::

   In the referenced `{exc_description_pxe}` XML description, the `pxe`
   type must be changed as follows, and the image needs to be
   rebuilt:

   .. code:: xml

       <type image="pxe" filesystem="ext3" boot="{exc_netboot}"/>

.. code:: bash

       IMAGE="/dev/sda2;{exc_image_base_name_pxe}.x86_64;{exc_image_version};192.168.100.2;4096"
       DISK="/dev/sda"
       PART="5;S;X,X;L;/"

The setup above will create a partition table on `sda` with a 5MB swap
partition (no mountpoint), and the rest of the disk will be a Linux(L)
partition with `/` as its mountpoint. The (`X`) in the `PART` setup specifies
a placeholder to indicate the default behavior.

Setup Client with System on Local MD RAID Disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the image on a local disk with a prior software RAID
configuration, the following setup is required:

.. note::

   In the referenced `{exc_description_pxe}` XML description, the `pxe`
   type must be changed as follows, and the image needs to be
   rebuilt:

   .. code:: xml

       <type image="pxe" filesystem="ext3" boot="{exc_netboot}"/>

.. code:: bash

       RAID="1;/dev/sda;/dev/sdb"
       IMAGE="/dev/md1;{exc_image_base_name_pxe}.x86_64;{exc_image_version};192.168.100.2;4096"
       PART="5;S;x,x;L;/"

The first parameter of the RAID line is the RAID level. So far, only raid1
(mirroring) is supported. The second and third parameters specify the
raid disk devices that make up the array. If a `RAID` line is present,
all partitions in `PART` will be created as RAID partitions. The first
RAID is named `md0`, the second one `md1`, and so on. It is required to
specify the correct RAID partition in the `IMAGE` line according to the
`PART` setup. In this case, `md0` is reserved for the SWAP space, and `md1`
is reserved for the system.

Setup Loading of Custom Configuration File(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To load, for example, a custom :file:`/etc/hosts` file on the client,
the following setup is required:

.. code:: bash

   CONF="hosts;/etc/hosts;192.168.1.2;4096;ffffffff"

On boot of the client, {kiwi}'s boot code will fetch the :file:`hosts` file
from the root of the server (192.168.1.2) with 4k blocksize and deploy
it as :file:`/etc/hosts` on the client. The protocol is tftp by default
but can be changed via the `kiwiservertype` kernel command-line option.
For details, see :ref:`custom-download-server`.

Setup Client to Force Reload Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To force the reload of the system image even if the image on
the disk is up-to-date, the following setup is required:

.. code:: bash

   RELOAD_IMAGE=1

The option only applies to configurations with a `DISK`/`PART` setup.

Setup Client to Force Reload Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To force the reload of all configuration files specified in
CONF, the following setup is required:

.. code:: bash

   RELOAD_CONFIG=1

By default, only configuration files that have changed according to
their checksum value will be reloaded. With the above setup, all files
will be reloaded from the PXE server. The option only applies to
configurations with a `DISK`/`PART` setup.

Setup Client for Reboot After Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To reboot the system after the initial deployment process is
done, the following setup is required:

.. code:: bash

   REBOOT_IMAGE=1

Setup custom kernel boot options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deactivate the kernel mode setting on the local
boot of the client, the following setup is required:

.. code:: bash

   KIWI_KERNEL_OPTIONS="nomodeset"

.. note::

   This does not influence the kernel options passed to the client
   if it boots from the network. To set up those, the PXE
   configuration on the PXE server needs to be changed.

Setup a Custom Boot Timeout
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set up a 10-second custom timeout for the local boot of the client,
the following setup is required.

.. code:: bash

   KIWI_BOOT_TIMEOUT="10"

.. note::

   This does not influence the boot timeout if the client boots from
   the network.

.. _custom-download-server:

Setup a Different Download Protocol and Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all downloads controlled by the {kiwi} linuxrc code are
performed by an atftp call using the TFTP protocol. With PXE, the download
protocol is fixed, and thus you cannot change the way the kernel and
the boot image (:file:`initrd`) are downloaded. As soon as Linux takes over, the
download protocols http, https, and ftp are also supported. {kiwi} uses
the `curl` program to support the additional protocols.

To select one of the additional download protocols, the following
kernel parameters need to be specified:

.. code:: bash

   kiwiserver=192.168.1.1 kiwiservertype=ftp

To set up these parameters, edit the file
:file:`/srv/tftpboot/pxelinux.cfg/default` on your PXE boot server and change
the append line accordingly.

.. note::

   Once configured, all downloads except for kernel and initrd are
   now controlled by the given server and protocol. You need to make
   sure that this server provides the same directory and file structure
   as initially provided by the `kiwi-pxeboot` package.
