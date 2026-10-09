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
