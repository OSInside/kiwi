.. _runtime_config:

The Runtime Configuration File
------------------------------

{kiwi} supports an additional configuration file for runtime-specific
settings that do not belong in the image description but which are
persistent and are unsuitable for command-line parameters.

The runtime configuration file must adhere to the `YAML <https://yaml.org/>`_
format. {kiwi} reads **every** one of the following locations that exists and
merges them, with later entries overriding earlier ones:

1. :file:`/usr/share/kiwi/kiwi.yml` (vendor)

2. every :file:`*.yml` in :file:`/usr/share/kiwi/kiwi.yml.d/`, alphabetically

3. :file:`/etc/kiwi.yml` (administrator)

4. every :file:`*.yml` in :file:`/etc/kiwi.yml.d/`, alphabetically

5. :file:`~/.config/kiwi/config.yml`

6. the file passed via the global `--config` option

`--config` does not replace the standard lookup, it is merged last and
has the highest precedence.

Both drop-in directories are always scanned, whether or not the corresponding
main file exists. A system with no :file:`/etc/kiwi.yml` still loads
:file:`/etc/kiwi.yml.d/*.yml`. This allows for modular configuration management,
where different aspects of the configuration can be separated into different
files.

.. note::

   Sections are merged key by key. A later file only needs to contain the
   keys it wants to change; all other keys of the same section from earlier
   files are kept. Lists, such as the `disable` list in the `runtime_checks`
   section, are combined from all files with duplicates removed.

   For example, if :file:`/usr/share/kiwi/kiwi.yml` contains

   .. code:: yaml

      bundle:
        compress: true
        shasum_size: "512"

   and :file:`/etc/kiwi.yml.d/10-local.yml` contains

   .. code:: yaml

      bundle:
        shasum_size: "256"

   then the effective `shasum_size` is ``"256"`` and `compress` stays
   ``true``.

A default runtime config file in :file:`/usr/share/kiwi/kiwi.yml.example` is
provided with the `python3-kiwi` main package. The file contains the available
settings as comments, including a short description of each setting.

.. _runtime_config_sparse_sync:

The sparse data sync
^^^^^^^^^^^^^^^^^^^^

The `sparse` setting of the `sync` section asks the sync step that
installs the image payload to turn sequences of null bytes in the
source into holes on the target. It is off by default. Its effect
depends on the presence of null runs in the source material and the
target filesystem.  The setting applies to every data sync {kiwi}
performs, not only to the one that installs the payload.

One typical system setup with many null runs is a Linux distribution
compiled for a larger page size (e.g., for ARM 64K Kernels).  This
leads to many zero tails between elf binary segments.

Filesystems differ in what is needed to make the holes stick. On a
filesystem that performs speculative preallocation, syncing sparsely
is not enough on its own, because the skipped range is eaten by
speculative preallocation and is recorded as an
allocated-but-unwritten extent.  Such an extent reads as zero and is
reported as a hole, yet it still occupies space. {kiwi} therefore lets
a filesystem implementation declare the mount options it needs to
prevent this, and applies them to the install time mount only, so that
they do not become mount options of the running system. Of the
filesystems {kiwi} supports, only `xfs` needs this. `ext4` and `btrfs`
keep the holes without help.

An encrypted image keeps the gain inside the filesystem, but by
default not in the image file. The sync sees the null runs in the
source and writes the payload sparsely either way, so the filesystem
in the image accounts less and the running system has that space
available. The image file does not become smaller by itself, because
{kiwi} overwrites the whole device with random data before the
filesystem is created, which allocates every block of the image
whatever the data sync does. With ``luks_randomize="false"`` the image
file accounts less as well. It is the randomization that limits the
gain. However, if the sparseness savings allow for it, you can always
make the overall image smaller in the build recipe.

A compressing read-only filesystem, such as `squashfs` or `erofs`,
typically gains nothing in addition, because the compression already
removes the null runs.

Sparse allocation can sometimes lead to additional fragmentation in
the target filesystem and underlying image file. Do not blindly enable
it, but check if your use case gains.
