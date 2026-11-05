.. _kiwi_system_boxbuild:

kiwi-ng system boxbuild
=======================

.. _db_kiwi_system_boxbuild_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng system boxbuild --help
   kiwi-ng system boxbuild --box=<name>
       [--box-memory=<vmgb>]
       [--box-console=<ttyname>]
       [--box-smp-cpus=<number>]
       [--box-debug]
       [--container]
       [--kiwi-version=<version>]
       [--shared-path=<path>]
       [--no-update-check]
       [--no-snapshot]
       [--no-accel]
       [--9p-sharing | --virtiofs-sharing | --sshfs-sharing]
       [--ssh-key=<name>]
       [--ssh-port=<port>]
       [--x86_64 | --aarch64]
       [--machine=<qemu_machine>]
       [--cpu=<qemu_cpu>]
       kiwi <kiwi_build_command_args>...
   kiwi-ng system boxbuild --list-boxes

.. _db_kiwi_system_boxbuild_desc:

DESCRIPTION
-----------

Build an image in a self-contained environment. The `boxbuild`
command uses KVM to start a virtual machine and run the kiwi
build command inside of that virtual machine. The provided
`--description` and `--target-dir` options are set up as shared
folders between the host and the guest. No other data will be
shared with the host, which also allows for cross distribution
builds. The boxbuild command provides the following additional
features over the standard build command:

* Build images independent of the host.
* Build images as normal user not as root.
* Build cross distribution images on one host.
* Build in predefined build VMs called boxes which includes
  all components needed to build appliances.

For running the build process in a virtual machine, it's required
to provide VM images that are suitable to perform this job. We
call the VM images `boxes`, and they contain kiwi itself as well
as all other components needed to build appliances. Those boxes
are hosted in the Open Build Service and are publicly available
on the `Subprojects` tab at:
https://build.opensuse.org/project/show/Virtualization:Appliances:SelfContained

As a user, you don't need to work with the boxes because this
is all done by the `boxbuild` command. It knows where to
fetch the box and also cares for an update of the box when it
has changed.

For a detailed introduction, see :ref:`self_contained`.

.. _db_kiwi_system_boxbuild_opts:

OPTIONS
-------

--box=<name>

  Name of the virtual machine that should be used for
  the build process.

--list-boxes

  Show available build boxes.

--box-memory=<vmgb>

  Amount of main memory to reserve for the virtual machine.
  The value is passed as is to the QEMU `-m` option, so add a
  unit suffix, e.g. `8G`. By default, the memory setting of the
  selected box is used, which is 8096M for the boxes provided
  with {kiwi}.

--box-console=<ttyname>

  Name of console in the kernel settings for the virtual
  machine. By default, set to hvc0.

--box-smp-cpus=<number>

  Number of CPUs to use in the SMP setup. By default,
  4 CPUs will be used.

--box-debug

  In debug mode, the started virtual machine will be kept open.

--container

  Build in container instead of a VM. Options related to
  building in a VM will have no effect.

--kiwi-version=<version>

  Specify a KIWI version to use for the build. The referenced
  KIWI will be fetched from pip and replaces the box installed
  KIWI version. Note: If --no-snapshot is used in combination
  with this option, the change of the KIWI version will be
  permanently stored in the used box.

--shared-path=<path>

  Optional host path to share with the box. The same path
  as it is present on the host will also be available inside
  of the box during build time.

--no-update-check

  Skip check for available box update. The option has no
  effect if the selected box does not yet exist on the host.

--no-snapshot

  Run box with snapshot mode switched off. This causes the
  box disk file to be modified by the build process and allows
  to keep a persistent package cache as part of the box.
  The option can be used to increase the build performance
  due to data stored in the box which doesn't have to be
  reloaded from the network. On the contrary, this option
  invalidates the immutable box attribute and should be
  used with care. On update of the box, all data stored
  will be wiped. To prevent this, combine the option with
  the --no-update-check option.

--no-accel

  Run box without hardware acceleration. By default, KVM
  acceleration is activated.

--9p-sharing|--virtiofs-sharing|--sshfs-sharing

  Select sharing backend to use for sharing data between the
  host and the box. This can be either 9p, virtiofs or sshfs.
  By default, 9p is used.

--ssh-key=<name>

  Name of ssh key to authorize for connection.
  By default, 'id_rsa' is used.

--ssh-port=<port>

  Port number to use to forward the guest's SSH port to the host.
  By default, '10022' is used.

--x86_64|--aarch64

  Select box for the given architecture. If no architecture
  is selected, the host architecture is used for selecting
  the box. The selected box architecture also specifies the
  target architecture for the image build with that box.

--machine=<qemu_machine>

  Optional machine name used by QEMU. By default, no specific
  value is used here and QEMU selects its default machine type.
  For cross arch builds or for system architectures for which
  QEMU defines no default like for Arm, it's required to specify
  a machine name.

  If you don't care about reproducing the idiosyncrasies of
  a particular bit of hardware, the best option is to use
  the 'virt' machine type.

--cpu=<qemu_cpu>

  Optional CPU type used by QEMU. By default, the host CPU
  type is used, which is only a good selection if the host
  and the selected box are from the same architecture. On
  cross arch builds, it's required to specify the CPU
  emulation the box should use.

kiwi <kiwi_build_command_args>...

  List of command parameters as supported by the kiwi-ng
  system build command. The information given here is passed
  along to the kiwi-ng system build command running in
  the virtual machine or container. The `--description` and
  `--target-dir` options are mandatory. Global options like
  `--type` or `--profile` must be passed as global options to
  the `boxbuild` call and are forwarded to the build command.
  See the example below how to provide options to the
  build command correctly.

  For compatibility with the former kiwi-boxed-plugin, the
  `--` separator is accepted as an alias for `kiwi`.

.. _db_kiwi_system_boxbuild_env:

ENVIRONMENT
-----------

KIWI_BOXED_CACHE_DIR
  By default, VM disk images used as build environment are
  stored in the $HOME/.kiwi_boxes directory. To override this
  location, set the KIWI_BOXED_CACHE_DIR environment variable
  to a different absolute path.

KIWI_BOXED_PLUGIN_CFG
  Path to a custom boxes configuration file. If not set, the
  configuration is searched in the following order:
  $PWD/kiwi_boxed_plugin.yml,
  $HOME/.config/kiwi/kiwi_boxed_plugin.yml,
  /etc/kiwi_boxed_plugin.yml and the default configuration
  provided with {kiwi}.

.. _db_kiwi_system_boxbuild_example:

EXAMPLE
-------

.. code:: bash

   $ git clone https://github.com/OSInside/kiwi-descriptions

   $ kiwi-ng --profile Virtual system boxbuild --box leap kiwi \
       --description kiwi-descriptions/suse/x86_64/suse-leap-15.6 \
       --target-dir /tmp/myimage
