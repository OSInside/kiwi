.. _setup_for_azure:

KIWI Image Description for Microsoft Azure
==========================================

.. sidebar:: Abstract

   This page provides further information for handling
   vmx images built with KIWI and references the following
   articles:

   * :ref:`vmx`

A virtual disk image which is able to boot in the Microsoft Azure
cloud framework has to comply the following constraints:

* Hyper-V tools must be installed
* Microsoft Azure Agent must be installed
* Disk size must be set to 30G
* Kernel parameters must allow for serial console

To meet this requirements update the KIWI image
description as follows:

1. Software packages

   Make sure to add the following packages to the package list

   .. note::
 
      Package names used in the following list matches the
      package names of the SUSE distribution and might be different
      on other distributions.

   .. code:: xml

      <package name="hyper-v"/>
      <package name="python-azure-agent"/>

2. Image Type definition

   Update the vmx image type setup as follows

   .. code:: xml

      <type image="vmx"
            initrd_system="dracut"
            filesystem="ext4"
            boottimeout="1"
            kernelcmdline="console=ttyS0 rootdelay=300 net.ifnames=0"
            devicepersistency="by-uuid"
            format="vhd-fixed"
            formatoptions="force_size"
            bootloader="grub2"
            bootpartition="true"
            bootpartsize="1024">
        <size unit="M">30720</size>
      </type>

An image built with the above setup can be uploaded into the
Microsoft Azure cloud and registered as image. For further information
on how to upload to Azure see: `azurectl <https://github.com/SUSE/azurectl>`_
