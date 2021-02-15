.. _runtime_config:

The Runtime Configuration File
------------------------------

{kiwi} supports an additional configuration file for runtime specific
settings that do not belong into the image description but which are
persistent and would be unsuitable for command line parameters.

The runtime configuration file must adhere to the `YAML
<https://yaml.org/>`_ syntax and can be provided via the global
`--config` option at call time of {kiwi}. If no config file is
provided at the commandline, {kiwi} searches for the runtime
configuration file in the following locations:

1. :file:`~/.config/kiwi/config.yml`

2. :file:`/etc/kiwi.yml`

A default runtime config file in :file:`/etc/kiwi.yml` is provided with
the python3-kiwi package. The file contains all settings as comments
including a short description of each setting.
