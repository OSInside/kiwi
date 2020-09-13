.. _image-profiles:

Image Profiles
==============

A *profile* is a namespace for additional settings that can be applied by
{kiwi} on top of the default settings (or other profiles), thereby allowing
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

Each profile is declared via the element `profile`, which itself must be a
child of `profiles` and must contain the `name` and `description`
attributes. The `description` is only present for documentation purposes,
`name` on the other hand is used to instruct {kiwi} which profile to build
via the command line. Additionally, one can provide the boolean attribute
`import`, which defines whether this profile should be used by default when
{kiwi} is invoked via the command line.

A profile inherits the default settings which do not belong to any
profile. It applies only to elements that contain the profile in their
`profiles` attribute. The attribute `profiles` expects a comma separated
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

The profile `QEMU` would inherit the settings from `VM` in the above
example.

For further details on the usage of *profiles* see
:ref:`building-build-with-profiles`
