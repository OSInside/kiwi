.. _setup_for_luks:

Image Description Encrypted Disk
================================

.. sidebar:: Abstract

   This page provides further information for handling
   disk images with an encrypted root filesystem setup.
   The information here is based on top of the following
   article:

   * :ref:`simple_disk`

A virtual disk image can be partially or fully encrypted
using the LUKS extension supported by {kiwi}. A fully encrypted
image also includes the data in :file:`/boot` to be encrypted.
Such an image requests the passphrase for the master key
to be entered at the bootloader stage. A partialy encrypted
image keeps :file:`/boot` unencrypted and on an extra boot partition.
Such an image requests the passphrase for the master key later
in the boot process when the root partition gets accessed by
the systemd mount service. In any case the master passphrase
is requested only once.

Update the {kiwi} image description as follows:

1. Software packages

   Make sure to add the following package to the package list

   .. note::

      Package names used in the following list match the
      package names of the SUSE distribution and might be different
      on other distributions.

   .. code:: xml

      <package name="cryptsetup"/>

2. Image Type definition

   Update the oem image type setup as follows

   Full disk encryption including :file:`/boot`:
     .. code:: xml

        <type image="oem" filesystem="ext4" luks="linux" bootpartition="false">
            <oemconfig>
                <oem-resize>false</oem-resize>
            </oemconfig>
        </type>

   Encrypted root partition with an unencrypted extra :file:`/boot` partition:
     .. code:: xml

        <type image="oem" filesystem="ext4" luks="linux" bootpartition="true">
            <oemconfig>
                <oem-resize>false</oem-resize>
            </oemconfig>
        </type>

   .. note::

       The value for the `luks` attribute sets the master passphrase
       for the LUKS keyring. Therefore the XML description becomes
       security critical and should only be readable by trustworthy
       people. Alternatively the credentials information can be
       stored in a key file and referenced as:

       .. code:: xml

          <type luks="file:///path/to/keyfile"/>
