kiwi-ng
=======

.. _db_commands_kiwi_desc:

`kiwi-ng` builds operating system images from an image description: a
directory with a :file:`config.xml` or :file:`*.kiwi` file and optional
files such as scripts or an overlay tree. The commands are grouped into
the services `system` (build images), `result` (work with build results)
and `image` (work with image descriptions and images). Plugins can add
commands to the `system` service.

.. _db_commands_kiwi_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] <service> <command> [options]
   kiwi-ng <service> <command> --help | help
   kiwi-ng --help | --version | --install-completion | --show-completion

The global options must be given before the service. `--help` shows the
usage of a service or command, `help` after a command opens its manual
page.

.. _db_commands_kiwi_opts:

Global Options
--------------

Options marked with ``...`` can be given multiple times.

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--type <build_type>``
     - The image type to build, instead of the default type of the image
       description. The former type `vmx` is replaced by `oem`.
   * - ``--profile <name>...``
     - Select a profile of the image description. Without it, the
       profiles with `import="true"` are used. See :ref:`image-profiles`.
   * - ``--kiwi-file <file>``
     - The image description file in the description directory. Default:
       :file:`config.xml`, :file:`image/config.xml`, then the first
       :file:`*.kiwi` file in alphabetical order.
   * - ``--target-arch <name>``
     - The image architecture, by default the one of the build host. A
       different architecture requires the host to be set up to run its
       binaries first, which is not part of {kiwi}.
   * - ``--config <file>``
     - An additional runtime configuration file with the highest
       precedence. It must exist. See :ref:`runtime_config`.
   * - ``--shared-cache-dir <directory>``
     - The shared cache of repository metadata and packages, bind mounted
       into the image root during the build. Default:
       :file:`/var/cache/kiwi`.
   * - ``--temp-dir <directory>``
     - The base directory for temporary files. Default: :file:`/var/tmp`.
   * - ``--setenv <variable=value>...``
     - Set an environment variable for {kiwi} and the tools and scripts it
       calls.
   * - ``--debug``
     - Print debug messages, same as ``--loglevel 10``.
   * - ``--loglevel <number>``
     - Only print messages at or above the level: 10 debug, 20 info,
       30 warning, 40 error, 50 critical.
   * - ``--logfile <file>``
     - Write all messages, including debug messages, to the file. With
       ``--logfile stdout``, write them to standard output instead.
   * - ``--logsocket <socket>``
     - Send all messages to the Unix domain socket, in the format of
       ``--logfile``.
   * - ``--debug-run-scripts-in-screen``
     - Run the scripts of the image description in a `screen` session,
       see :ref:`working-with-kiwi-user-defined-scripts`.
   * - ``--version``
     - Print the version of {kiwi}.
   * - ``--install-completion``
     - Install the shell completion for the current shell.
   * - ``--show-completion``
     - Print the shell completion for the current shell.

.. _db_commands_kiwi_console:

Console Output
--------------

The `system build`, `system prepare` and `system create` commands
start with a summary of the image: the image type, the repositories
the image is built from, and a check list of the basic features of
the image type, for example the encryption of a disk image, showing
which of them are enabled. The summary is shown after the command line
options, for example ``--set-repo``, are applied to the image
description.

The messages on the console are shown as a tree, grouped by the
state of the build process. Each phase of the build, for example the
preparation of the root system and the creation of the image, is the
root of a tree. The steps of a phase, for example the installation of
the bootstrap packages, are branches with their messages below them.
The end of a step closes its branch and shows the time the step took.
An action which is not a step shows the time it took, if it took a
while.

.. code:: bash

   12:54:39 ◆ Prepare root system
   12:54:39 ├─ Setup root directory: /tmp/myimage/build/image-root
   12:54:39 ├─┬ Installing bootstrap packages
            │ ├─ collection type: onlyRequired
            │ ├─ 148 packages installed, 21 scripts run
   12:55:12 │ └─ ✔ Installing bootstrap packages (32s)

While the package manager runs, a progress bar shows the current
action, for example the download or installation of a package or a
running package script. The progress is computed from the output of
the package manager, including the dependencies of the requested
packages. When the package manager is done, the number of installed
packages and of package scripts run is shown.

Colors are used if the output is a terminal and the `NO_COLOR`
environment variable is not set. The messages written by ``--logfile``
and ``--logsocket`` are plain text, one message per line.

.. _db_commands_kiwi_example:

Example
-------

.. code:: bash

   $ git clone https://github.com/OSInside/kiwi
   $ sudo kiwi-ng --type oem system build \
       --description kiwi/build-tests/{exc_description_disk} \
       --set-repo {exc_repo_leap} \
       --target-dir /tmp/myimage
