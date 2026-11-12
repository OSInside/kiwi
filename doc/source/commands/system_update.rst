.. _kiwi_system_update:

kiwi-ng system update
=====================

.. _db_kiwi_system_update_desc:

Updates the packages of a root tree created by `kiwi-ng system prepare`
from the repositories of its image description, and optionally adds or
removes packages.

.. _db_kiwi_system_update_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system update --root <directory> [options]

.. _db_kiwi_system_update_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--root <directory>``
     - Required. The root tree to update.
   * - ``--add-package <name>...``
     - Install the package.
   * - ``--delete-package <name>...``
     - Uninstall the package, including the packages depending on it.

.. _db_kiwi_system_update_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system update --root /tmp/myimage/root --add-package vim
