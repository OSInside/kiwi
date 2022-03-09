.. _building_container_build:

Build a Container Image
=======================

.. sidebar:: Abstract

   This page explains how to build a Container Image. It contains

   * basic configuration explanation
   * how to build a Container Image
   * how to run it with a Container Runtime

{kiwi} is capable of building native Container Images from scratch and
derived ones. {kiwi} Container images are considered to be native since the
{kiwi} tarball image is ready to be loaded into a Container Runtime like
Podman, Docker or Containerd, including common container configurations.

The Container configuration metadata is provided to {kiwi} as part of the
:ref:`XML description file <description_components>` using the
``<containerconfig>`` tag. The following configuration metadata can be
specified:

`containerconfig` attributes:

* ``name``: Specifies the repository name of the Container Image.
* ``tag``: Sets the tag of the Container Image.
* ``maintainer``: Specifies the author field of the container, this is
  equivalent to the `MAINTAINER` directive in a :file:`Dockerfile`.
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
* ``expose``: Define which ports can be exposed to the outside when
  running this container image.  Equivalent to one or more `EXPOSE`
  directives in a :file:`Dockerfile`.
* ``environment``: Sets environment variables using key-value pairs.
  Equivalent to one or multiple `ENV` directives in a :file:`Dockerfile`.
* ``entrypoint``: Sets the binary via which all commands inside the
  container will be executed. Equivalent of the `ENTRYPOINT` directive
  in a :file:`Dockerfile`.
* ``volumes``: Create mountpoints with the given name and mark them to hold
  external volumes from the host or from other containers. Equivalent to
  one or more `VOLUME` directives in a :file:`Dockerfile`.

Other :file:`Dockerfile` directives such as ``RUN``, ``COPY`` or ``ADD``,
can be mapped to {kiwi} using the
:ref:`config.sh <description_components>` script file to run bash commands
or the :ref:`overlay tree <description_components>` to include
additional files.

The following example illustrates how to build a Container Image based on
openSUSE Leap:

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

#. Include the ``Virtualization/containers`` repository to your list:

   .. code:: bash

      $ zypper addrepo http://download.opensuse.org/repositories/Virtualization:/containers/<DIST> container-tools

   where the placeholder `<DIST>` is the preferred distribution.

#. Install :command:`umoci` and :command:`skopeo` tools

   .. code:: bash

      $ zypper in umoci skopeo

#. Build the image with {kiwi}:

   .. code:: bash

      $ sudo kiwi-ng system build \
          --description kiwi/build-tests/{exc_description_docker} \
          --set-repo {exc_repo_leap} \
          --target-dir /tmp/myimage

#. Test the Container image.

   First load the new image into your Container Runtime:

   .. code:: bash

      $ podman load -i {exc_image_base_name_docker}.x86_64-{exc_image_version}.docker.tar.xz

   and then run the image:

   .. code:: bash

      $ podman run --rm -it buildsystem /bin/bash
