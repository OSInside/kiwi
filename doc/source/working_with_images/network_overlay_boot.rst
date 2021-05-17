.. _network_overlay_boot:

Booting a Root Filesystem from Network
======================================

.. sidebar:: Abstract

   This page provides further information for handling
   KIS images built with {kiwi} and references the following
   article:

   * :ref:`kis`

In {kiwi}, the `kiwi-overlay` dracut module can be used to boot
from a remote exported root filesystem. The exported device
is visible as block device on the network client. {kiwi}
supports the two export backends `NBD` (Network Block Device)
and `AoE` (ATA over Ethernet) for this purpose. A system that is
booted in this mode will read the contents of the root filesystem
from a remote location and targets any write action into RAM by
default. The kernel cmdline option `rd.root.overlay.write` can
be used to specify an alternative device to use for writing.
The two layers (read and write) are combined using the `overlayfs`
filesystem.

For remote boot of a network client, the PXE boot protocol
is used. This functionality requires a network boot server
setup on the system. Details how to setup such a server
can be found in :ref:`network-boot-server`.

Before the KIS image can be build, the following configuration step
is required:

* Create dracut configuration to include the `kiwi-overlay` module

   .. code:: bash

       $ cd kiwi/build-tests/{exc_description_pxe}
       $ mkdir -p root/etc/dracut.conf.d
       $ cd root/etc/dracut.conf.d
       $ echo 'add_dracutmodules+=" kiwi-overlay "' > overlay.conf

Now the KIS image can be build as shown in :ref:`kis`. After the
build, the following configuration steps are required to boot
from the network:

1. Copy initrd/kernel from the KIS build to the PXE server

   The PXE boot process loads the configured kernel and initrd from
   the PXE server. For this reason, the following files must be
   copied to the PXE server as follows:

   .. code:: bash

       $ cp *.initrd.xz /srv/tftpboot/boot/initrd
       $ cp *.kernel /srv/tftpboot/boot/linux

2. Export Root FileSystem to the Network

   Access to the root filesystem is implemented using either the
   AoE or the NBD protocol. This requires the export of the
   root filesystem image as remote block device:

   Export via AoE:
     Install the `vblade` package on the system which is expected
     to export the root filesystem

     .. note::

         Not all versions of AoE are compatible with any kernel. This
         means the kernel on the system exporting the root filesystem image
         must provide a compatible aoe kernel module compared to the
         kernel used inside of the root filesystem image.

     Once done, export the filesystem from the KIS build above as follows:

     .. code:: bash

         $ vbladed 0 1 IFACE {exc_image_base_name}.x86_64-{exc_image_version}

     The above command exports the given filesystem image file as a block
     storage device to the network of the given IFACE. On any machine except
     the one exporting the file, it will appear as :file:`/dev/etherd/e0.1`
     once the :command:`aoe` kernel module was loaded. The two numbers,
     0 and 1 in the above example, classifies a major and minor number which
     is used in the device node name on the reading side, in this
     case :file:`e0.1`.

     .. note::

         Only machines in the same network of the given INTERFACE
         can see the exported block device.

   Export via NBD:
     Install the `nbd` package on the system which is expected
     to export the root filesystem

     Once done, export the filesystem from the KIS build above as follows:

     .. code:: bash

         $ losetup /dev/loop0 {exc_image_base_name}.x86_64-{exc_image_version}

         $ vi /etc/nbd-server/config

           [generic]
               user = root
               group = root
           [export]
               exportname = /dev/loop0

         $ nbd-server

3. Setup boot entry in the PXE configuration

   .. note::

       The following step assumes that the pxelinux.0 loader
       has been configured on the boot server to boot up network
       clients

   Edit the file :file:`/srv/tftpboot/pxelinux.cfg/default` and create
   a boot entry of the form:

   Using NBD:
     .. code:: bash

         LABEL Overlay-Boot
             kernel boot/linux
             append initrd=boot/initrd root=overlay:nbd=server-ip:export

     The boot parameter `root=overlay:nbd=server-ip:export` specifies
     the NBD server IP address and the name of the export as used in
     :file:`/etc/nbd-server/config`

   Using AoE:
     .. code:: bash

         LABEL Overlay-Boot
             kernel boot/linux
             append initrd=boot/initrd root=overlay:aoe=AOEINTERFACE

     The boot parameter `root=overlay:aoe=AOEINTERFACE` specifies the
     interface name as it was exported by the :command:`vbladed` command

4. Boot from the Network

   Within the network which has access to the PXE server and the
   exported root filesystem image, any network client can now boot the
   system. A test based on QEMU can be done as follows:

   .. code:: bash

      $ sudo qemu -boot n
