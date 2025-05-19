.. _network-boot-server:

Setting Up a Network Boot Server
================================

.. sidebar:: Abstract

   This page provides general information how to setup
   a network boot server that provides all services
   needed for the PXE boot protocol

To be able to deploy a system through the PXE boot protocol, you need
to set up a network boot server providing the services DHCP and tftp.
With `dnsmasq` an utility exists which allows to setup all needed
services at once:

Installing and Configuring DHCP and TFTP with dnsmasq
-----------------------------------------------------

The following instructions can only serve as an example. Depending on your
network structure, the IP addresses, ranges and domain settings needs to
be adapted to allow the DHCP server to work within your network. If you
already have a DHCP server running in your network, make sure that the
`filename` and `next-server` directives are correctly set on this server.

The following steps describe how to set up dnsmasq to work as
DHCP and TFTP server.

1. Install the `dnsmasq` package.

2. Create the file :file:`/etc/dnsmasq.conf` and insert the following content

   .. code:: bash

      # Don't function as a DNS server.
      port=0

      # Log information about DHCP transactions.
      log-dhcp

      # Set the root directory for files available via FTP,
      # usually "/srv/tftpboot":
      tftp-root=TFTP_ROOT_DIR

      enable-tftp

      dhcp-range=BOOT_SERVER_IP,proxy

   In the next step it's required to decide for the boot method. There
   is the PXE loader provided via pxelinux.0 from the syslinux package
   and there is the GRUB loader provided via the grub package.

   .. note:: Placeholders

      Replace all placeholders (written in uppercase) with data fitting
      your network setup.


2.1. insert the following content to use pxelinux.0:

   .. code:: bash

      # The boot filename, Server name, Server Ip Address
      dhcp-boot=pxelinux.0,,BOOT_SERVER_IP

      # Disable re-use of the DHCP servername and filename fields as extra
      # option space. That's to avoid confusing some old or broken
      # DHCP clients.
      dhcp-no-override

      # PXE menu.  The first part is the text displayed to the user.
      # The second is the timeout, in seconds.
      pxe-prompt="Booting FOG Client", 1

      # The known types are x86PC, PC98, IA64_EFI, Alpha, Arc_x86,
      # Intel_Lean_Client, IA32_EFI, BC_EFI, Xscale_EFI and X86-64_EFI
      # This option is first and will be the default if there is no input
      # from the user.
      pxe-service=X86PC, "Boot to FOG", pxelinux.0
      pxe-service=X86-64_EFI, "Boot to FOG UEFI", ipxe
      pxe-service=BC_EFI, "Boot to FOG UEFI PXE-BC", ipxe

   .. note::

      On boot of a network client with that configuration the default
      pxelinux.0 config file is expected at
      :file:`TFTP_ROOT_DIR/pxelinux.cfg/default`

2.2. insert the following content to use grub:

    .. code:: bash

       # The boot filename, Server name, Server Ip Address
       dhcp-boot=boot/grub2/i386-pc/core.0,,BOOT_SERVER_IP

    When using grub the referenced dhcp-boot grub module must be genereated.
    To do this change the directory to :file:`TFTP_ROOT_DIR` and create
    the :file:`setvars.conf` with the following content:

    .. code:: bash

       set root=(tftp)
       set net_default_server=BOOT_SERVER_IP
       set prefix=boot/grub2

    Now call the following commands to create the grub module

    .. code:: bash

       $ grub2-mknetdir --net-directory=TFTP_ROOT_DIR --subdir=boot/grub2
       $ grub2-mkimage -O i386-pc-pxe \
           --output boot/grub2/i386-pc/core.0 \
           --prefix=/boot/grub2 \
           -c setvars.conf \
         pxe tftp

    .. note::

       On boot of a network client with that configuration the grub
       config file is expected at :file:`TFTP_ROOT_DIR/boot/grub2/grub.cfg`

3. Run the dnsmasq server by calling:

   .. code:: bash

       systemctl start dnsmasq
