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

To build Vagrant boxes, you can use
`veewee <https://github.com/jedi4ever/veewee>`_ which builds boxes
based on AutoYaST. As an alternative, `Packer <https://www.packer.io>`_ can
be utilized, which is provided by Hashicorp itself.

Both tools are based on the official installation media (DVDs) as shipped
by the distribution vendor.

The KIWI way of building images might be helpful, if such a media does not
exist or does not suit your needs. For example, if the distribution is
still under development or you want to use a collection of your own
repositories.

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
   name of the user as the password for login.

4. Integrate public SSH key

   Vagrant requires an insecure public key pair [#f1]_ to be added to the
   authorized keys for the user ``vagrant`` so that Vagrant itself can
   connect to the box via ssh.
   The key can be obtained from `GitHub
   <https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub>`_
   and should be inserted into the file
   :file:`home/vagrant/.ssh/authorized_keys`, which can be added as an
   overlay file into the image description.

   Keep in mind to set the file system permissions of
   :file:`home/vagrant/.ssh/` and :file:`home/vagrant/.ssh/authorized_keys`
   correctly, otherwise Vagrant will not be able to connect to your
   box. The following snippet can be added to :file:`config.sh`:

   .. code:: bash

      chmod 0600 /home/vagrant/.ssh/authorized_keys
      chown -R vagrant:vagrant /home/vagrant/

5. Create the default shared folder

   Vagrant boxes usually provide a default shared folder under
   :file:`/vagrant`. Consider adding this empty folder to your overlay
   files and ensure that the user ``vagrant`` has write permissions to
   it.

6. Setup and start SSH daemon

   In :file:`config.sh`, add the start of sshd and the initial creation of
   machine keys as follows:

   .. code:: bash

      #======================================
      # Create ssh machine keys
      #--------------------------------------
      /usr/sbin/sshd-gen-keys-start

      #======================================
      # Activate services
      #--------------------------------------
      suseInsertService sshd

   Also make sure to add the line **UseDNS=no** into
   :file:`/etc/ssh/sshd_config`. This can be done by an overlay file or by
   patching the file in the above mentioned :file:`config.sh` file.

7. Configure sudo for the Vagrant user

   Vagrant expects to have passwordless root permissions via ``sudo`` to be
   able to setup your box. Add the following line to :file:`/etc/sudoers`
   or add it into a new file :file:`/etc/sudoers.d/vagrant`:

   .. code::

      vagrant ALL=(ALL) NOPASSWD: ALL

   You can also use :command:`visudo` to verify that the resulting
   :file:`/etc/sudoers` or :file:`/etc/sudoers.d/vagrant` are valid:

   .. code:: bash

      visudo -cf /etc/sudoers
      if [ $? -ne 0 ]; then
          exit 1
      fi


An image built with the above setup creates a box file with the
extension :file:`.vagrant.libvirt.box`. That box file can now be
added to vagrant with the command:

.. code:: bash

   vagrant box add my-box image-file.vagrant.libvirt.box

.. note::

   Using the box requires a correct Vagrant installation on your machine,
   the plugin ``vagrant-libvirt`` to be installed and the libvirtd daemon
   to be running.

Once added to Vagrant, boot the box and log in
with the following sequence of :command:`vagrant` commands:

.. code:: bash

   vagrant init my-box
   vagrant up --provider libvirt
   vagrant ssh

.. note:: Vagrant Providers

   Currently, KIWI only supports the libvirt provider. There are
   also other providers available, like virtualbox and vmware, which
   require a different box layout (currently not supported by KIWI).


.. [#f1] The insecure key is removed from the box when the it is first
         booted via Vagrant.
