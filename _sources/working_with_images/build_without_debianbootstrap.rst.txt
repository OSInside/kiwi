.. _debianbootstrap_alternative:

Circumvent Debian Bootstrap
===========================

.. sidebar:: Abstract

   This page provides information how to build Debian based
   images without an extra bootstrap process.

When building Debian based images {kiwi} uses `apt` in the
bootstrap and the system phase to create the image root tree.
However, `apt` does not support a native way to bootstrap
an empty root tree. Therefore the bootstrap phase uses
apt only to resolve the given bootstrap packages and to
download these packages from the given repositories.
The list of packages is then manually extracted into the
new root tree which is not exactly the same as if `apt`
would have installed them natively. For the purpose of
creating an initial tree to begin with, this procedure
is acceptable though.

If, for some reasons, this bootstrap procedure is not
applicable, {kiwi} allows for an alternative process which is
based on a prebuilt bootstrap-root archive provided as a package.

To make use of a `bootstrap_package`, the name of that package
needs to be referenced in the {kiwi} description as follows:

.. code:: xml

   <packages type="bootstrap" bootstrap_package="bootstrap-root">
       <package name="a"/>
       <package name="b"/>
   </packages>

The boostrap process now changes in a way that the provided
bootstrap_package `bootstrap-root` will be installed on the build
host machine. Next {kiwi} searches for a tar archive file
:file:`/var/lib/bootstrap/bootstrap-root.ARCH.tar.xz`,
where `ARCH` is the name of the host architecture e.g `x86_64`.
If found the archive gets unpacked and serves as the bootstrap
root tree to begin with. The optionally provided additional
bootstrap packages, `a` and `b` in this example will be installed
like system packages via `chroot` and `apt`. Usually no additional
bootstrap packages are needed as they could all be handled as
system packages.

How to Create a bootstrap_package
---------------------------------

Changing the setup in {kiwi} to use a `bootstrap_package` rather
then using {kiwi}'s debian bootstrap method to do the job, comes with
the task to create that package providing the bootstrap root tree. There
are more than one way to do this. The following procedure is just one
example and requires some background knowledge about the Open Build Service
`OBS <https://build.opensuse.org>`__ and its {kiwi} integration.

1. Create an OBS project and repository setup that matches your image target
2. Create an image build package

   .. code:: bash

      osc mkpac bootstrap-root

3. Create the following :file:`appliance.kiwi` file

   .. code:: xml

      <image schemaversion="7.4" name="bootstrap-root">
          <description type="system">
              <author>The Author</author>
              <contact>author@example.com</contact>
              <specification>prebuilt bootstrap rootfs for ...</specification>
          </description>

          <preferences>
              <version>1.0.1</version>
              <packagemanager>apt</packagemanager>
              <type image="tbz"/>
          </preferences>

          <repository type="rpm-md">
              <source path="obsrepositories:/"/>
          </repository>

          <packages type="image">
              <package name="gawk"/>
              <package name="apt-utils"/>
              <package name="debconf"/>
              <package name="mawk"/>
              <package name="libpam-runtime"/>
              <package name="util-linux"/>
              <package name="systemd"/>
              <package name="init"/>
              <package name="gnupg"/>
              <package name="iproute2"/>
              <package name="iptables"/>
              <package name="iputils-ping"/>
              <package name="ifupdown"/>
              <package name="isc-dhcp-client"/>
              <package name="netbase"/>
              <package name="dbus"/>
              <package name="xz-utils"/>
              <package name="usrmerge"/>
              <package name="language-pack-en"/>
          </packages>

          <packages type="bootstrap"/>
      </image>

   .. code:: bash

      osc add appliance.kiwi
      osc ci

4. Package the image build results into a debian package

   In step 3. the bootstrap root tarball was created but not yet
   packaged. A debian package is needed such that it can be
   referenced with the `bootstrap_package` attribute and the repository
   providing it. The simplest way to package the `bootstrap-root` tarball
   is to create another package in OBS and use the tarball file as
   its source.
