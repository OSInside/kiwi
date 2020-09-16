.. _packages:

Adding and Removing Packages
============================

On top of the :ref:`repositories` setup the package setup is
required. {kiwi} allows the end user to completely customize the selection
of packages via the `packages` element.

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <packages type="bootstrap">
           <package name="udev"/>
           <package name="filesystem"/>
           <package name="openSUSE-release"/>
           <!-- additional packages installed before the chroot is created -->
       </packages>
       <packages type="image">
           <package name="patterns-openSUSE-base"/>
           <!-- additional packages to be installed into the chroot -->
       </packages>
   </image>

The `packages` element provides a collection of different child elements
that instruct {kiwi} when and how to perform package installation or
removal. Each `packages` element acts as a group, whose behavior can be
configured via the following attributes:

- `type`: either `bootstrap`, `image`, `delete`, `uninstall` or one of the
  following build types: `docker`, `iso`, `oem`, `kis`, `oci`.

  Packages for `type="bootstrap"` are pre-installed to populate the images'
  root file system before chrooting into it.

  Packages in `type="image"` are installed immediately after the initial
  chroot into the new root file system.

  Packages in `type="delete"` and `type="uninstall"` are removed from the
  image, for details see :ref:`uninstall-system-packages`.

  And packages which belong to a build type are only installed when that
  specific build type is currently processed by {kiwi}.

- `profiles`: a list of profiles to which this package selection applies
  (see :ref:`image-profiles`).

- `patternType`: selection type for patterns, supported values are:
  `onlyRequired`, `plusRecommended`, see:
  :ref:`product-and-namedCollection-element`.

The following sections describes the different child elements of
a `packages` group.

.. _package-element:

The `package` element
^^^^^^^^^^^^^^^^^^^^^

The `package` element represents a single package to be installed (or
removed), whose name is specified via the mandatory `name` attribute:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="bootstrap">
           <package name="udev"/>
       </packages>
   </image>

which adds the package `udev` to the list of packages to be added to the
initial filesystem. Note, that the value that you pass via the `name`
attribute is passed directly to the used package manager. Thus, if the
package manager supports other means how packages can be specified, you may
pass them in this context too. For example, RPM based package managers
(like :command:`dnf` or :command:`zypper`) can install packages via their
`Provides:`. This can be used to add a package that provides a certain
capability (e.g. `Provides: /usr/bin/my-binary`) via:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="bootstrap">
           <package name="/usr/bin/my-binary"/>
       </packages>
   </image>

Whether this works depends on the package manager and on the environment
that is being used. In the Open Build Service, certain `Provides` either
are not visible or cannot be properly extracted from the {kiwi}
description. Therefore, relying on `Provides` is not recommended.

Packages can also be included only on specific host architectures via the
`arch` attribute. {kiwi} compares the `arch` attributes value with the host
architecture that builds the image according to the output of `uname -m`.

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="image">
           <package name="grub2"/>
           <package name="grub2-x86_64-efi" arch="x86_64"/>
           <package name="shim" arch="x86_64"/>
       </packages>
   </image>

which results in `grub2-x86_64-efi` and `shim` being only installed if the
build host is a 64bit x86 machine, but `grub2` will be installed independent
of the architecture.


.. _archive-element:

The `archive` element
^^^^^^^^^^^^^^^^^^^^^

It is sometimes necessary to include additional packages into the image
which are not available in the package manager's native format. {kiwi}
supports the inclusion of ordinary tar archives via the `archive` element,
whose `name` attribute specifies the filename of the archive ({kiwi} looks
for the archive in the image description folder).

.. code:: xml

   <packages type="image">
       <archive name="custom-program1.tgz"/>
       <archive name="custom-program2.tar"/>
   </packages>

{kiwi} will extract the archive into the root directory of the image using
`GNU tar <https://www.gnu.org/software/tar/>`_, thus only archives
supported by it can be included. When multiple `archive` elements are
specified then they will be applied in a top to bottom order. If a file is
already present in the image, then the file from the archive will overwrite
it (same as with the image overlay).

.. _uninstall-system-packages:

Uninstall System Packages
^^^^^^^^^^^^^^^^^^^^^^^^^

{kiwi} supports two different methods how packages can be removed from the
appliance:

1. Packages present as a child element of `<packages type="uninstall">`
   will be gracefully uninstalled by the package manager alongside with
   dependent packages and orphaned dependencies.

2. Packages present as a child element of `<packages type="delete">` will
   be removed by RPM/DPKG without any dependency check, thus potentially
   breaking dependencies and compromising the underlying package database.

Both types of removals take place after :file:`config.sh` is run in the
:ref:`prepare step <prepare-step>`
(see also :ref:`working-with-kiwi-user-defined-scripts`).

.. warning::

   An `uninstall` packages request deletes:

     * the listed packages,
     * the packages dependent on the listed ones, and
     * any orphaned dependency of the listed packages.

   Use this feature with caution as it can easily cause the removal of
   sensitive tools leading to failures in later build stages.


Removing packages via `type="uninstall"` can be used to completely remove a
build time tool (e.g. a compiler) without having to specify a all
dependencies of that tool (as one would have when using
`type="delete"`). Consider the following example where we wish to compile a
custom program in :file:`config.sh`. We ship its source code via an
`archive` element and add the build tools (`ninja`, `meson` and `clang`) to
`<packages type="image">` and `<packages type="uninstall">`:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <!-- snip -->
       <packages type="image">
           <package name="ca-certificates"/>
           <package name="coreutils"/>
           <package name="ninja"/>
           <package name="clang"/>
           <package name="meson"/>
           <archive name="foo_app_sources.tar.gz"/>
       </packages>
       <!-- These packages will be uninstalled after running config.sh -->
       <packages type="uninstall">
           <package name="ninja"/>
           <package name="meson"/>
           <package name="clang"/>
       </packages>
   </image>

The tools `meson`, `clang` and `ninja` are then available during the
:ref:`prepare step <prepare-step>` and can thus be used in
:file:`config.sh` (for further details, see
:ref:`working-with-kiwi-user-defined-scripts`), for example to build
``foo_app``:

.. code:: bash

   pushd /opt/src/foo_app
   mkdir build
   export CC=clang
   meson build
   cd build && ninja && ninja install
   popd

The `<packages type="uninstall">` element will make sure that the final
appliance will no longer contain our tools required to build ``foo_app``,
thus making our image smaller.

There are also other use cases for `type="uninstall"`, especially for
specialized appliances. For containers one can often remove the package
`shadow` (it is required to setup new user accounts) or any left over
partitioning tools (`parted` or `fdisk`). All networking tools can be
safely uninstalled in images for embedded devices without a network
connection.

.. _product-and-namedCollection-element:

The `product` and `namedCollection` element
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

{kiwi} supports the inclusion of openSUSE products or of namedCollections
(*patterns* in SUSE based distributions or *groups* for RedHat based
distributions). These can be added via the `product` and `namedCollection`
child elements, which both take the mandatory `name` attribute and the
optional `arch` attribute.

`product` and `namedCollection` can be utilized to shorten the list of
packages that need to be added to the image description tremendously. A
named pattern, specified with the namedCollection element is a
representation of a predefined list of packages. Specifying a pattern will
install all packages listed in the named pattern. Support for patterns is
distribution specific and available in SLES, openSUSE, CentOS, RHEL and
Fedora. The optional `patternType` attribute on the packages element allows
you to control the installation of dependent packages. You may assign one
of the following values to the `patternType` attribute:

- `onlyRequired`: Incorporates only patterns and packages that the
  specified patterns and packages require. This is a "hard dependency" only
  resolution.

- `plusRecommended`: Incorporates patterns and packages that are required
  and recommended by the specified patterns and packages.


The `ignore` element
^^^^^^^^^^^^^^^^^^^^

Packages can be explicitly marked to be ignored for installation inside a
`packages` collection. This useful to exclude certain packages from being
installed when using patterns with `patternType="plusRecommended"` as shown
in the following example:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <packages type="image" patternType="plusRecommended">
           <namedCollection name="network-server"/>
           <package name="grub2"/>
           <package name="kernel"/>
           <ignore name="ejabberd"/>
           <ignore name="puppet-server"/>
       </packages>
   </image>


Packages can be marked as ignored during the installation by adding a
`ignore` child element with the mandatory `name` attribute set to the
package's name. Optionally one can also specify the architecture via the
`arch` similarly to :ref:`package-element`.

.. warning::

   Adding `ignore` elements as children of a `<packages type="delete">` or
   a `<packages type="uninstall">` element has no effect! The packages will
   still get deleted.
