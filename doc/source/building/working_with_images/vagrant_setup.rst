.. _setup_vagrant:

KIWI Image Description for Vagrant
==================================

.. sidebar:: Abstract

   This page provides further information for handling
   VMX images built with KIWI and references the following
   article:

   * :ref:`vmx`

`Vagrant <https://www.vagrantup.com>`_ is a framework to
implement consistent processing/testing work environments based on
Virtualization technologies. To run a system, Vagrant needs so-called
**boxes**. A box is a TAR archive containing a virtual disk image and
some metadata.

To build Vagrant boxes, use
`veewee <https://github.com/jedi4ever/veewee>`_ which builds boxes
based on AutoYaST. As an alternative, use `Packer <https://www.packer.io>`_,
which is providedby Vagrant itself.

Both tools are based on the official installation media (DVDs) as shipped
by the distribution vendor.

The KIWI way of building images might be helpful, if such a media does
not exist. For example, if the distribution is still under development or
you want to use a collection of your own repositories.

In addition, you can use the KIWI image description as source for the
`Open Build Service <https://openbuildservice.org>`_ which allows
building and maintaining boxes.

A Vagrant box which is able to work with Vagrant has to comply with the
constraints documented in
`Vagrant Box Constraints <https://www.vagrantup.com/docs/boxes/base.html>`_.
Applied to the referenced KIWI image description from :ref:`vmx`,
the following changes are required:

1. Add mandatory packages

   .. code:: xml

      <package name="sudo"/>
      <package name="openssh"/>
      <package name="rsync"/>

2. Update the image type setup

   .. code:: xml

      <type image="vmx" filesystem="ext4" format="vagrant" boottimeout="0">
          <vagrantconfig provider="libvirt" virtualsize="42"/>
          <size unit="G">42</size>
      </type>

   This modifies the type to build a Vagrant box for the libvirt
   provider including a pre-defined disk size. The disk size is
   optional, but recommended to provide some free space on disk.

3. Add Vagrant user

   .. code:: xml

      <users group='vagrant'>
          <user name='vagrant' password='vh4vw1N4alxKQ' home='/home/vagrant'/>
      </users>

   This adds the **vagrant** user to the system and applies the
   name of the user as the password for login. Change this as you
   see fit.

4. Integrate public SSH key

   Reach out to
   `Insecure Keys <https://github.com/hashicorp/vagrant/tree/master/keys>`_
   for details on this keys. Add the public key to the
   box as overlay file in your image description at
   :file:`home/vagrant/.ssh/authorized_keys`

5. Setup and start SSH daemon

   In :file:`config.sh` add the start of the sshd and the initial
   creation of machine keys as follows:

   .. code:: bash

      #======================================
      # Create ssh machine keys
      #--------------------------------------
      /usr/sbin/sshd-gen-keys-start

      #======================================
      # Activate services
      #--------------------------------------
      suseInsertService sshd

   Also make sure to setup **UseDNS=no** in :file:`etc/ssh/sshd_config`
   This can be done by an overlay file or clever patching of
   the file in the above mentioned :file:`config.sh` file.

6. Configure sudo for Vagrant user

   Add the :file:`etc/sudoers` file to the box as overlay file and make
   sure the user: **vagrant** is configured to allow passwordless root
   permissions.

An image built with the above setup creates a box file with the
extension :file:`.vagrant.libvirt.box`. That box file can now be
added to vagrant with the command:

.. code:: bash

   vagrant box add my-box image-file.vagrant.libvirt.box

.. note::

   Using the box requires a correct Vagrant installation on your machine.
   The libvirtd daemon and the libvirt default network need to be running.

Once added to Vagrant, boot the box and log in
with the following sequence of :command:`vagrant` commands:

.. code:: bash

   vagrant init my-box
   vagrant up --provider libvirt
   vagrant ssh

.. note:: Vagrant Providers

   Currently, KIWI only supports the libvirt provider. There are
   other providers like virtualbox and also vmware available which
   requires a different box layout currently not supported by KIWI.
