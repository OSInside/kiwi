.. _building_docker_build:

Build a Docker Container Image
==============================

.. sidebar:: Abstract

   This page explains how to build a Docker base image. It contains

   * basic configuration explanation
   * how to build a Docker image
   * how to run it with the Docker daemon

{kiwi} is capable of building native Docker images, from scratch and derived
ones. {kiwi} Docker images are considered to be native since the {kiwi}
tarball image is ready to be loaded to a Docker daemon, including common
container configurations.

The Docker configuration metadata is provided to {kiwi} as part of the
:ref:`XML description file <description_components>` using the
``<containerconfig>`` tag. The following configuration metadata can be
specified:

`containerconfig` attributes:

* ``name``: Specifies the repository name of the Docker
  image.
* ``tag``: Sets the tag of the Docker image.
* ``maintainer``: Specifies the author field of
  the container.
* ``user``: Sets the user name or user id (UID) to be used when
  running `entrypoint` and
  `subcommand`. Equivalent of the `USER` directive of a Docker file.
* ``workingdir``: Sets the working directory to be used when running `cmd` and
  `entrypoint`. Equivalent of the `WORKDIR` directive of a Docker file.

`containerconfig` child tags:

* ``subcommand``: Provides the default execution parameters of the
  container. Equivalent of the `CMD` directive of a Docker file.
* ``labels``: Adds custom metadata to an image using key-value pairs.
  Equivalent to one or more `LABEL` directives of a Docker file.
* ``expose``: Informs at which ports is the container listening at runtime.
  Equivalent to one or more `EXPOSE` directives of a Docker file.
* ``environment``: Sets an environment values using key-value pairs.
  Equivalent to one or more the `env` directives of a Docker file.
* ``entrypoint``: Sets the command that the container will run, it can
  include parameters. Equivalent of the `ENTRYPOINT` directive of a Docker
  file.
* ``volumes``: Create mountpoints with the given name and mark it to hold
  external volumes from the host or from other containers. Equivalent to
  one or more `VOLUME` directives of a Docker file.

Other Docker file directives such as ``RUN``, ``COPY`` or ``ADD``, can be
mapped to {kiwi} by using the :ref:`config.sh <description_components>`
script file to run bash commands or the
:ref:`overlay tree <description_components>` to include extra files.

The following example shows how to build a Docker base image based on
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

#. Test the Docker image.

   First load the new image

   .. code:: bash

      $ docker load -i {exc_image_base_name_docker}.x86_64-{exc_image_version}.docker.tar.xz

   then run the loaded image:

   .. code:: bash

      $ docker run -it buildsystem /bin/bash
