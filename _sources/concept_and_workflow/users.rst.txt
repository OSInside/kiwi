.. _adding-users:

Adding Users
============

User accounts can be added or modified via the `users` element that
supports a list of multiple `user` child elements:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <users>
           <user
               password="this_is_soo_insecure"
               home="/home/me" name="me"
               groups="users" pwdformat="plain"
           />
           <user
               password="$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
               home="/root" name="root" groups="root"
           />
       </users>
   </image>

Each `user` element represents a specific added or modified user.
The following attributes are mandatory:

- `name`: the UNIX username

- `password`: The password for the user account. It can be provided either
  in clear-text form (`pwdformat="plain"`) or in encrypted form
  (`pwdformat="encrypted"`). Using lain passwords is not advisable, as anyone
  with access to the image description can see the password. It is
  recommended to generate a hash of your password using `openssl` as
  follows:

  .. code:: bash

     $ openssl passwd -1 -salt 'xyz' YOUR_PASSWORD

Additionally, the following optional attributes can be specified:

- `home`: the path to the user's home directory

- `groups`: A comma-separated list of UNIX groups. The first element of the
  list is used as the user's primary group. The remaining elements are
  appended to the user's supplementary groups. When no groups are assigned,
  the system's default primary group is be used.

- `id`: The numeric user ID of the account.

- `pwdformat`: The format in which `password` is provided, either `plain`
  or `encrypted` (the latter is the default).
