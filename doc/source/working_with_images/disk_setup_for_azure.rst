.. _setup_for_azure:

Image Description for Microsoft Azure
=====================================

.. sidebar:: Abstract

   This page provides further information for handling
   Azure disk images built with {kiwi} and references the
   following articles:

   * :ref:`simple_disk`

A virtual disk image which is able to boot in the Microsoft Azure
cloud framework has to comply the following constraints:

* Hyper-V tools must be installed
* Microsoft Azure Agent must be installed
* Disk size must be set to 30G
* Kernel parameters must allow for serial console

To meet this requirements update the {kiwi} image
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

   Update the oem image type setup as follows

   .. code:: xml

      <type image="oem"
            filesystem="ext4"
            kernelcmdline="console=ttyS0 rootdelay=300 net.ifnames=0"
            devicepersistency="by-uuid"
            format="vhd-fixed"
            formatoptions="force_size"
            bootpartition="true"
            bootpartsize="1024">
        <bootloader name="grub2" timeout="1"/>
        <size unit="M">30720</size>
        <oemconfig>
            <oem-resize>false</oem-resize>
        </oemconfig>
      </type>

An image built with the above setup can be uploaded into the
Microsoft Azure cloud and registered as image. For further
information on how to upload to Azure see:
`azurectl <https://github.com/SUSE-Enceladus/azurectl>`_
