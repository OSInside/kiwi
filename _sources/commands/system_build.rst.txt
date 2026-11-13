.. _kiwi_system_build:

kiwi-ng system build
====================

.. _db_kiwi_system_build_desc:

Builds an image in one call by running the prepare and the create step,
see :ref:`working-with-kiwi-image-building-process`. The root tree is
created in :file:`<target-dir>/build/image-root`, the log is written to
:file:`<target-dir>/build/image-root.log` unless ``--logfile`` is given,
and the image files are stored in the target directory.

.. _db_kiwi_system_build_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system build \
       --description <directory> \
       --target-dir <directory> \
       [options]

.. _db_kiwi_system_build_opts:

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
   * - ``--target-dir <directory>``
     - Required. The directory for the build results.
   * - ``--allow-existing-root``
     - Use the root tree of an earlier build instead of stopping with an
       error. The root tree can become inconsistent.
   * - ``--clear-cache``
     - Delete the cache of the used repositories before installing
       packages. The cache is shared between builds, use this if
       signatures must be validated against the repositories.

Repositories
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--set-repo <repo>``
     - Replace the first repository of the image description, see
       `Repository Format`_.
   * - ``--set-repo-credentials <credentials>``
     - The credentials of ``--set-repo``, see `Repository Format`_.
   * - ``--add-repo <repo>...``
     - Add a repository.
   * - ``--add-repo-credentials <credentials>...``
     - The credentials of ``--add-repo``, matched by order.
   * - ``--ignore-repos``
     - Ignore all repositories of the image description. Combine it with
       ``--set-repo`` or ``--add-repo``.
   * - ``--ignore-repos-used-for-build``
     - Like ``--ignore-repos``, but keep the repositories with
       `imageonly="true"`.

Packages
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--add-package <name>...``
     - Install the package in addition to the image description.
   * - ``--add-bootstrap-package <name>...``
     - Install the package in the bootstrap phase.
   * - ``--delete-package <name>...``
     - Uninstall the package, including the packages depending on it,
       right after the packages are installed.

Image Settings
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--set-type-attr <attribute=value>...``
     - Set an attribute of the selected image type, for example
       ``--set-type-attr volid=some``.
   * - ``--set-release-version <version>``
     - Set the `release-version` of the selected image type.
   * - ``--set-container-derived-from <uri>``
     - Replace the base container of the selected type, if the type has
       a `derived_from` attribute.
   * - ``--set-container-tag <name>``
     - Replace the container tag, if the image description sets one.
   * - ``--add-container-label <name=value>...``
     - Add a container label, overwriting a label of the same name.

Keys and Certificates
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--signing-key <key-file>...``
     - Import the key as trusted key into the package manager database
       before any package operation.
   * - ``--ca-cert <cert-file>...``
     - Import the CA certificate into the root tree right after the
       bootstrap phase, for example for proxy servers used by the build.
   * - ``--ca-target-distribution <name>``
     - How the certificates of ``--ca-cert`` and of the image description
       are imported: `suse`, `redhat`, `debian` or `archlinux`.

.. _db_kiwi_system_build_repo:

Repository Format
~~~~~~~~~~~~~~~~~

A `<repo>` value is a comma-separated list of fields. Fields at the end
can be omitted, fields in between left empty:

.. code:: bash

   source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Value
   * - source
     - The location of the repository, see `URI Types`_.
   * - type
     - `apk`, `apt-deb`, `apt-rpm`, `deb-dir`, `mirrors` or `rpm-md`.
   * - alias
     - The name of the repository. Default: a generated unique name.
   * - priority
     - The priority, its meaning depends on the package manager.
   * - imageinclude
     - `true` configures the repository in the image as well.
   * - package_gpgcheck
     - `true` validates the package signatures.
   * - {signing_keys}
     - Signing key URIs in curly brackets, separated by semicolons, for
       example `{file:///keys/a.asc;file:///keys/b.asc}`.
   * - components
     - Debian repositories: the components, separated by spaces.
   * - distribution
     - Debian repositories: the distribution name.
   * - repo_gpgcheck
     - `true` validates the repository signature.
   * - repo_sourcetype
     - `baseurl` (default), `metalink` or `mirrorlist`.

A `<credentials>` value is `user:password`, or the name of a file whose
first line contains it. It is added to the repository source as
`scheme://user:password@location`.

.. _db_kiwi_system_build_uri:

URI Types
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Source
     - Location
   * - ``http://``, ``https://``, ``ftp://``
     - A repository on a server.
   * - ``obs://<project>/<repository>``
     - A repository of the Open Build Service, resolved with the download
       server of the runtime configuration. Default:
       http://download.opensuse.org/repositories.
   * - ``obsrepositories:/``
     - Builds in the Open Build Service only: the repositories of the
       project building the image.
   * - ``dir://<path>``, ``file://<path>``
     - A local directory or file. An absolute path is used as ``dir://``.

.. _db_kiwi_system_build_example:

Example
-------

.. code:: bash

   $ sudo kiwi-ng system build \
       --description kiwi/build-tests/{exc_description_disk} \
       --set-repo {exc_repo_leap} \
       --target-dir /tmp/myimage
