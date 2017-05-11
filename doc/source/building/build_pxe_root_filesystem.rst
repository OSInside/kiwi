Build a PXE root File System Image
==================================

.. toctree::
   :maxdepth: 1

   build_pxe_root_filesystem/setup_pxe_bootserver

.. hint::

   Make sure you have checked out the example image descriptions
   For details see :ref:`example-descriptions`

PXE is a network boot protocol that is shipped with most BIOS
implementations. The protocol sends a DHCP request to get an IP
address. When an IP address is assigned, it uses the TFTP protocol to
download a Kernel and boot instructions. Contrary to other images built
with KIWI, a PXE image consists of separate boot and system images, since
both images need to be made available in different locations on the network
boot server.

The following example shows how to build one out of many possible
network root filesystem flavours. The command below generates a squashfs
root file system image which is designed to become deployed as an
overlayfs-based union system. To use the image, all image parts need
to be copied to a PXE boot server. If you have not set up such a server,
refer to :ref:`pxe-boot-server` for instructions. The following
example assumes you have created the PXE image on the boot server itself
(if not, use **scp** to copy the files on the remote host)

.. code:: bash

    $ sudo kiwi-ng --profile netboot --type pxe system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/mypxe-result

1. Change into the build directory

   .. code:: bash

      $ cd /tmp/mypxe-result

2. Copy the initrd and the kernel to /srv/tftpboot/boot

   .. code:: bash

      $ cp initrd-netboot-suse-*.gz /srv/tftpboot/boot/initrd
      $ cp initrd-netboot-suse-*.kernel /srv/tftpboot/boot/linux

3. Copy the system image and its md5 sum to /srv/tftpboot/image

   .. code:: bash

      $ cp LimeJeOS-Leap-42.1.x86_64-1.42.1 /srv/tftpboot/image
      $ cp LimeJeOS-Leap-42.1.x86_64-1.42.1.md5 /srv/tftpboot/image

4. Adjust the PXE configuration file. it controls which kernel and initrd is
   loaded and which kernel parameters are set. A template has been installed
   at /srv/tftpboot/pxelinux.cfg/default with the kiwi-pxeboot package.
   The minimal configuration required to boot the example image looks
   like to following:

   .. code:: bash

      DEFAULT KIWI-Boot

      LABEL KIWI-Boot
          kernel boot/linux
          append initrd=boot/initrd
          IPAPPEND 2

5. Create the image client configuration file

   .. code:: bash

      $ vi /srv/tftpboot/KIWI/config.default

        IMAGE=/dev/ram1;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096
        UNIONFS_CONFIG=/dev/ram2,/dev/ram1,overlay

   All PXE boot based deployment methods are controlled by a client
   configuration file. The above configuration tells the client where
   to find the image and how to activate it. In this case the image
   will be deployed into a ramdisk (ram1) and overlay mounted such
   that all write operations will land in another ramdisk (ram2).
   KIWI supports a variety of different deployment strategies based
   on the rootfs image created beforehand. For details please refer
   to :ref:`pxe-deployments`

6. Connect the client to the network and boot. This can also be done
   in a virtualized environment using QEMU as follows:

   .. code:: bash

      $ qemu -boot n

   .. note:: QEMU bridged networking

      In order to let qemu connect to the network we recommend to
      setup a network bridge on the host system and let qemu connect
      to it via a custom /etc/qemu-ifup. For details see
      https://en.wikibooks.org/wiki/QEMU/Networking

.. _pxe-deployments:

PXE Client Configuration
------------------------

All PXE boot based deployment methods are controlled by configuration files
located in /srv/tftpboot/KIWI on the PXE server. Such a configuration
file can either be client-specific (config.MAC_ADDRESS, for example
config.00.AB.F3.11.73.C8), or generic (config.default). In an environment
with heterogeneous clients, this allows to have a default configuration
suitable for the majority of clients, to have configurations suitable
for a group of clients (for example machines with similar or identical
hardware) and individual configurations for selected machines.

The configuration file contains data about the image and about
configuration, synchronization, and partition parameters.
The configuration file has got the following general format:

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

   The configuration file is sourced by the Bash, so the same quoting
   rules as for the Bash apply.

Not all configuration options needs to be specified. It depends on the
setup of the client which configuration values are required. The
following is a collection of client setup examples which covers all
supported PXE client configurations:

Setup client with remote root
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to serve the image from a remote location and redirect all
write operations on a tmpfs, the following setup is required:

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
with KIWI is populated over the network using either AoE, NBD or NFS
in combination with overlayfs which redirects all write operations
to be local to the client. In any case a setup of either AoE, NBD or
NFS on the image server is required beforehand.

Setup client with system on local disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to deploy the image on a local disk the following setup
is required:

.. code:: bash

   IMAGE="/dev/sda2;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096"
   DISK="/dev/sda"
   PART="5;S;x,x;L;/"

The setup above will create a partition table on sda with a 5MB swap
partition (no mountpoint) and the rest of the disk will be a Linux(L)
partition with / as mountpoint. The (x) in the PART setup specifies
a place holder to indicate the default behaviour.

Setup client with system on local MD RAID disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to deploy the image on a local disk with prior software raid
configuration, the following setup is required:

.. code:: bash

   RAID='1;/dev/sda;/dev/sdb'
   IMAGE="/dev/md1;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096"
   PART="5;S;x,x;L;/"

The first parameter of the RAID line is the raid level. So far only raid1
(mirroring) is supported. The second and third parameter specifies the
raid disk devices which make up the array. If a RAID line is present
all partitions in PART will be created as raid partitions. The first
raid is named md0 the second one md1 and so on. It is required to
specify the correct raid partition in the IMAGE line according to the
PART setup. In this case md0 is reserved for the swap space and md1
is reserved for the system.

Setup loading of custom configuration file(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to load for example a custom /etc/hosts file on the client,
the following setup is required:

.. code:: bash

   CONF="hosts;/etc/hosts;192.168.1.2;4096;ffffffff"

On boot of the client KIWI's boot code will fetch the `hosts` file
from the root of the server (192.168.1.2) with 4k blocksize and deploy
it as `/etc/hosts` on the client. The protocol is by default tftp
but can be changed via the kiwiservertype kernel commandline option.
For details see :ref:`custom-download-server`

Setup client to force reload image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to force the reload of the system image even if the image on
the disk is up-to-date, the following setup is required:

.. code:: bash

   RELOAD_IMAGE=1

The option only applies to configurations with a DISK/PART setup

Setup client to force reload configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to force the reload of all configuration files specified in
CONF, the following setup is required:

.. code:: bash

   RELOAD_CONFIG=1

By default only configuration files which has changed according to
their md5sum value will be reloaded. With the above setup all files
will be reloaded from the PXE server. The option only applies to
configurations with a DISK/PART setup

Setup client for reboot after deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to reboot the system after the initial deployment process is
done the following setup is required:

.. code:: bash

   REBOOT_IMAGE=1

Setup custom kernel boot options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to for example deactivate the kernel mode setting on local
boot of the client the following setup is required:

.. code:: bash

   KIWI_KERNEL_OPTIONS="nomodeset"

.. note::

   This does not influence the kernel options passed to the client
   if it boots from the network. In order to setup those the pxe
   configuration on the PXE server needs to be changed

Setup a custom boot timeout
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to setup a 10sec custom timeout for the local boot of the client
the following setup is required.

.. code:: bash

   KIWI_BOOT_TIMEOUT="10"

.. note::

   This does not influence the boot timeout if the client boots off
   from the network.

.. _custom-download-server:

Setup a different download protocol and server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default all downloads controlled by the KIWI linuxrc code are
performed by an atftp call using the TFTP protocol. With PXE the download
protocol is fixed and thus you cannott change the way how the kernel and
the boot image (initrd) is downloaded. As soon as Linux takes over, the
download protocols http, https and ftp are supported too. KIWI uses
the curl program to support the additional protocols.

To select one of the additional download protocols the following
kernel parameters need to be specified

.. code:: bash

   kiwiserver=192.168.1.1 kiwiservertype=ftp

To set up this parameters edit the file
/srv/tftpboot/pxelinux.cfg/default on your PXE boot server and change
the append line accordingly.

.. note::

   Once configured all downloads except for kernel and initrd are
   now controlled by the given server and protocol. You need to make
   sure that this server provides the same directory and file structure
   as initially provided by the kiwi-pxeboot package
