.. _gracefully_uninstall:

Gracefully Uninstall System Packages
====================================

.. sidebar:: Abstract

   This page provides some details about uninstalling
   packages and how it could be used in order to remove
   packages once the image configuration, using the `config.sh`
   script, is done.

Uninstalling packages from the system image that were previously installed
during the installation phase is an operation that can be
handy under certain circumstances. As an example, someone could be interested
in performing some configuration tasks in the
`config.sh` script (see :ref:`prepare step <prepare-step>` for
further details). That would require to include some extra packages,
which are only needed at build time. One example would be compiling
some unpacked application sources.

KIWI description file schema defines package requests of type `uninstall`
and type `delete`:

  * The `uninstall` requests perform a clean packages removal by removing
    any package dependent on the requested ones and also removing orphan
    dependencies.

  * The `delete` requests perform a hard removal without any dependency
    check, thus only listed packages are deleted even if it breaks
    dependencies or compromises any underlying package database.

This page focuses on `uninstall` package requests.

This is an example of the package requests in a description of a Container
image that removes user related tools and development tools:

.. code:: xml

      <packages type="image">
        <package name="ca-certificates"/>
        <package name="ca-certificates-mozilla"/>
        <package name="coreutils"/>
        <package name="iputils"/>
        <package name="openSUSE-build-key"/>
        <package name="krb5"/>
        <package name="netcfg"/>
        <package name="kubic-locale-archive"/>
        <package name="make"/>
        <package name="llvm-clang"/>
        <archive name="foo_app_sources.tar.gz"/>
      </packages>
      <!-- These packages will be uninstalled after running config.sh -->
      <packages type="uninstall">
        <package name="shadow"/>
        <package name="make"/>
        <package name="llvm-clang"/>
      </packages>
    

In the previous example after installing all the packages and archives, image
repositories are configured and then the `config.sh` script is executed.
In `config.sh` the `foo_app_sources.tar.gz` could be compiled using the
`make` and `llvm` packages with something like a `make install` call. It is
a common practice to build tiny and single purpose container images, thus
makes sense to remove unneeded packages, like `make` and `llvm-clang`.
To gracefully remove them, they have been included into the
*type="uninstall"* packages list. Those packages will be removed including
a dependency cleanup.

.. warning::

   An `uninstall` packages request deletes:

     * the listed packages,
     * the packages dependent on the listed ones, and
     * any orphaned dependecy of the listed packages.

   Use this feature with caution as it can easily
   cause the removal of sensitive tools leading to failures in
   later build stages.

In the above example also the *shadow* package is being removed, again, in
this specific case, it is not expected to be needed in the final image.
The *shadow* package mainly provides tools to handle user accounts.
In a container image, once everything is installed and configured, it is
not expected to require any further user account modification to the image, 
tools such as *useradd* or *usermod* will not be required.
