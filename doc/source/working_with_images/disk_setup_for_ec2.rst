.. _setup_for_ec2:

Image Description for Amazon EC2
================================

.. sidebar:: Abstract

   This page provides further information for handling
   Amazon EC2 images built with {kiwi} and references the following
   articles:

   * :ref:`simple_disk`

A virtual disk image which is able to boot in the Amazon EC2
cloud framework has to comply the following constraints:

* Xen tools and libraries must be installed
* cloud-init package must be installed
* cloud-init configuration for Amazon must be provided
* Grub bootloader modules for Xen must be installed
* AWS tools must be installed
* Disk size must be set to 10G
* Kernel parameters must allow for xen console

To meet this requirements add or update the {kiwi} image
description as follows:

1. Software packages

   Make sure to add the following packages to the package list

   .. note::

      Package names used in the following list matches the
      package names of the SUSE distribution and might be different
      on other distributions.

   .. code:: xml

      <package name="aws-cli"/>
      <package name="grub2-x86_64-xen"/>
      <package name="xen-libs"/>
      <package name="xen-tools-domU"/>
      <package name="cloud-init"/>

2. Image Type definition

   Update the oem image type setup as follows

   .. code:: xml

      <type image="oem"
            filesystem="ext4"
            kernelcmdline="console=xvc0 multipath=off net.ifnames=0"
            devicepersistency="by-label"
            firmware="ec2">
        <bootloader name="grub2" timeout="1"/>
        <size unit="M">10240</size>
        <machine xen_loader="hvmloader"/>
        <oemconfig>
            <oem-resize>false</oem-resize>
        </oemconfig>
      </type>

3. Cloud Init setup

   Cloud init is a service which runs at boot time and allows
   to customize the system by activating one ore more cloud init
   modules. For Amazon EC2 the following configuration file
   :file:`/etc/cloud/cloud.cfg` needs to be provided as part of the
   overlay files in your {kiwi} image description

   .. code:: yaml

      users:
        - default

      disable_root: true
      preserve_hostname: false
      syslog_fix_perms: root:root

      datasource_list: [ NoCloud, Ec2, None ]

      cloud_init_modules:
        - migrator
        - bootcmd
        - write-files
        - growpart
        - resizefs
        - set_hostname
        - update_hostname
        - update_etc_hosts
        - ca-certs
        - rsyslog
        - users-groups
        - ssh

      cloud_config_modules:
        - mounts
        - ssh-import-id
        - locale
        - set-passwords
        - package-update-upgrade-install
        - timezone

      cloud_final_modules:
        - scripts-per-once
        - scripts-per-boot
        - scripts-per-instance
        - scripts-user
        - ssh-authkey-fingerprints
        - keys-to-console
        - phone-home
        - final-message
        - power-state-change

      system_info:
        default_user:
          name: ec2-user
          gecos: "cloud-init created default user"
          lock_passwd: True
          sudo: ["ALL=(ALL) NOPASSWD:ALL"]
          shell: /bin/bash
        paths:
          cloud_dir: /var/lib/cloud/
          templates_dir: /etc/cloud/templates/
        ssh_svcname: sshd

An image built with the above setup can be uploaded into the
Amazon EC2 cloud and registered as image. For further information
on how to upload to EC2 see: `ec2uploadimg <https://github.com/SUSE-Enceladus/ec2imgutils>`_
