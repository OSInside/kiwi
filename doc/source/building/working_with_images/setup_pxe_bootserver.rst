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

       $ systemctl start atftpd

Installing and Configuring DHCP
-------------------------------

Contrary to the atftp server setup the following instructions can only
serve as an example. Depending on your network structure, the IP addresses,
ranges and domain settings need to be adapted to allow the DHCP server to
work within your network. If you already have a DHCP server running in your
network, make sure that the filename and next-server are correctly set
in :file:`/etc/dhcpd.conf` on this server.

The following steps describe how to set up a new DHCP server instance:

1. Install the package dnsmasq

2. Create the file :file:`/etc/dnsmasq.conf` and include the
   following statements. Note that all **values** listed
   below are examples, make sure to replace them with data fitting your
   network setup.

   .. code:: bash

       log-dhcp

       expand-hosts
       domain=linux.local
       dhcp-range=192.168.100.5,192.168.100.30,12h
       dhcp-option=3,192.168.100.2
       # nis-domain
       dhcp-option=40,linux.local
       # next-server
       dhcp-option=pxe,66,192.168.100.2
       dhcp-option=option:root-path,"/srv/tftpboot"
       dhcp-option=option:Bootfile-name,"/srv/tftpboot/pxelinux.0"

       # no-dhcp-interface=tun0

       bind-interfaces

3. Run the dnsmasq server by calling:

   .. code:: bash

       systemctl start dnsmasq
