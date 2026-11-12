.. _kiwi_image_info:

kiwi-ng image info
==================

.. _db_image_info_desc:

Shows information about an image description without building it. The
output always contains the image name, the options add further
information and can be combined. At least one repository is required,
from the image description or from ``--add-repo``.

.. _db_image_info_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] image info --description <directory> [options]

.. _db_image_info_opts:

Options
-------

Options marked with ``...`` can be given multiple times.

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--description <directory>``
     - Required. The image description directory.
   * - ``--list-profiles``
     - List the profiles. If the default image type belongs to a profile,
       or there is no default type, also select that profile with the
       global option ``--profile``.
   * - ``--print-kiwi-env``
     - List the environment variables of the image description scripts,
       see :ref:`image-customization-methods`. Some only get a value
       during a build.
   * - ``--resolve-package-list``
     - Resolve the dependencies and list all packages with source, install
       size, architecture, version, and whether they are listed in the
       image description or added as dependency.
   * - ``--print-xml``
     - Print the image description in XML, converted to the latest schema
       and validated. Use this to update an older image description.
   * - ``--print-yaml``, ``--print-toml``
     - Like ``--print-xml``, in YAML or TOML. Requires the Python module
       `anymarkup`. Only one ``--print-*`` option is applied, XML over
       YAML over TOML.
   * - ``--add-repo <repo>...``
     - Add a repository, see :ref:`db_kiwi_system_build_repo`.
   * - ``--add-repo-credentials <credentials>...``
     - The credentials of ``--add-repo``, matched by order.
   * - ``--ignore-repos``
     - Ignore all repositories of the image description.

.. _db_image_info_example:

Example
-------

.. code:: bash

   $ kiwi-ng image info --resolve-package-list \
       --description kiwi/build-tests/{exc_description_disk}
