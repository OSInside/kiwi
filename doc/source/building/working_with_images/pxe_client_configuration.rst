.. _pxe_client_config:

PXE Client Setup Configuration
==============================

.. sidebar:: Abstract

   This page provides further information for handling
   vmx images built with KIWI and references the following
   articles:

   * :ref:`build_pxe`

All PXE boot based deployment methods are controlled by configuration files
located in :file:`/srv/tftpboot/KIWI` on the PXE server. Such a configuration
file can either be client-specific (config.MAC_ADDRESS, for example
config.00.AB.F3.11.73.C8), or generic (config.default).

In an environment
with heterogeneous clients, this allows to have a default configuration
suitable for the majority of clients, to have configurations suitable
for a group of clients (for example machines with similar or identical
hardware), and individual configurations for selected machines.

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

   The configuration file is sourced by Bash, so the same quoting
   rules as for Bash apply.

Not all configuration options needs to be specified. It depends on the
setup of the client which configuration values are required. The
following is a collection of client setup examples which covers all
supported PXE client configurations.

Setup Client with Remote Root
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To serve the image from a remote location and redirect all
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

Setup Client with System on Local Disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the image on a local disk the following setup
is required:

.. note::

   In the referenced :file:`suse-leap-42.1-JeOS` XML description the ``pxe``
   type must be changed as follows and the image needs to be
   rebuild:

   .. code:: xml

       <type image="pxe" filesystem="ext3" boot="netboot/suse-leap42.1"/>

.. code:: bash

   IMAGE="/dev/sda2;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096"
   DISK="/dev/sda"
   PART="5;S;X,X;L;/"

The setup above will create a partition table on sda with a 5MB swap
partition (no mountpoint) and the rest of the disk will be a Linux(L)
partition with :file:`/` as mountpoint. The (``X``) in the PART setup specifies
a place holder to indicate the default behaviour.

Setup Client with System on Local MD RAID Disk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the image on a local disk with prior software RAID
configuration, the following setup is required:

.. note::

   In the referenced :file:`suse-leap-42.1-JeOS` XML description the ``pxe``
   type must be changed as follows and the image needs to be
   rebuild:

   .. code:: xml

       <type image="pxe" filesystem="ext3" boot="netboot/suse-leap42.1"/>

.. code:: bash

   RAID='1;/dev/sda;/dev/sdb'
   IMAGE="/dev/md1;LimeJeOS-Leap-42.1.x86_64;1.42.1;192.168.100.2;4096"
   PART="5;S;x,x;L;/"

The first parameter of the RAID line is the RAID level. So far only raid1
(mirroring) is supported. The second and third parameter specifies the
raid disk devices which make up the array. If a RAID line is present
all partitions in ``PART`` will be created as RAID partitions. The first
RAID is named ``md0``, the second one ``md1`` and so on. It is required to
specify the correct RAID partition in the ``IMAGE`` line according to the
``PART`` setup. In this case ``md0`` is reserved for the SWAP space and ``md1``
is reserved for the system.

Setup Loading of Custom Configuration File(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to load for example a custom :file:`/etc/hosts` file on the client,
the following setup is required:

.. code:: bash

   CONF="hosts;/etc/hosts;192.168.1.2;4096;ffffffff"

On boot of the client KIWI's boot code will fetch the :file:`hosts` file
from the root of the server (192.168.1.2) with 4k blocksize and deploy
it as :file:`/etc/hosts` on the client. The protocol is by default tftp
but can be changed via the ``kiwiservertype`` kernel commandline option.
For details, see :ref:`custom-download-server`

Setup Client to Force Reload Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To force the reload of the system image even if the image on
the disk is up-to-date, the following setup is required:

.. code:: bash

   RELOAD_IMAGE=1

The option only applies to configurations with a DISK/PART setup

Setup Client to Force Reload Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To force the reload of all configuration files specified in
CONF, the following setup is required:

.. code:: bash

   RELOAD_CONFIG=1

By default only configuration files which has changed according to
their md5sum value will be reloaded. With the above setup all files
will be reloaded from the PXE server. The option only applies to
configurations with a DISK/PART setup

Setup Client for Reboot After Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To reboot the system after the initial deployment process is
done the following setup is required:

.. code:: bash

   REBOOT_IMAGE=1

Setup custom kernel boot options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deactivate the kernel mode setting on local
boot of the client the following setup is required:

.. code:: bash

   KIWI_KERNEL_OPTIONS="nomodeset"

.. note::

   This does not influence the kernel options passed to the client
   if it boots from the network. In order to setup those the PXE
   configuration on the PXE server needs to be changed

Setup a Custom Boot Timeout
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To setup a 10sec custom timeout for the local boot of the client
the following setup is required.

.. code:: bash

   KIWI_BOOT_TIMEOUT="10"

.. note::

   This does not influence the boot timeout if the client boots off
   from the network.

.. _custom-download-server:

Setup a Different Download Protocol and Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default all downloads controlled by the KIWI linuxrc code are
performed by an atftp call using the TFTP protocol. With PXE the download
protocol is fixed and thus you cannot change the way how the kernel and
the boot image (:file:`initrd`) is downloaded. As soon as Linux takes over, the
download protocols http, https and ftp are supported too. KIWI uses
the curl program to support the additional protocols.

To select one of the additional download protocols the following
kernel parameters need to be specified

.. code:: bash

   kiwiserver=192.168.1.1 kiwiservertype=ftp

To set up this parameters edit the file
:file:`/srv/tftpboot/pxelinux.cfg/default` on your PXE boot server and change
the append line accordingly.

.. note::

   Once configured all downloads except for kernel and initrd are
   now controlled by the given server and protocol. You need to make
   sure that this server provides the same directory and file structure
   as initially provided by the ``kiwi-pxeboot`` package
