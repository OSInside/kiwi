.. _repositories:

Setting up Repositories
=======================

The repository selection is a crucial part of an appliance. {kiwi} allows the
end user to customize the selection of repositories and packages via
the `repository` element.

Adding repositories
-------------------

{kiwi} installs packages into an appliance from the repositories defined in
the image description. This means that at least one repository **must** be
defined. Otherwise, {kiwi} cannot fetch any packages.

A repository is added to the description via the `repository` element
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

The above example specifies two repositories:

1. The repository belonging to the {kiwi} project:
   *{exc_kiwi_repo}* at the Open Build Service (OBS).

2. The RPM repository belonging to the OS project:
   *{exc_repo}*, at the Open Build Service (OBS). The translated
   http URL is also included in the final appliance.

The `repository` element accepts one `source` child element that
contains the URL of the repository in an correct format along with the
following optional attributes:

- `imageinclude`: Specifies whether the repository should be added to the
  resulting image. Default is false.

- `imageonly`: A repository with `imageonly="true"` is not available
  during image build, but is present in the resulting appliance. Default is
  false.

- `priority`: An integer value for all packages in this repository. If
  the same package is available in more than one repository, then the one
  with the highest priority is used.

- `alias`: Name to use for the repository. It appears as the repository's name
  in the image visible via ``zypper repos`` or ``dnf repolist``. If `alias`` is
  not specified, {kiwi} generates an alias name using hex representation from
  uuid4.

- `repository_gpgcheck`: Specifies whether the repository is
  configured to perform repository signature validation. If not set, the
  package manager's default is used.

- `package_gpgcheck`: Boolean value that specifies whether each package's
  GPG signature is verified. If omitted, the package manager's default
  is used.

- `components`: Distribution components used for `deb` repositories. Default is `main`.

- `distribution`: Distribution name information, used for deb repositories.

- `profiles`: List of profiles to which this repository applies.

- `customize`: Script to run custom modifications to the repo file or files.
  Repo files allow for several customization options, but not all of them
  are supported to be set by kiwi through the current repository schema.
  As the used options do not follow any standard, and they are not compatible
  between package managers and distributions, the only way to handle
  this is through a script hook which is invoked with the repo file as
  parameter for each file created by {kiwi}.

  An example for a script call to add the `module_hotfixes` option
  for a `dnf` compatible repository configuration could look as follows:

  .. code:: bash

     repo_file=$1
     echo 'module_hotfixes = 1' >> ${repo_file}

  .. note::

     If the script is provided as a relative path, it is expected to be found
     in the image description directory:

.. _supported-repository-paths:

Supported repository paths
^^^^^^^^^^^^^^^^^^^^^^^^^^

The actual location of a repository is specified in the `source` child
element of `repository` via its only attribute `path`. {kiwi} supports the
following paths types:

- `http://URL` or `https://URL` or `ftp://URL`: a URL to the repository
  available via HTTP(s) or FTP.

- `obs://$PROJECT/$REPOSITORY`: checks whether the repository `$REPOSITORY`
  of the project `$PROJECT` available on the Open Build Service (OBS). By
  default, {kiwi} looks for projects on `build.opensuse.org
  <https://build.opensuse.org>`_, but this can be overridden using the
  runtime configuration file (see :ref:`runtime_config`).
  Note that it is not possible to add repositories using the `obs://` path
  from **different** OBS instances (use direct URLs to the :file:`.repo`
  file instead in this case).

- `obsrepositories:/`: special path only available for builds using the Open
  Build Service. The repositories configured for the OBS project where the
  {kiwi} image resides are made available inside the appliance. This allows you
  to configure the repositories of your image from OBS itself, without modifying
  the image description.

- `dir:///path/to/directory` or `file:///path/to/file`: an absolute path to
  a local directory or file available on the host building the
  appliance.

- `iso:///path/to/image.iso`: the specified ISO image is mounted
  during the build of the {kiwi} image and a repository is created,
  pointing to the mounted ISO.
