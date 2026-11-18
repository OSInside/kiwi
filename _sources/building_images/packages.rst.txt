.. _packages:

Packages
========

.. sidebar:: Abstract

   This page describes how to select the packages to install into an
   image, and to remove from it.

Packages are listed in `packages` sections of the image description.
The `type` attribute of a section defines when its packages are
installed or removed:

.. code:: xml

   <image schemaversion="{schema_version}" name="{exc_image_base_name}">
       <packages type="bootstrap">
           <package name="filesystem"/>
           <package name="openSUSE-release"/>
       </packages>
       <packages type="image">
           <package name="patterns-openSUSE-base"/>
       </packages>
   </image>

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - `type`
     - Packages of the section
   * - `bootstrap`
     - Installed first, with the package manager of the build host, to
       create the initial root tree, see :ref:`prepare-step`.
   * - `image`
     - Installed inside of the root tree (chroot) after the bootstrap.
   * - an image type, for example `iso` or `oem`
     - Installed only when this image type is built.
   * - `uninstall`, `delete`
     - Removed from the image, see :ref:`uninstall-system-packages`.

A `packages` section also supports the attributes `profiles`, to use it
only for the given profiles (see :ref:`image-profiles`), and
`patternType` (see :ref:`product-and-namedCollection-element`).

.. _package-element:

The `package` element
---------------------

Each `package` element adds the package given in its `name` attribute.
The optional `arch` attribute limits the package to a build host
architecture, as reported by `uname -m`. In the following example,
`grub2-x86_64-efi` and `shim` are only installed on x86_64 hosts:

.. code:: xml

   <packages type="image">
       <package name="grub2"/>
       <package name="grub2-x86_64-efi" arch="x86_64"/>
       <package name="shim" arch="x86_64"/>
   </packages>

The name is passed to the package manager as is. RPM-based package
managers therefore also accept a capability, for example
`<package name="/usr/bin/my-binary"/>`. Such capabilities are not always
resolvable, for example in the Open Build Service, and are therefore not
recommended.

.. _archive-element:

The `archive` element
---------------------

Software which is not available as a package can be added as a tar
archive. Each `archive` element adds the archive given in its `name`
attribute, which {kiwi} looks up in the image description directory:

.. code:: xml

   <packages type="image">
       <archive name="custom-program1.tgz"/>
       <archive name="custom-program2.tar"/>
   </packages>

The archives are unpacked into the root of the image with `GNU tar
<https://www.gnu.org/software/tar/>`_, in the listed order, after the
packages are installed. Existing files are overwritten.

.. _product-and-namedCollection-element:

The `namedCollection` and `product` elements
--------------------------------------------

A `namedCollection` element installs a predefined list of packages: a
*pattern* on SUSE distributions or a *group* on Red Hat-based
distributions. A `product` element installs an openSUSE product. Both
take a `name` and an optional `arch` attribute.

The `patternType` attribute of the `packages` section controls which
dependencies of patterns are installed:

`onlyRequired`
   Only the required packages and patterns.

`plusRecommended`
   The required and the recommended packages and patterns.

Single packages are excluded from installation with `ignore` elements,
for example to not install some of the recommended packages of a
pattern:

.. code:: xml

   <packages type="image" patternType="plusRecommended">
       <namedCollection name="network-server"/>
       <package name="kernel"/>
       <ignore name="ejabberd"/>
       <ignore name="puppet-server"/>
   </packages>

`ignore` elements have no effect in `uninstall` and `delete` sections.

.. _uninstall-system-packages:

Removing Packages
-----------------

Packages are removed from the image at the end of the prepare step,
after :file:`config.sh` ran. There are two ways:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Section
     - Removes
   * - `<packages type="uninstall">`
     - The packages, all packages depending on them and their orphaned
       dependencies, with the package manager.
   * - `<packages type="delete">`
     - Only the packages, with `rpm` or `dpkg` and without dependency
       checks. This can break dependencies and the package database.

.. warning::

   `uninstall` can remove more packages than listed, including tools
   needed by later build stages. Use it with care.

`uninstall` removes tools which are only needed during the build,
without listing their dependencies. The following example installs a
compiler to build a program in :file:`config.sh` from sources shipped in
an archive, and removes the compiler afterwards:

.. code:: xml

   <packages type="image">
       <package name="ninja"/>
       <package name="clang"/>
       <package name="meson"/>
       <archive name="foo_app_sources.tar.gz"/>
   </packages>
   <!-- uninstalled after config.sh ran -->
   <packages type="uninstall">
       <package name="ninja"/>
       <package name="meson"/>
       <package name="clang"/>
   </packages>

.. code:: bash

   # config.sh
   pushd /opt/src/foo_app
   export CC=clang
   meson build
   cd build && ninja && ninja install
   popd

Other uses are removing `shadow` or partitioning tools such as `parted`
from containers, or the networking tools from images for devices
without a network.
