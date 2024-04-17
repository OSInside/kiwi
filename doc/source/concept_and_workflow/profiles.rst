.. _image-profiles:

Image Profiles
==============

A *profile* is a namespace for additional settings that can be applied by
{kiwi} in addition to the default settings (or other profiles), making it possible
to build multiple appliances with the same build type but with different
configurations.

The use of profiles is advisable to distinguish image builds of the same
type but with different settings. In the following example, two virtual
machine images of the `oem` type are configured: one for QEMU (using the
`qcow2` format) and one for VMWare (using the `vmdk` format).

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <profiles>
           <profile name="QEMU" description="virtual machine for QEMU"/>
           <profile name="VMWare" description="virtual machine for VMWare"/>
       </profiles>
       <preferences>
           <version>15.0</version>
           <packagemanager>zypper</packagemanager>
       </preferences>
       <preferences profiles="QEMU">
           <type image="oem" format="qcow2" filesystem="ext4">
       </preferences>
       <preferences profiles="VMWare">
           <type image="oem" format="vmdk" filesystem="ext4">
       </preferences>
   </image>

Each profile is declared via the element `profile` that must be a
child of `profiles`, and it must contain the `name` and `description`
attributes. The `description` is only present for documentation purposes,
`name`, on the other hand, is used to instruct {kiwi} which profile to build
via the command line. Additionally, you can provide the boolean attribute
`import`, which defines whether this profile should be used by default when
{kiwi} is invoked via the command line.

A profile inherits the default settings that do not belong to any
profile. It applies only to elements that contain the profile in their
`profiles` attribute. The attribute `profiles` expects a comma-separated
list of profiles for which the settings of this element apply.

Profiles can furthermore inherit settings from another profile via the
`requires` sub-element:

.. code:: xml

   <profiles>
       <profile name="VM" description="virtual machine"/>
       <profile name="QEMU" description="virtual machine for QEMU">
           <requires profile="VM"/>
       </profile>
   </profiles>

In the above example, the profile `QEMU` inherit the settings from `VM`.

For further details on the usage of *profiles*, see
:ref:`building-build-with-profiles`
