.. _building_container_build:

Build a Container Image
=======================

.. sidebar:: Abstract

   This page explains how to build a Container Image. It covers the following topics:

   * basic configuration explanation
   * how to build a Container Image
   * how to run it with a Container Runtime

{kiwi} can build native container images from scratch or using existing images.
{kiwi} container images are considered to be native, because a {kiwi} tarball
image can be loaded directly into container runtimes like Podman, Docker or
Containerd, including common container configurations.

The container configuration metadata is supplied to {kiwi} as part of the
:ref:`XML description file <description_components>` using the
``<containerconfig>`` tag. The following configuration metadata can be
specified.

`containerconfig` attributes:

* ``name``: Specifies the repository name of the container image.
* ``tag``: Sets the tag of the container image.
* ``maintainer``: Specifies the author of the container. Equivalent to the
  `MAINTAINER` directive in a :file:`Dockerfile`.
* ``user``: Sets the user name or user id (UID) to be used when
  running `entrypoint` and `subcommand`. Equivalent of the `USER`
  directive of a :file:`Dockerfile`.
* ``workingdir``: Sets the working directory to be used when running
  `cmd` and `entrypoint`. Equivalent of the `WORKDIR` directive in a
  :file:`Dockerfile`.

`containerconfig` child tags:

* ``subcommand``: Provides the default execution parameters of the
  container. Equivalent of the `CMD` directive in a :file:`Dockerfile`.
* ``labels``: Adds custom metadata to an image using key-value pairs.
  Equivalent to one or more `LABEL` directives in a :file:`Dockerfile`.
* ``expose``: Defines which ports can be exposed to the outside when
  running this container image.  Equivalent to one or more `EXPOSE`
  directives in a :file:`Dockerfile`.
* ``environment``: Sets environment variables using key-value pairs.
  Equivalent to one or multiple `ENV` directives in a :file:`Dockerfile`.
* ``entrypoint``: Sets the binary to use for executing all commands inside the
  container. Equivalent of the `ENTRYPOINT` directive in a :file:`Dockerfile`.
* ``volumes``: Creates mountpoints with the given name and marks them to hold
  external volumes from the host or from other containers. Equivalent to
  one or more `VOLUME` directives in a :file:`Dockerfile`.
* ``stopsignal``: The stopsignal element sets the system call signal that
  will be sent to the container to exit. This signal can be a signal name
  in the format SIG[NAME], for instance SIGKILL, or an unsigned number that
  matches a position in the kernel's syscall table, for instance 9.
  The default is SIGTERM if not defined

Other :file:`Dockerfile` directives such as ``RUN``, ``COPY`` or ``ADD``,
can be mapped to {kiwi} using the
:ref:`config.sh <description_components>` script file to run Bash commands,
or the :ref:`overlay tree <description_components>` to include
additional files.

The following example illustrates how to build a container image based on
openSUSE Leap:

1. Make sure you have checked out the example image descriptions
   (see :ref:`example-descriptions`).

#. Include the ``Virtualization/containers`` repository into your list (replace the placeholder `<DIST>` with the name of the desired distribution):

   .. code:: bash

      $ zypper addrepo http://download.opensuse.org/repositories/Virtualization:/containers/<DIST> container-tools

#. Install :command:`umoci` and :command:`skopeo` tools

   .. code:: bash

      $ zypper in umoci skopeo

#. Build an image with {kiwi}:

   .. code:: bash

      $ sudo kiwi-ng system build \
          --description kiwi/build-tests/{exc_description_docker} \
          --set-repo {exc_repo_leap} \
          --target-dir /tmp/myimage

#. Test the container image.

   First load the new image into your container runtime:

   .. code:: bash

      $ podman load -i {exc_image_base_name_docker}.x86_64-{exc_image_version}.docker.tar.xz

   Then run the image:

   .. code:: bash

      $ podman run --rm -it buildsystem /bin/bash
