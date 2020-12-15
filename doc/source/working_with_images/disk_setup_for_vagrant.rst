.. _setup_vagrant:

Image Description for Vagrant
=============================

.. sidebar:: Abstract

   This page provides further information for handling
   Vagrant controlled disk images built with {kiwi} and references
   the following article:

   * :ref:`simple_disk`

`Vagrant <https://www.vagrantup.com>`_ is a framework to
implement consistent processing/testing work environments based on
Virtualization technologies. To run a system, Vagrant needs so-called
**boxes**. A box is a TAR archive containing a virtual disk image and
some metadata.

To build Vagrant boxes, you can use `Packer <https://www.packer.io>`_ which
is provided by Hashicorp itself. Packer is based on the official
installation media (DVDs) as shipped by the distribution vendor.

The {kiwi} way of building images might be helpful, if such a media does not
exist or does not suit your needs. For example, if the distribution is
still under development or you want to use a collection of your own
repositories. Note, that in contrast to Packer {kiwi} only supports the
libvirt and VirtualBox providers. Other providers require a different box
layout that is currently not supported by {kiwi}.

In addition, you can use the {kiwi} image description as source for the
`Open Build Service <https://openbuildservice.org>`_ which allows
building and maintaining boxes.

Vagrant expects boxes to be setup in a specific way (for details refer to
the `Vagrant box documentation
<https://www.vagrantup.com/docs/boxes/base.html>`_.), applied to the
referenced {kiwi} image description from :ref:`simple_disk`, the following
steps are required:

1. Update the image type setup

   .. code:: xml

      <type image="oem" filesystem="ext4" format="vagrant">
          <bootloader name="grub2" timeout="0"/>
          <vagrantconfig provider="libvirt" virtualsize="42"/>
          <size unit="G">42</size>
          <oemconfig>
              <oem-resize>false</oem-resize>
          </oemconfig>
      </type>

   This modifies the type to build a Vagrant box for the libvirt
   provider including a pre-defined disk size. The disk size is
   optional, but recommended to provide some free space on disk.

   For the VirtualBox provider, the additional attribute
   ``virtualbox_guest_additions_present`` can be set to ``true`` when the
   VirtualBox guest additions are installed in the {kiwi} image:

   .. code:: xml

      <type image="oem" filesystem="ext4" format="vagrant">
          <bootloader name="grub2" timeout="0"/>
          <vagrantconfig
            provider="virtualbox"
            virtualbox_guest_additions_present="true"
            virtualsize="42"
          />
          <size unit="G">42</size>
          <oemconfig>
              <oem-resize>false</oem-resize>
          </oemconfig>
      </type>

   The resulting Vagrant box then uses the ``vboxfs`` module for the
   synchronized folder instead of ``rsync``, that is used by default.

2. Add mandatory packages

   .. code:: xml

      <package name="sudo"/>
      <package name="openssh"/>

3. Add additional packages

   If you have set the attribute ``virtualbox_guest_additions_present`` to
   ``true``, add the VirtualBox guest additions. For openSUSE the following
   packages are required:

   .. code:: xml

      <package name="virtualbox-guest-tools"/>
      <package name="virtualbox-guest-x11"/>
      <package name="virtualbox-guest-kmp-default"/>

   Otherwise, you must add ``rsync``:

   .. code:: xml

      <package name="rsync"/>

   Note that {kiwi} cannot verify whether these packages are installed. If
   they are missing, the resulting Vagrant box will be broken.

4. Add Vagrant user

   .. code:: xml

      <users group='vagrant'>
          <user name='vagrant' password='vh4vw1N4alxKQ' home='/home/vagrant'/>
      </users>

   This adds the **vagrant** user to the system and applies the
   name of the user as the password for login.

5. Configure SSH, the default shared folder and sudo permissions

   Vagrant expects that it can login as the user ``vagrant`` using an
   insecure public key [#f1]_. Furthermore, vagrant also usually uses
   :file:`/vagrant` as the default shared folder and assumes that the
   ``vagrant`` user can invoke commands via :command:`sudo` without having
   to enter a password.

   This can be achieved using the function ``baseVagrantSetup`` in
   :file:`config.sh`:

   .. code:: bash

      baseVagrantSetup

6. Additional customizations:

   Additionally to ``baseVagrantSetup``, you might want to also ensure the
   following:

   - If you have installed the Virtualbox guest additions into your box,
     then also load the ``vboxsf`` kernel module.
   - When building boxes for libvirt, then ensure that the default wired
     networking interface is called ``eth0`` and uses DHCP. This is
     necessary since libvirt uses ``dnsmasq`` to issue IPs to the VMs. This
     step can be omitted for Virtualbox boxes.

An image built with the above setup creates a Vagrant box file with the
extension :file:`.vagrant.libvirt.box` or
:file:`.vagrant.virtualbox.box`. Add the box file to Vagrant with the
command:

.. code:: bash

   vagrant box add my-box image-file.vagrant.libvirt.box

.. note::

   Using the box with the libvirt provider requires alongside a correct
   Vagrant installation:

   - the plugin ``vagrant-libvirt`` to be installed
   - a running libvirtd daemon

Once added to Vagrant, boot the box and log in
with the following sequence of :command:`vagrant` commands:

.. code:: bash

   vagrant init my-box
   vagrant up --provider libvirt
   vagrant ssh


Customizing the embedded Vagrantfile
------------------------------------

.. warning:: This is an advanced topic and not required for most users


Vagrant ship with an embedded :file:`Vagrantfile` that carries settings
specific to this box, for instance the synchronization mechanism for the
shared folder. {kiwi} generates such a file automatically for you and it
should be sufficient for most use cases.

If a box requires different settings in the embedded :file:`Vagrantfile`,
then the user can provide {kiwi} with a path to an alternative via the
attribute `embebbed_vagrantfile` of the `vagrantconfig` element: it
specifies a relative path to the :file:`Vagrantfile` that will be included
in the finished box.

In the following example snippet from :file:`config.xml` we add a custom
:file:`MyVagrantfile` into the box (the file should be in the image
description directory next to :file:`config.sh`):

.. code:: xml

   <type image="oem" filesystem="ext4" format="vagrant">
       <bootloader name="grub2" timeout="0"/>
       <vagrantconfig
         provider="libvirt"
         virtualsize="42"
         embedded_vagrantfile="MyVagrantfile"
       />
       <size unit="G">42</size>
       <oemconfig>
           <oem-resize>false</oem-resize>
       </oemconfig>
   </type>


The option to provide a custom :file:`Vagrantfile` can be combined with the
usage of *profiles* (see :ref:`image-profiles`), so that
certain builds can use the automatically generated :file:`Vagrantfile` (in
the following example that is the Virtualbox build) and others get a
customized one (the libvirt profile in the following example):

.. code:: xml

   <?xml version="1.0" encoding="utf-8"?>

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
     <!-- description goes here -->
     <profiles>
       <profile name="libvirt" description="Vagrant Box for Libvirt"/>
       <profile name="virtualbox" description="Vagrant Box for VirtualBox"/>
     </profiles>

     <!-- general preferences go here -->

     <preferences profiles="libvirt">
       <type
         image="oem"
         filesystem="ext4"
         format="vagrant">
           <bootloader name="grub2" timeout="0"/>
           <vagrantconfig
             provider="libvirt"
             virtualsize="42"
             embedded_vagrantfile="LibvirtVagrantfile"
           />
           <size unit="G">42</size>
           <oemconfig>
               <oem-resize>false</oem-resize>
           </oemconfig>
      </type>
      </preferences>
      <preferences profiles="virtualbox">
        <type
          image="oem"
          filesystem="ext4"
          format="vagrant">
            <bootloader name="grub2" timeout="0"/>
            <vagrantconfig
              provider="virtualbox"
              virtualbox_guest_additions_present="true"
              virtualsize="42"
            />
            <size unit="G">42</size>
            <oemconfig>
                <oem-resize>false</oem-resize>
            </oemconfig>
        </type>
      </preferences>

      <!-- remaining box description -->
    </image>


.. [#f1] The insecure key is removed from the box when the it is first
         booted via Vagrant.
