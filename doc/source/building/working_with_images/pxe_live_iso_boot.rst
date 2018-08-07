.. _pxe_live_boot:

Booting a Live ISO Image from Network
=====================================

.. sidebar:: Abstract

   This page provides further information for handling
   ISO images built with KIWI and references the following
   articles:

   * :ref:`hybrid_iso`

In KIWI, live ISO images can be configured to boot via PXE.
This functionality requires a network boot server setup on the
system. Details how to setup such a server can be found in
:ref:`pxe-boot-server`.

After the live ISO was built as shown in :ref:`hybrid_iso`,
the following configuration steps are required to boot from
the network:

1. Extract initrd/kernel From Live ISO

   The PXE boot process loads the configured kernel and initrd from
   the PXE server. For this reason, those two files must be extracted
   from the live ISO image and copied to the PXE server as follows:
   
   .. code:: bash

       $ mount LimeJeOS-Leap-42.3.x86_64-1.42.3.iso /mnt
       $ cp /mnt/boot/x86_64/loader/initrd /srv/tftpboot/boot/initrd
       $ cp /mnt/boot/x86_64/loader/linux /srv/tftpboot/boot/linux
       $ umount /mnt

   .. note::

       This step must be repeated with any new build of the live ISO image

2. Export Live ISO To The Network

   Access to the live ISO file is implemented using the AoE protocol
   in KIWI. This requires the export of the live ISO file as remote
   block device which is typically done with the :command:`vblade`
   toolkit. Install the following package on the system which is
   expected to export the live ISO image:

   .. code:: bash

       $ zypper in vblade

   .. note::

       Not all versions of AoE are compatible with any kernel. This
       means the kernel on the system exporting the live ISO image
       must provide a compatible aoe kernel module compared to the
       kernel used in the live ISO image.
   
   Once done, export the live ISO image as follows:

   .. code:: bash

       $ vbladed 0 1 INTERFACE LimeJeOS-Leap-42.3.x86_64-1.42.3.iso

   The above command exports the given ISO file as a block storage
   device to the network of the given INTERFACE. On any machine
   except the one exporting the file, it will appear as
   :file:`/dev/etherd/e0.1` once the :command:`aoe` kernel module
   was loaded. The two numbers, 0 and 1 in the above example, classifies
   a major and minor number which is used in the device node name
   on the reading side, in this case :file:`e0.1`. The numbers given
   at export time must match the AOEINTERFACE name as described in
   the next step.

   .. note::

       Only machines in the same network of the given INTERFACE
       can see the exported live ISO image. If virtual machines
       are the target to boot the live ISO image they could all
       be connected through a bridge. In this case INTERFACE
       is the bridge device. The availability scope of the live
       ISO image on the network is in general not influenced
       by KIWI and is a task for the network administrators.

3. Setup live ISO boot entry in PXE configuration

   Edit the file :file:`/srv/tftpboot/pxelinux.cfg/default` and create
   a boot entry of the form:

   .. code:: bash

      LABEL Live-Boot
          kernel boot/linux
          append initrd=boot/initrd rd.kiwi.live.pxe root=live:AOEINTERFACE=e0.1

   * The boot parameter `rd.kiwi.live.pxe` tells the KIWI boot process to
     setup the network and to load the required :mod:`aoe` kernel module.

   * The boot parameter `root=live:AOEINTERFACE=e0.1` specifies the
     interface name as it was exported by the :command:`vbladed` command
     from the last step. Currently only AoE (Ata Over Ethernet)
     is supported.

4. Boot from the Network

   Within the network which has access to the PXE server and the
   exported live ISO image, any network client can now boot the
   live system. A test based on QEMU is done as follows:

   .. code:: bash

      $ qemu -boot n
