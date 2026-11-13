.. _kiwi_result_list:

kiwi-ng result list
===================

.. _db_kiwi_result_list_desc:

Lists the results of the last `kiwi-ng system build` or
`kiwi-ng system create` call in a target directory, read from its file
:file:`kiwi.result`. Each build overwrites this file.

.. _db_kiwi_result_list_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] result list --target-dir <directory>

.. _db_kiwi_result_list_opts:

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--target-dir <directory>``
     - Required. The target directory of the build.

.. _db_kiwi_result_list_example:

Example
-------

.. code:: bash

   $ kiwi-ng result list --target-dir /tmp/myimage
