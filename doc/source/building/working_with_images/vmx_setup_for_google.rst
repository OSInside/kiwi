.. _setup_for_gce:

KIWI Image Description for Google Compute Engine
================================================

.. sidebar:: Abstract

   This page provides further information for handling
   vmx images built with KIWI and references the following
   articles:

   * :ref:`vmx`

A virtual disk image which is able to boot in the Google Compute Engine
cloud framework has to comply the following constraints:

* KIWI type must be an expandable disk
* Google Compute Engine init must be installed
* Disk size must be set to 10G
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

      <package name="google-compute-engine-init"/>

2. Image Type definition

   To allow the image to be expanded to the configured disk
   geometry of the instance started by Google Compute Engine it is
   suggested to let KIWI's OEM boot code take over that task. It would
   also be possible to try cloud-init's resize module but we found
   conflicts when two cloud init systems, `google-compute-engine-init` and
   `cloud-init` were used together. Thus for now we stick with KIWI's
   boot code which can resize the disk from within the initrd before
   the system gets activated through systemd.

   Update the vmx image type setup to be changed into an expandable
   (oem) type as follows:

   .. code:: xml

      <type image="oem"
            boot="oemboot/suse-leap42.1"
            filesystem="ext4" boottimeout="1"
            kernelcmdline="console=ttyS0,38400n8 net.ifnames=0 NON_PERSISTENT_DEVICE_NAMES=1"
            format="gce"
            bootloader="grub2"
        <size unit="M">10240</size>
        <oemconfig>
          <oem-swap>false</oem-swap>
        </oemconfig>
      </type>

An image built with the above setup can be uploaded into the
Google Compute Engine cloud and registered as image. For further information
on how to upload to Google see: `google-cloud-sdk <https://software.opensuse.org/package/google-cloud-sdk>`_
