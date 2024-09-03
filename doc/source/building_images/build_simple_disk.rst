.. _simple_disk:

Build a Virtual Disk Image
==========================

.. sidebar:: Abstract

   This page explains how to build a simple disk image.
   It covers the following topics:

   - define a simple disk image in the image description
   - build a simple disk image
   - run it with QEMU

A simple virtual disk image is a compressed system disk with additional
metadata useful for cloud frameworks like Amazon EC2, Google Compute Engine,
or Microsoft Azure. It is used as the native disk of a system, and it does
not require an additional installation workflow or a complex first boot setup
procedure.

To enable {kiwi} to build a simple disk image, add a `type` element with
`image="oem"` in :file:`config.xml`, where the `oem-resize` option
disabled. An example configuration for a 42 GB large VMDK image with
512 MB RAM, an IDE controller and a bridged network interface is shown
below:

.. code:: xml

   <image schemaversion="{schema_version}" name="Tumbleweed_appliance">
     <!-- snip -->
     <preferences>
       <type image="oem" filesystem="ext4" format="vmdk">
         <bootloader name="grub2" timeout="0"/>
         <size unit="G">42</size>
         <oemconfig>
             <oem-resize>false</oem-resize>
         </oemconfig>
         <machine memory="512" guestOS="suse" HWversion="4">
           <vmdisk id="0" controller="ide"/>
           <vmnic driver="e1000" interface="0" mode="bridged"/>
         </machine>
       </type>
       <!-- additional preferences -->
     </preferences>
     <!-- snip -->
   </image>

The following attributes of the `type` element are deserve attention
when building simple disk images:

- `format`: Specifies the format of the virtual disk, possible values are:
  `gce`, `ova`, `qcow2`, `vagrant`, `vmdk`, `vdi`, `vhd`, `vhdx` and
  `vhd-fixed`.

- `formatoptions`: Specifies additional format options passed to
  :command:`qemu-img`. `formatoptions` is a comma-separated list of format
  specific options in a ``name=value`` format as expected by
  :command:`qemu-img`. {kiwi} forwards the settings from the attribute as a
  parameter to the `-o` option in the :command:`qemu-img` call.

The `bootloader`, `size` and `machine` child-elements of `type` can be
used to customize the virtual machine image. These elements are described in
the following sections: :ref:`disk-bootloader`, :ref:`disk-the-size-element`
and :ref:`disk-the-machine-element`

Once your image description is finished , you can build the image using the
following {kiwi} command:

.. code:: bash

   $ sudo kiwi-ng system build \
        --description kiwi/build-tests/{exc_description_disk_simple} \
        --set-repo {exc_repo_leap} \
        --target-dir /tmp/myimage

The resulting :file:`.raw` image is stored in :file:`/tmp/myimage`.

You can test the image using QEMU:

.. code:: bash

   $ sudo qemu \
       -drive file={exc_image_base_name_disk_simple}.x86_64-{exc_image_version}.raw,format=raw,if=virtio \
       -m 4096

For further information on how to configure the image to work within a cloud
framework see:

* :ref:`setup_for_ec2`
* :ref:`setup_for_azure`
* :ref:`setup_for_gce`

For information on how to setup a Vagrant system, see: :ref:`setup_vagrant`.

.. _disk-bootloader:

Setting up the Bootloader in the Image
--------------------------------------

.. code:: xml

   <preferences>
     <type>
        <bootloader name="grub2"/>
     </type>
   </preferences>

The `bootloader` element defines which bootloader to use in the
image, and the element offers several options for customizing its configuration.

For details, see: :ref:`preferences-type-bootloader`

.. _disk-the-size-element:

Modifying the Size of the Image
-------------------------------

The `size` child element of `type` specifies the size of the resulting
disk image. The following example shows an image description, where 20 GB are
added to the virtual machine image, of which 5 GB are left unpartitioned:

.. code:: xml

   <preferences>
     <type image="oem" format="vmdk">
       <size unit="G" additive="true" unpartitioned="5">20</size>
       <oemconfig>
           <oem-resize>false</oem-resize>
       </oemconfig>
     </type>
   </preferences>

The following optional attributes can be used to futher customize the image size:

- `unit`: Defines the unit used for the provided numerical value, possible
  values are `M` for megabytes and `G` for gigabytes. The default unit
  is megabytes.

- `additive`: Boolean value that determines whether the provided value is added
  to the current image size (`additive="true"`) or whether it is the total size
  (`additive="false"`). The default value is `false`.

- `unpartitioned`: Specifies the image space in the image that is not
  partitioned. The attribute uses either the same unit as defined in the attribute
  `unit` or the default value.


.. _disk-the-machine-element:

Customizing the Virtual Machine
-------------------------------

The `machine` child element of `type` can be used to customize the virtual
machine configuration, including the number of CPUs and the connected network
interfaces.

The following attributes are supported by the `machine` element:

- `ovftype`: The OVF configuration type. The Open Virtualization Format is a
  standard for describing virtual appliances and distribute them in an archive
  called Open Virtual Appliance (OVA). The standard describes the major
  components associated with a disk image. The exact specification depends on
  the product using the format. Supported values are `zvm`, `powervm`, `xen` and
  `vmware`.

- `HWversion`: The virtual machine's hardware version (`vmdk` and `ova`
  formats only), refer https://kb.vmware.com/s/article/1003746 for further
  information on which value to choose.

- `arch`: the VM architecture (`vmdk` format only). Valid values are
  `ix86` (= `i585` and `i686`) and `x86_64`.

- `xen_loader`: the Xen target loader which is expected to load the guest.
  Valid values are: `hvmloader`, `pygrub` and `pvgrub`.

- `guestOS`: The virtual guest OS' identification string for the VM (only
  applicable for `vmdk` and `ova` formats. Note that the name designation
  is different for the two formats).
  Note: For vmware ovftools, guestOS is a VMX GuestOS, but not VIM GuestOS.
  For instance, correct value for Ubuntu 64 bit is "ubuntu-64", but not
  "ubuntu64Guest". See GUEST_OS_KEY_MAP in guest_os_tables.h at
  https://github.com/vmware/open-vm-tools for another guestOS values.

- `min_memory`: The virtual machine's minimum memory in MB (`ova` format
  only).

- `max_memory`: The virtual machine's maximum memory in MB (`ova` format
  only).

- `min_cpu`: The virtual machine's minimum CPU count (`ova` format only).

- `max_cpu`: The virtual machine's maximum CPU count (`ova` format only).

- `memory`: The virtual machine's memory in MB (all formats).

- `ncpus`: The number of virtual CPUs available to the virtual machine (all
  formats).

`machine` also supports additional child elements that are covered in the following
subsections.

Modifying the VM Configuration Directly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `vmconfig-entry` element is used to add entries directly into the
virtual machine's configuration file. This is currently only supported for
the `vmdk` format where the provided strings are directly pasted into the
:file:`.vmx` file.

The `vmconfig-entry` element has no attributes and can appear multiple
times. The entries are added to the configuration file in the provided
order. Note that {kiwi} does not check the entries for correctness.

The following example adds the two entries `numvcpus = "4"` and
`cpuid.coresPerSocket = "2"` into the VM configuration file:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4" format="vmdk">
       <machine memory="512" guestOS="suse" HWversion="4">
         <vmconfig-entry>numvcpus = "4"</vmconfig-entry>
         <vmconfig-entry>cpuid.coresPerSocket = "2"</vmconfig-entry>
       </machine>
     </type>
   </preferences>

Adding Network Interfaces to the VM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Network interfaces can be explicitly specified for the VM when required via
the `vmnic` element. This makes is possible to add another bridged interface or
to specify the driver wto be used.

Note that this element is used for the `vmdk` image format only.

The following example adds a bridged network interface that uses the `e1000`
driver:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4" format="vmdk">
       <machine memory="4096" guestOS="suse" HWversion="4">
         <vmnic driver="e1000" interface="0" mode="bridged"/>
       </machine>
     </type>
   </preferences>

The `vmnic` element supports the following attributes:

- `interface`: **Mandatory** interface ID for the VM's network interface.

- `driver`: An optional driver.

- `mac`: The MAC address of the specified interface.

- `mode`: The mode of the interface.

Note that {kiwi} doesn **not** verify the values of the
attributes, it only inserts them into the appropriate configuration
files.


Specifying Disks and Disk Controllers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `vmdisk` element can be used to customize the disks and disk controllers for
the virtual machine. This element can be specified for each disk or disk
controller present.

Note that this element is used for `vmdk` and `ova` image formats only.

The following example adds a disk with the ID 0 that uses an IDE controller:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4" format="vmdk">
       <machine memory="512" guestOS="suse" HWversion="4">
         <vmdisk id="0" controller="ide"/>
       </machine>
     </type>
   </preferences>

Each `vmdisk` element can be further customized using optional
attributes:

- `controller`: The disk controller used for the VM guest (`vmdk` format
  only). Supported values are: `ide`, `buslogic`, `lsilogic`, `lsisas1068`,
  `legacyESX` and `pvscsi`.

- `device`: The disk device to appear in the guest (`xen` format only).

- `diskmode`: The disk mode (`vmdk` format only). Valid values are
  `monolithicSparse`, `monolithicFlat`, `twoGbMaxExtentSparse`,
  `twoGbMaxExtentFlat` and `streamOptimized` (see also
  https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.OvfManager.CreateImportSpecParams.DiskProvisioningType.html).

- `disktype`: The type of the disk handled internally by the VM
  (`ova` format only). This attribute is currently unused.

- `id`: The disk ID of the VM disk (`vmdk` format only).

Adding CD/DVD Drives
^^^^^^^^^^^^^^^^^^^^

{kiwi} supports adding IDE and SCSCI CD/DVD drives to the virtual
machine using the `vmdvd` element for the `vmdk` image format. The
following example adds two drives: one with a SCSCI and another with a
IDE controller:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4">
       <machine memory="512" xen_loader="hvmloader">
         <vmdvd id="0" controller="scsi"/>
         <vmdvd id="1" controller="ide"/>
       </machine>
     </type>
   </preferences>

The `vmdvd` element features two **mandatory** attributes:

- `id`: The CD/DVD ID of the drive.

- `controller`: The CD/DVD controller used for the VM guest. Valid
  values are `ide` and `scsi`.
