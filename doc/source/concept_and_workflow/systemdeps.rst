.. _systemdeps:

Host Requirements To Build Images
---------------------------------

When building OS images, several tools and sub-systems are used
and required on the host {kiwi} is called at. For example, to
build a virtual disk image, several tools needs to be available
on the host that builds the image. This includes tools for
partition table setup or tools to create filesystems.

The number of required components depends on the selected image
type and the *features* used with the image. We cannot expect
the users of {kiwi} to know about each and every component that
is needed to build the image. Therefore a concept to help with
the host requirements exists and is named `kiwi-systemdeps`

The `kiwi-systemdeps` concept consists out of a collection of
sub-packages provided with the `python-kiwi` main package. Each
individual package requires a number of tools and subsystem packages
which belongs to the package category. There are the following
systemdeps packages:

`kiwi-systemdeps-core`:
  * Supports building the simple root archive `tbz` image type.
  * Installs the package managers which are supported by the
    target distribution as well as the `tar` archiving tool.

`kiwi-systemdeps-containers`:
  * Supports building `docker` and `appx` image types.
  * Installs the distribution specific tool chain to build OCI
    compliant and WSL container images.

`kiwi-systemdeps-iso-media`:
  * Supports building `iso` image types and `oem` install media.
  * Installs all tools required to build ISO filesystems.
  * Depends on the `-core`, `-filesystems` and `-bootloaders`
    kiwi-systemdeps packages.

`kiwi-systemdeps-bootloaders`:
  * Supports building bootable `oem` and `iso` image types.
  * Installs all bootloader tools depending on the host architecture
    to allow setup and install of the bootloader. The pulled in
    components are required for any image that is able to boot
    through some BIOS or firmware.
  * Depends on the `-core` kiwi-systemdeps packages.

  .. note::

     The `iso` type is an exception which might not require the
     `-bootloaders` systemdeps. In case of the `firmware` attribute
     to be set to `bios`, {kiwi} builds bootable ISO images still
     based on isolinux which is provided with the `-iso-media`
     systemdeps. However, by default, any {kiwi} created ISO image
     is BIOS and EFI capable and based on the grub bootloader which
     causes a requirement to the `-bootloaders` systemdeps.

`kiwi-systemdeps-filesystems`:
  * Supports building `fs-type`, `oem`, `pxe`,
    `kis` and live `iso` image types.
  * Installs all tools to create filesystems supported with {kiwi}.
    The pulled in components are needed for any image type that
    needs to create a filesystem. This excludes the archive based
    image types like `docker`, `appx` or `tbz`. The package also
    installs tools one level below the actual filesystem creation
    toolkit. These are components to manage loop devices as well
    as partition table setup and subsystem support like LVM and LUKS.
  * Depends on the `-core` kiwi-systemdeps packages.

`kiwi-systemdeps-disk-images`:
  * Supports building the `oem` image type.
  * Installs all tools to create virtual disks. In {kiwi}, virtual disks
    are created using the QEMU toolchain.
  * Depends on the `-filesystems` and `-bootloaders` kiwi-systemdeps
    packages.

`kiwi-systemdeps-image-validation`:
  * Installs the `jing` tool to validate the image description. This is
    useful for detailed error reports from {kiwi} in case of an image
    description validation error. In addition, the `anymarkup` Python
    module is installed if the the option to install recommended packages
    is set. With `anymarkup` available, {kiwi} can also handle image
    descriptions in another format than the XML markup, like YAML.

Depending on the image type the kiwi-systemdeps packages can help
to setup the host system quickly for the task to build an image.
In case the host should support *everything* there is also the
main `kiwi-systemdeps` package which has a dependency on all other
existing systemdeps packages.

.. note::

   Pulling in all `kiwi-systemdeps` packages can result in quite
   some packages to become installed on the host. This is because
   the required packages itself comes with a number of dependencies
   like java for jing as one example.
