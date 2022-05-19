.. _debootstrap_alternative:

Circumvent debootstrap
======================

.. sidebar:: Abstract

   This page provides information how to build Debian based
   images with `apt` but without using `debootstrap` to bootstrap
   the image root tree

When building Debian based images {kiwi} uses two tools to
create the image root tree. First it calls `debootstrap` to
initialize a minimal root tree and next it chroot's into that
tree to complete the installation via `apt`. The reason why it
is done that way is because `apt` does not(yet) support to
install packages into an empty root directory like it is done
with all other packagemanager interfaces implemented in {kiwi}.

The use of `debootstrap` comes along with some prerequisites
and limitations:

* It can only use one repository to bootstrap from
* It can only use an official archive repo
* It has its own dependency resolver different from apt

If one ore more of this properties turns into an issue, {kiwi}
allows for an alternative process which is based on a prebuilt
bootstrap-root archive provided as a package.

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
then letting `debootstrap` do the job comes with the task to create
that package providing the bootstrap root tree. There are more than
one way to do this. The following procedure is just one example and
requires some background knowledge about the Open Build Service
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
              <!-- packages included so OBS adds it as a build dependency, however this is installed by debootstrap -->
              <package name="mawk"/>
          </packages>

          <packages type="bootstrap">
              <!-- bootstrap done via debootstrap -->
          </packages>
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
