.. _repositories:

Setting up Repositories
=======================

A crucial part of each appliance is the repository
selection. {kiwi} allows the end user to completely customize the selection
of repositories and packages via the `repository` element.

Adding repositories
-------------------

{kiwi} installs packages into your appliance from the repositories defined in
the image description. Therefore at least one repository **must** be
defined, as {kiwi} will otherwise not be able to fetch any packages.

A repository is added to the description via the `repository` element,
which is a child of the top-level `image` element:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <repository type="rpm-md" alias="kiwi" priority="1">
           <source path="{exc_kiwi_repo}"/>
       </repository>
       <repository type="rpm-md" alias="OS" imageinclude="true">
           <source path="{exc_repo}"/>
       </repository>
   </image>

In the above snippet we defined two repositories:

1. The repository belonging to the {kiwi} project:
   *{exc_kiwi_repo}* at the Open Build Service (OBS)

2. The RPM repository belonging to the OS project:
   *{exc_repo}*, at the Open Build Service (OBS). The translated
   http URL will also be included in the final appliance.

The `repository` element accepts one `source` child element, which
contains the URL to the repository in an appropriate format and the
following optional attributes:

- `imageinclude`: Specify whether this repository should be added to the
  resulting image, defaults to false.

- `imageonly`: A repository with `imageonly="true"` will not be available
  during image build, but only in the resulting appliance. Defaults to
  false.

- `priority`: An integer priority for all packages in this repository. If
  the same package is available in more than one repository, then the one
  with the highest priority is used.

- `alias`: Name to be used for this repository, it will appear as the
  repository's name in the image, which is visible via ``zypper repos`` or
  ``dnf repolist``. {kiwi} will construct an alias from the path in the
  `source` child element (replacing each `/` with a `_`), if no value is
  given.

- `repository_gpgcheck`: Specify whether or not this specific repository is
  configured to to run repository signature validation. If not set, the
  package manager's default is used.

- `package_gpgcheck`: Boolean value that specifies whether each package's
  GPG signature will be verified. If omitted, the package manager's default
  will be used

- `components`: Distribution components used for `deb` repositories,
  defaults to `main`.

- `distribution`: Distribution name information, used for deb repositories.

- `profiles`: List of profiles to which this repository applies.

- `customize`: Script to run custom modifications to the repo file(s).
  repo files allows for several customization options which not all of them
  are supported to be set by kiwi through the current repository schema.
  As the options used do not follow any standard and are not compatible
  between package managers and distributions, the only generic way to handle
  this is through a script hook which is invoked with the repo file as
  parameter for each file created by {kiwi}.

  An example for a script call to add the `module_hotfixes` option
  for a `dnf` compatible repository configuration could look like
  this

  .. code:: bash

     repo_file=$1
     echo 'module_hotfixes = 1' >> ${repo_file}

  .. note::

     If the script is provided as relative path it will
     be searched in the image description directory

.. _supported-repository-paths:

Supported repository paths
^^^^^^^^^^^^^^^^^^^^^^^^^^

The actual location of a repository is specified in the `source` child
element of `repository` via its only attribute `path`. {kiwi} supports the
following paths types:

- `http://URL` or `https://URL` or `ftp://URL`: a URL to the repository
  available via HTTP(s) or FTP.

- `obs://$PROJECT/$REPOSITORY`: evaluates to the repository `$REPOSITORY`
  of the project `$PROJECT` available on the Open Build Service (OBS). By
  default {kiwi} will look for projects on `build.opensuse.org
  <https://build.opensuse.org>`_, but this can be overridden using the
  runtime configuration file (see :ref:`runtime_config`).
  Note that it is not possible to add repositories using the `obs://` path
  from **different** OBS instances (use direct URLs to the :file:`.repo`
  file instead in this case).

- `obsrepositories:/`: special path only available for builds using the
  Open Build Service. The repositories configured for the OBS project in
  which the {kiwi} image resides will be available inside the appliance. This
  allows you to configure the repositories of your image from OBS itself
  and not having to modify the image description.

- `dir:///path/to/directory` or `file:///path/to/file`: an absolute path to
  a local directory or file available on the host building the
  appliance.

- `iso:///path/to/image.iso`: the specified ISO image will be mounted
  during the build of the {kiwi} image and a repository will be created
  pointing to the mounted ISO.
