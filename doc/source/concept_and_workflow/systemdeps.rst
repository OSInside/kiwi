.. _systemdeps:

Host Requirements To Build Images
---------------------------------

Building OS images requires several tools and sub-systems to be present on the
host {kiwi} host. For example, to build a virtual disk image, tools for
partition table setup or tools to create filesystems must to be available on the
host that builds the image.

The number of required components depends on the selected image type and the
features used with the image. It's unreasonable to expect {kiwi} users to know
which exact components are needed to build the image. A mechanism called
`kiwi-systemdeps` is designed to handle the host requirements.

`kiwi-systemdeps` consists out of a collection of sub-packages provided with the
`python-kiwi` main package. Each individual package requires a number of tools
and subsystem packages that belongs to the package category. There are the
following systemdeps packages:

`kiwi-systemdeps-core`:
  * Supports building the simple root archive `tbz` image type.
  * Installs the package managers which are supported by the target distribution
    as well as the `tar` archiving tool.

`kiwi-systemdeps-containers`:
  * Supports building `OCI` image types used with `docker`, `podman`.
  * Installs the distribution specific tool chain to build OCI
    compliant container images.

`kiwi-systemdeps-containers-wsl`:
  * Supports building `appx` image types.
  * Installs the distribution specific tool chain to build
    WSL compliant container images on Windows systems.

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

`kiwi-systemdeps-filesystems`:
  * Supports building `fs-type`, `oem`, `pxe`,
    `kis` and live `iso` image types.
  * Installs all tools to create filesystems supported by {kiwi}.
    The pulled in components are needed for any image type that
    needs to create a filesystem. This excludes the archive-based
    image types like `docker`, `appx` or `tbz`. The package also
    installs tools one level below the actual filesystem creation
    toolkit. These are components to manage loop devices as well
    as partition table setup and subsystem support like LVM and LUKS.
  * Depends on the `-core` kiwi-systemdeps packages.

`kiwi-systemdeps-disk-images`:
  * Supports building the `oem` image type.
  * Installs all tools to create virtual disks. Virtual disks in {kiwi}
    are created using the QEMU toolchain.
  * Depends on the `-filesystems` and `-bootloaders` kiwi-systemdeps
    packages.

`kiwi-systemdeps-image-validation`:
  * Installs the `jing` tool to validate the image description. This is
    useful for detailed error reports from {kiwi} if an image
    description validation error occurs. In addition, the `anymarkup` Python
    module is installed if the the option to install recommended packages
    is set. With `anymarkup` available, {kiwi} can also handle image
    descriptions in another format than the XML markup (for example,YAML).

Depending on the image type the `kiwi-systemdeps`` packages can help
to quickly setup the host system for building images.
In case the host must support everything, there is also the
main `kiwi-systemdeps` package that has all other
existing systemdeps packages as its dependency.

.. note::

   Pulling in all `kiwi-systemdeps` packages can result in a large number
   packages installed on the host., because the required packages themselves
   have other dependencies (for example, java for jing).
