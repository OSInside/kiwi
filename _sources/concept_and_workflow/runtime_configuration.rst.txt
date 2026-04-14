.. _runtime_config:

The Runtime Configuration File
------------------------------

{kiwi} supports an additional configuration file for runtime-specific
settings that do not belong in the image description but which are
persistent and are unsuitable for command-line parameters.

The runtime configuration file must adhere to the `YAML <https://yaml.org/>`_
syntax, and the file can be pointed to via the global `--config` option at call
time of {kiwi}. If no config file is provided, {kiwi} searches for the runtime
configuration file in the following locations:

1. :file:`~/.config/kiwi/config.yml`

2. :file:`/etc/kiwi.yml`

3. :file:`/usr/share/kiwi/kiwi.yml`

A default runtime config file in :file:`/usr/etc/kiwi.yml.example` is
provided with the `python3-kiwi` main package. The file contains all
possible settings as comments, including a short description of each
setting.

If the runtime configuration file is located at :file:`/etc/kiwi.yml`,
the system will also check for extra configuration files in
:file:`/etc/kiwi.yml.d/`. Similarly, if the main file is at
:file:`/usr/share/kiwi/kiwi.yml`, it will look for additional files in
:file:`/usr/share/kiwi/kiwi.yml.d/`. All `.yml` files in these directories are
loaded in alphabetical order and combined into the final configuration.
This allows for modular configuration management, where different
aspects of the configuration can be separated into different files.
