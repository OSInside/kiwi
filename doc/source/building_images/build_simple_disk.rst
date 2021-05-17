.. _simple_disk:

Build a Virtual Disk Image
==========================

.. sidebar:: Abstract

   This page explains how to build a simple disk image.
   It contains how to:

   - define a simple disk image in the image description
   - build a simple disk image
   - run it with QEMU

A simple Virtual Disk Image is a compressed system disk with additional
metadata useful for cloud frameworks like Amazon EC2, Google Compute Engine,
or Microsoft Azure. It is used as the native disk of a system and does
not require an extra installation workflow or a complex first boot setup
procedure which is why we call it a *simple* disk image.

To instruct {kiwi} to build a simple disk image add a `type` element with
`image="oem"` in :file:`config.xml` that has the `oem-resize` feature
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

The following attributes of the `type` element are of special interest
when building simple disk images:

- `format`: Specifies the format of the virtual disk, possible values are:
  `gce`, `ova`, `qcow2`, `vagrant`, `vmdk`, `vdi`, `vhd`, `vhdx` and
  `vhd-fixed`.

- `formatoptions`: Specifies additional format options passed to
  :command:`qemu-img`. `formatoptions` is a comma separated list of format
  specific options in a ``name=value`` format like :command:`qemu-img`
  expects it. {kiwi} will forward the settings from this attribute as a
  parameter to the `-o` option in the :command:`qemu-img` call.

The `bootloader`, `size` and `machine` child-elements of `type` can be
used to customize the virtual machine image further. We describe them in
the following sections: :ref:`disk-bootloader`, :ref:`disk-the-size-element`
and :ref:`disk-the-machine-element`

Once your image description is finished (or you are content with a image
from the :ref:`example descriptions <example-descriptions>` and use one of
them) build the image with {kiwi}:

.. code:: bash

   $ sudo kiwi-ng system build \
        --description kiwi/build-tests/{exc_description_disk_simple} \
        --set-repo {exc_repo_leap} \
        --target-dir /tmp/myimage

The created image will be in the target directory :file:`/tmp/myimage` with
the file extension :file:`.raw`.

The live image can then be tested with QEMU:

.. code:: bash

   $ sudo qemu \
       -drive file={exc_image_base_name_disk_simple}.x86_64-{exc_image_version}.raw,format=raw,if=virtio \
       -m 4096

For further information how to setup the image to work within a cloud
framework see:

* :ref:`setup_for_ec2`
* :ref:`setup_for_azure`
* :ref:`setup_for_gce`

For information how to setup a Vagrant box, see: :ref:`setup_vagrant`.

.. _disk-bootloader:

Setting up the Bootloader of the Image
--------------------------------------

.. code:: xml

   <preferences>
     <bootloader name="grub2"/>
   </preferences>

The `bootloader` element is used to select the bootloader. At the moment
`grub2`, `isolinux`, `zipl` and `grub2_s390x_emu` (a combination of zipl
and a userspace GRUB2) are supported. The special `custom` entry allows
to skip the bootloader configuration and installation and leaves this up
to the user which can be done by using the `editbootinstall` and
`editbootconfig` custom scripts.

In addition to the mandatory name attribute the following optional
attributes are supported:

console="console|gfxterm|serial":
  Specifies the bootloader console. The attribute is available for the
  grub and isolinux bootloader types. By default a graphics console
  setup is used

serial_line="string":
  Specifies the bootloader serial line setup. The setup
  is effective if the bootloader console is set to use
  the serial line. The attribute is available for the grub
  bootloader only

timeout="number":
  Specifies the boot timeout in seconds prior to launching
  the default boot option. By default the timeout is set to 10 seconds. It
  makes sense to set this value to `0` for images intended to be started
  non-interactively (e.g. virtual machines).

timeout_style="countdown|hidden":
  Specifies the boot timeout style to control the way in which
  the timeout interacts with displaying the menu. If set the
  display of the bootloader menu is delayed after the timeout
  expired. In countdown mode an indication of the remaining time
  is displayed. The attribute is available for the grub loader only

targettype="CDL|LDL|FBA|SCSI":
  Specifies the device type of the disk zipl should boot.
  On zFCP devices use `SCSI`, on DASD devices use `CDL` or `LDL` on
  emulated DASD devices use `FBA`. The attribute is available for the
  zipl loader only

.. _disk-the-size-element:

Modifying the Size of the Image
-------------------------------

The `size` child element of `type` specifies the size of the resulting
disk image. The following example shows a image description where 20 GB are
added to the virtual machine image of which 5 GB are left unpartitioned:

.. code:: xml

   <preferences>
     <type image="oem" format="vmdk">
       <size unit="G" additive="true" unpartitioned="5">20</size>
       <oemconfig>
           <oem-resize>false</oem-resize>
       </oemconfig>
     </type>
   </preferences>

The following optional attributes can be used to customize the image size
further:

- `unit`: Defines the unit used for the provided numerical value, possible
  settings are `M` for megabytes and `G` for gigabytes. The default unit
  are megabytes.

- `additive`: boolean value that determines whether the provided value will
  be added to the current image's size (`additive="true"`) or whether it is
  the total size (`additive="false"`). The default is `false`.

- `unpartitioned`: Specifies the image space in the image that will not be
  partitioned. This value uses the same unit as defined in the attribute
  `unit` or the default.


.. _disk-the-machine-element:

Customizing the Virtual Machine
-------------------------------

The `machine` child element of `type` can be used to customize the virtual
machine configuration which is used when the image is run, like the number
of CPUs or the connected network interfaces.

The following attributes are supported by the `machine` element:

- `ovftype`: The OVF configuration type. The Open Virtualization Format is
  a standard for describing virtual appliances and distribute them in an
  archive called Open Virtual Appliance (OVA). The standard describes the
  major components associated with a disk image. The exact specification
  depends on the product using the format.

  Supported values are `zvm`, `powervm`, `xen` and `vmware`.

- `HWversion`: The virtual machine's hardware version (`vmdk` and `ova`
  formats only), see https://kb.vmware.com/s/article/1003746 for further
  details which value to choose.

- `arch`: the VM architecture (`vmdk` format only), possible values are:
  `ix86` (= `i585` and `i686`) and `x86_64`.

- `xen_loader`: the Xen target loader which is expected to load this guest,
  supported values are: `hvmloader`, `pygrub` and `pvgrub`.

- `guestOS`: The virtual guest OS' identification string for the VM (only
  applicable for `vmdk` and `ova` formats, note that the name designation
  is different for the two formats).

- `min_memory`: The virtual machine's minimum memory in MB (`ova` format
  only).

- `max_memory`: The virtual machine's maximum memory in MB (`ova` format
  only).

- `min_cpu`: The virtual machine's minimum CPU count (`ova` format only).

- `max_cpu`: The virtual machine's maximum CPU count (`ova` format only).

- `memory`: The virtual machine's memory in MB (all formats).

- `ncpus`: The umber of virtual CPUs available to the virtual machine (all
  formats).

Additionally, `machine` supports additional child elements that are covered
in the following subsections.

Modifying the VM Configuration Directly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `vmconfig-entry` element is used to add entries directly into the
virtual machine's configuration file. This is currently only supported for
the `vmdk` format where the provided strings are directly pasted into the
:file:`.vmx` file.

The `vmconfig-entry` element has no attributes and can appear multiple
times, the entries are added to the configuration file in the provided
order. Note, that {kiwi} does not check the entries for correctness. {kiwi} only
forwards them.

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
the `vmnic` element. This can be used to add another bridged interface or
to specify the driver which is being used.

Note, that this element is only used for the `vmdk` image format.

In the following example we add a bridged network interface using the
`e1000` driver:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4" format="vmdk">
       <machine memory="4096" guestOS="suse" HWversion="4">
         <vmnic driver="e1000" interface="0" mode="bridged"/>
       </machine>
     </type>
   </preferences>

The `vmnic` element supports the following attributes:

- `interface`: **mandatory** interface ID for the VM's network interface.

- `driver`: optionally the driver which will be used can be specified

- `mac`: this interfaces' MAC address

- `mode`: this interfaces' mode.

Note that {kiwi} will **not** verify the values that are passed to these
attributes, it will only paste them into the appropriate configuration
files.


Specifying Disks and Disk Controllers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `vmdisk` element can be used to customize the disks and disk
controllers for the virtual machine. This element can be specified multiple
times, each time for each disk or disk controller present.

Note that this element is only used for `vmdk` and `ova` image formats.

The following example adds a disk with the ID 0 using an IDE controller:

.. code:: xml

   <preferences>
     <type image="oem" filesystem="ext4" format="vmdk">
       <machine memory="512" guestOS="suse" HWversion="4">
         <vmdisk id="0" controller="ide"/>
       </machine>
     </type>
   </preferences>

Each `vmdisk` element can be further customized via the following optional
attributes:

- `controller`: The disk controller used for the VM guest (`vmdk` format
  only). Supported values are: `ide`, `buslogic`, `lsilogic`, `lsisas1068`,
  `legacyESX` and `pvscsi`.

- `device`: The disk device to appear in the guest (`xen` format only).

- `diskmode`: The disk mode (`vmdk` format only), possible values are:
  `monolithicSparse`, `monolithicFlat`, `twoGbMaxExtentSparse`,
  `twoGbMaxExtentFlat` and `streamOptimized` (see also
  https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.OvfManager.CreateImportSpecParams.DiskProvisioningType.html).

- `disktype`: The type of the disk as it is internally handled by the VM
  (`ova` format only). This attribute is currently unused.

- `id`: The disk ID of the VM disk (`vmdk` format only).

Adding CD/DVD Drives
^^^^^^^^^^^^^^^^^^^^

{kiwi} supports the addition of IDE and SCSCI CD/DVD drives to the virtual
machine using the `vmdvd` element for the `vmdk` image format. In the
following example we add two drives: one with a SCSCI and another with a
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

The `vmdvd` element features just these two **mandatory** attributes:

- `id`: The CD/DVD ID of the drive

- `controller`: The CD/DVD controller used for the VM guest, supported
  values are `ide` and `scsi`.
