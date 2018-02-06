.. _pxe-boot-server:

Setting Up a Network Boot Server
================================

.. sidebar:: Abstract

   This page provides further information for handling
   PXE images built with KIWI and references the following
   articles:

   * :ref:`build_pxe`

To be able to deploy PXE bot images created with KIWI, you need to
set up a network boot server providing the services DHCP and atftp.

Installing and Configuring atftp
--------------------------------

1. Install the packages atftp and kiwi-pxeboot.

2. Edit the file :file:`/etc/sysconfig/atftpd`. Set or modify the following variables:

   .. code:: bash

       ATFTPD_OPTIONS="--daemon --no-multicast"
       ATFTPD_DIRECTORY="/srv/tftpboot"

3. Start the atftpd service by calling:

   .. code:: bash

       $ systemctl start atftpd.socket
       $ systemctl start atftpd

Installing and Configuring DHCP
-------------------------------

Contrary to the atftp server setup the following instructions can only
serve as an example. Depending on your network structure, the IP addresses,
ranges and domain settings need to be adapted to allow the DHCP server to
work within your network. If you already have a DHCP server running in your
network, make sure that the `filename` and `next-server` directives are
correctly set on this server.

The following steps describe how to set up a new DHCP server instance
using dnsmasq:

1. Install the `dnsmasq` package.

2. Create the file :file:`/etc/dnsmasq.conf` and insert
   the following content:

   .. note:: Placeholders

      Replace all placeholders (written in uppercase) with data fitting
      your network setup.

   .. code:: bash

       # Don't function as a DNS server:
       port=0

       # Log lots of extra information about DHCP transactions.
       log-dhcp

       # Set the root directory for files available via FTP,
       # usually "/srv/tftpboot":
       tftp-root=TFTP_ROOT_DIR

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

       dhcp-range=BOOT_SERVER_IP,proxy

3. Run the dnsmasq server by calling:

   .. code:: bash

       systemctl start dnsmasq
