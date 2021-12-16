Host Security Settings Conflicts with KIWI
==========================================

.. note:: **Abstract**

   This page provides further information how to solve
   image build problems caused by `selinux` security
   policies.

Linux systems are protected against write/read or other
operations depending on the application which wants to
access or modify data. The rules for this protection are
provided in security policies. There are several applications
enforcing these security settings, e.g `apparmor` or `selinux`.
In this troubleshooting chapter the focus is set on `selinux`

Protecting files, process groups, kernel filesystems, device
nodes and more from unauthorized access and restrict it to
a certain set of applications is a nice concept. However, if
taken serious no other application except the ones configured
in the security policy will function properly.

When building an appliance, the appliance builder has to have
access to a wide range of services. It must be able to
create a new package database elsewhere in the system. It must
be able to create, read and write device nodes, create filesystems,
partitions, bootloader configurations etc etc. The list is very
long and no security policy could cover this in a way that it
would not be open to everything which in the end leads to a
pointless exercise and no security at all.

This means for users who would like to keep the security settings
of the system enforced and unchanged, the only way to allow {kiwi}
to do its job is to run it through `boxbuild` as explained in
:ref:`self_contained`

For users who can afford to open the system security policy,
the following procedure will make {kiwi} to work:

.. code:: bash

   sudo setenforce 0

This action disables selinux temporary. To disable selinux
permanently perform the following steps:

1. Open the SELinux configuration file: :file:`/etc/selinux/config`
2. Locate the following line: `SELINUX=enforcing`
3. Change the value to disabled:

   .. code:: bash

       SELINUX=disabled

4. On the next reboot, SELinux is permanently disabled.

.. note::

   similar instructions applies to other application security
   subsystems like `apparmor`. Due to the complexity of these
   systems this article just mentions the most common issue
   people run into when building images on systems protected
   through `selinux`.
