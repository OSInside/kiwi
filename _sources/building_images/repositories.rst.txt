.. _repositories:

Repositories
============

.. sidebar:: Abstract

   This page describes how to add the repositories {kiwi} installs the
   packages of the image from.

{kiwi} installs the packages of an image from the repositories of the
image description, at least one repository is required. Each repository
is a `repository` element with a `source` child element, which holds
the location of the repository in its `path` attribute:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <repository type="rpm-md" alias="kiwi" priority="1">
           <source path="{exc_kiwi_repo}"/>
       </repository>
       <repository type="rpm-md" alias="OS" imageinclude="true">
           <source path="{exc_repo_obs}"/>
       </repository>
   </image>

The example adds the {kiwi} repository and the repository of the
operating system, both from the Open Build Service. The repository of
the operating system is also configured in the resulting image.

The `repository` element supports the following optional attributes:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Attribute
     - Description
   * - `alias`
     - The name of the repository, shown for example by `zypper repos`
       or `dnf repolist`. Without it, {kiwi} generates a name.
   * - `priority`
     - The priority of the repository if a package is available in more
       than one repository. zypper and dnf prefer the *lower* value, apt
       prefers the *higher* value, see `apt_preferences(5)`.
   * - `imageinclude`
     - `true` configures the repository in the resulting image as well.
       The default is `false`.
   * - `imageonly`
     - `true` configures the repository only in the resulting image, it
       is not used for the build. The default is `false`.
   * - `repository_gpgcheck`
     - `true` validates the signature of the repository. The default is
       `false`.
   * - `package_gpgcheck`
     - `true` validates the signature of each package from the
       repository. The default is `false`.
   * - `components`
     - The distribution components of a `deb` repository. The default is
       `main`.
   * - `distribution`
     - The distribution name of a `deb` repository.
   * - `profiles`
     - The profiles the repository is used for, see
       :ref:`image-profiles`.
   * - `customize`
     - A script which modifies the repository files {kiwi} creates, for
       settings the schema does not support. It is called with the path
       of each repository file. A relative path is looked up in the image
       description directory.

For example, a `customize` script which adds the `module_hotfixes`
option to a dnf repository file:

.. code:: bash

   repo_file=$1
   echo 'module_hotfixes = 1' >> ${repo_file}

.. _supported-repository-paths:

Repository Paths
----------------

The `path` attribute of the `source` element supports the following
locations:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Path
     - Location
   * - `http://`, `https://`, `ftp://`
     - A repository on a server.
   * - `obs://$PROJECT/$REPOSITORY`
     - The repository `$REPOSITORY` of the project `$PROJECT` on the Open
       Build Service. The default instance is `build.opensuse.org
       <https://build.opensuse.org>`_, it can be changed in the
       :ref:`runtime configuration file <runtime_config>`. Repositories
       from different instances are not supported, use the URL of the
       repository instead.
   * - `obsrepositories:/`
     - For builds in the Open Build Service only: the repositories of
       the project which holds the image. This sets up the repositories
       in the Open Build Service instead of in the image description.
   * - `dir:///path` or `file:///path`
     - A local directory or file on the build host.
