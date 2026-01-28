.. _setup_for_gce:

Image Description for Google Compute Engine
===========================================

.. sidebar:: Abstract

   This page provides further information for handling
   GCE images built with {kiwi} and references the following
   articles:

   * :ref:`simple_disk`

A virtual disk image which is able to boot in the Google Compute Engine
cloud framework has to comply the following constraints:

* {kiwi} type must be an expandable disk
* Google Compute Engine init must be installed
* Disk size must be set to 10G
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

      <package name="google-compute-engine-init"/>

2. Image Type definition

   To allow the image to be expanded to the configured disk
   geometry of the instance started by Google Compute Engine it is
   suggested to let {kiwi}'s OEM boot code take over that task. It would
   also be possible to try cloud-init's resize module but we found
   conflicts when two cloud init systems, `google-compute-engine-init` and
   `cloud-init` were used together. Thus for now we stick with {kiwi}'s
   boot code which can resize the disk from within the initrd before
   the system gets activated through systemd.

   Update the oem image type setup to be changed into an expandable
   type as follows:

   .. code:: xml

      <type image="oem"
            initrd_system="dracut"
            filesystem="ext4"
            kernelcmdline="console=ttyS0,38400n8 net.ifnames=0"
            format="gce">
        <bootloader name="grub2" timeout="1"/>
        <size unit="M">10240</size>
        <oemconfig>
            <oem-resize>true</oem-resize>
            <oem-swap>false</oem-swap>
        </oemconfig>
      </type>

An image built with the above setup can be uploaded into the
Google Compute Engine cloud and registered as image. For further information
on how to upload to Google see: `google-cloud-sdk` on software.opensuse.org
