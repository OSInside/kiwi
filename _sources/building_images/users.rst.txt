.. _adding-users:

Users
=====

.. sidebar:: Abstract

   This page describes how to add user accounts to an image, or to
   modify existing ones.

User accounts are added or modified with `user` elements in the `users`
section:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <users>
           <user
               password="$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
               home="/root" name="root" groups="root"
           />
           <user
               password="this_is_soo_insecure" pwdformat="plain"
               home="/home/me" name="me" groups="users"
           />
       </users>
   </image>

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Attribute
     - Description
   * - `name`
     - Required. The user name.
   * - `password`
     - Required. The password, encrypted or, with `pwdformat="plain"`,
       in clear text.
   * - `pwdformat`
     - The format of the password: `encrypted` (default) or `plain`.
   * - `home`
     - The home directory.
   * - `groups`
     - A comma-separated list of groups. The first group is the primary
       group, the others are supplementary groups. Without groups, the
       default primary group of the system is used.
   * - `id`
     - The numeric user ID.
   * - `realname`
     - The full name of the user.
   * - `shell`
     - The login shell.

.. tip::

   Anyone with access to the image description can read a plain
   password. Use an encrypted password instead, created for example
   with:

   .. code:: bash

      $ openssl passwd -1 -salt 'xyz' YOUR_PASSWORD
