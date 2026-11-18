.. _kiwi_system_boxbuild:

kiwi-ng system boxbuild
=======================

.. _db_kiwi_system_boxbuild_desc:

Builds an image in a box: a virtual machine started with QEMU/KVM, or a
container, which contains {kiwi} and all tools to build images. Inside
of the box, `kiwi-ng system build` runs with the arguments after the
`kiwi` subcommand. Only the description and the target directory are
shared with the box. This allows to build images independent of the
build host, as a normal user, and for other distributions than the one
of the host. The boxes are provided in the `Open Build Service
<https://build.opensuse.org/project/show/Virtualization:Appliances:SelfContained>`__
and are downloaded and updated by the command. For an introduction, see
:ref:`self_contained`.

.. _db_kiwi_system_boxbuild_synopsis:

Usage
-----

.. code:: bash

   kiwi-ng [global options] system boxbuild \
       --box <name> \
       [options] \
       kiwi <build options>
   kiwi-ng system boxbuild --list-boxes

`<build options>` are the options of `kiwi-ng system build`, with
``--description`` and ``--target-dir`` required. Of the global options,
``--debug``, ``--type``, ``--profile`` and ``--kiwi-file`` are passed on
to the build in the box. ``--`` is accepted instead of `kiwi`, as in the
former `kiwi-boxed-plugin`.

.. _db_kiwi_system_boxbuild_opts:

Options
-------

Either ``--box`` or ``--list-boxes`` must be given, otherwise the
command does nothing.

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--box <name>``
     - The box to build in.
   * - ``--list-boxes``
     - List the available boxes.
   * - ``--container``
     - Build in a container instead of a virtual machine. The virtual
       machine options have no effect.
   * - ``--x86_64``, ``--aarch64``
     - The architecture of the box and the image. Default: the host
       architecture. ``--x86_64`` takes precedence.
   * - ``--kiwi-version <version>``
     - Install this {kiwi} version from PyPI in the box. Mutually exclusive
       with ``--kiwi-git``.
   * - ``--kiwi-git <git_link>``
     - Build and install {kiwi} from the git link in the box, for example
       `https://github.com/OSInside/kiwi/tree/BRANCH_NAME`, by default
       from the default branch.
   * - ``--shared-path <path>``
     - An additional host path to share with the box, at the same path.
   * - ``--no-update-check``
     - Do not check for a new version of the box.
   * - ``--no-snapshot``
     - Write into the disk of the box, which keeps for example the
       package cache for later builds. Changes of ``--kiwi-version`` or
       ``--kiwi-git`` stay in the box. A box update discards them.

Virtual Machine
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Description
   * - ``--box-memory <memory>``
     - The main memory, passed to the QEMU option `-m`, for example `8G`.
       Default: the memory of the box, 8096M for the {kiwi} boxes.
   * - ``--box-smp-cpus <number>``
     - The number of CPUs. Default: 4.
   * - ``--box-console <ttyname>``
     - The kernel console. Default: the console of the box, `hvc0` for
       the {kiwi} boxes.
   * - ``--box-debug``
     - Keep the virtual machine running after the build.
   * - ``--machine <qemu_machine>``
     - The QEMU machine type, required for cross architecture builds and
       for architectures without a default, such as Arm. `virt` is a good
       choice.
   * - ``--cpu <qemu_cpu>``
     - The QEMU CPU type. Default: the host CPU, which only works for the
       host architecture.
   * - ``--no-accel``
     - Run without KVM acceleration.
   * - ``--9p-sharing``, ``--virtiofs-sharing``, ``--sshfs-sharing``
     - The backend to share directories with the box. Default: 9p.
       virtiofs takes precedence over sshfs.
   * - ``--ssh-key <name>``
     - The ssh key to authorize. Default: `id_rsa`.
   * - ``--ssh-port <port>``
     - The host port for the ssh port of the box. Default: `10022`.

.. _db_kiwi_system_boxbuild_env:

Environment
-----------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Variable
     - Description
   * - `KIWI_BOXED_CACHE_DIR`
     - The directory for the boxes. Default: :file:`$HOME/.kiwi_boxes`.
   * - `KIWI_BOXED_PLUGIN_CFG`
     - The box configuration file. Default: the first existing file of
       :file:`$PWD/kiwi_boxed_plugin.yml`,
       :file:`$HOME/.config/kiwi/kiwi_boxed_plugin.yml` and
       :file:`/etc/kiwi_boxed_plugin.yml`, or the {kiwi} default.

.. _db_kiwi_system_boxbuild_example:

Example
-------

.. code:: bash

   $ git clone https://github.com/OSInside/kiwi-descriptions
   $ kiwi-ng --profile Virtual system boxbuild --box leap kiwi \
       --description kiwi-descriptions/suse/x86_64/suse-leap-15.6 \
       --target-dir /tmp/myimage
