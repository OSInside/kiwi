.. _grub_authorization:

Authorized access to boot menu entries
======================================

.. sidebar:: Abstract

    This page provides information how to configure the GRUB boot laoder
    to allow authorized access to its boot menu entries


You can configure &grub; to allow access to boot menu entries depending
on the level of authorization. You can configure multiple user accounts
protected with passwords and assign them access to different menu entries.
To configure authorization in GRUB;, follow these steps:

1. Create and encrypt one password for each user account you want to use in
   GRUB. Use the `grub2-mkpasswd-pbkdf2`:

   .. code-block:: bash

   $ sudo grub2-mkpasswd-pbkdf2
   Password: ****
   Reenter password: ****
   PBKDF2 hash of your password is grub.pbkdf2.sha512.10000.9CA4611006F77A...

2. Delete the content of the `/etc/grub.d/10_linux` file and save it.
   This prevents outputting the default GRUB menu entries.

3. Edit the `/boot/grub2/custom.cfg` file and add custom
   menu entries manually. The following template is just an example, adjust
   it to better match your use case:

   .. code-block:: bash

   set superusers=admin
   password admin ADMIN_PASSWORD
   password maintainer MAINTAINER_PASSWORD

   menuentry 'Operational mode' {
     insmod ext2
     set root=hd0,1
     echo 'Loading Linux ...'
     linux /boot/vmlinuz root=/dev/vda1 $GRUB_CMDLINE_LINUX_DEFAULT $GRUB_CMDLINE_LINUX mode=operation
     echo 'Loading Initrd ...'
     initrd /boot/initrd
   }

   menuentry 'Maintenance mode' --users maintainer {
     insmod ext2
     set root=hd0,1
     echo 'Loading Linux ...'
     linux /boot/vmlinuz root=/dev/vda1 $GRUB_CMDLINE_LINUX_DEFAULT $GRUB_CMDLINE_LINUX mode=maintenance
     echo 'Loading Initrd ...'
     initrd /boot/initrd
   }

4. Import the changes into the main configuration file:

     .. code-block:: bash

     $ sudo grub2-mkconfig -o /boot/grub2/grub.cfg

In the above example:

* The GRUB menu has two entries, *Operational mode* and *Maintenance mode*.
* If no user is specified, both boot menu entries are accessible, but
  no one can access GRUB command line nor edit existing menu entries.
* `admin` user can access GRUB command line and edit existing menu entries.
* `maintenance` user can select the recovery menu item.
