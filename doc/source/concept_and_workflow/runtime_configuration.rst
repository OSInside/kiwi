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

.. warning::

   Merging happens at the **top level only**. A file that defines a section
   replaces that whole section from earlier files. Individual keys inside
   sections are not merged.

   For example, if :file:`/usr/share/kiwi/kiwi.yml` contains

   .. code:: yaml

      bundle:
        - compress: true
        - shasum_size: "512"

   and :file:`/etc/kiwi.yml.d/10-local.yml` contains

   .. code:: yaml

      bundle:
        - compress: false

   then the effective `shasum_size` is **not** ``"512"``. The whole `bundle`
   section is replaced, so `shasum_size` falls back to its default.

A default runtime config file in :file:`/usr/share/kiwi/kiwi.yml.example` is
provided with the `python3-kiwi` main package. The file contains the available
settings as comments, including a short description of each setting.
