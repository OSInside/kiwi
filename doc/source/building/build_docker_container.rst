Build a Docker Container Image
==============================

.. sidebar:: Abstract

   This page explains how to build a Docker base image. It containts

   * basic configuration explanation
   * how to build a Docker image
   * how to run it with the Docker daemon

KIWI is capable of building native Docker images, from scratch and derived
ones. KIWI Docker images are considered to be native since the KIWI
tarball image is ready to be loaded to a Docker daemon, including common
container configurations.

The Docker configuration metadata is provided to KIWI as part of the
:ref:`XML description file <decription_components>` using the
``<containerconfig>`` section. The following parameters
can be specified (more detailed schema documentation
:ref:`here <k.image.preferences.type.containerconfig>`):

* ``name``: Specifies the repository name of the Docker image.
* ``tag``: Sets the tag of the Docker image.
* ``maintainer``: Specifies the author field of the container.
* ``subcommand``: Provides the default execution parameters of the container.
  Equivalent of the `CMD` directive of a Docker file.
* ``labels``: Adds custom metadata to an image, is key-value pair. Equivalent
  of the `LABEL` directive of a Docker file.
* ``expose``: Informs at which ports is the container listening at runtime.
  Equivalent of the `EXPOSE` directive of a Docker file.
* ``environment``: Sets an environment values using key-value pairs.
  Equivalent of the `env` directive of a Docker file.
* ``entrypoint``: Sets the executable that the container will run, it can
  include parameters. Equivalent of the `ENTRYPOINT` directive of a Docker
  file..
* ``volumes``: Creates mountpoints with the given name and marks it to hold
  external volumes from the host or from other contianers. Equivalent of the
  `VOLUME` directive of a Docker file.
* ``user``: Sets the user name or UID to be used when running `entrypoint` and
  `subcommand`. Equivalent of the `USER` directive of a Docker file.
* ``workdir``: Sets the working directory to be used when running `cmd` and
  `entrypoint`. Equivalent of the `WORKDIR` directive of a Docker file.

Other Docker file directives such as ``RUN`` and ``COPY`` or ``ADD``, can be
mapped to KIWI by using the :ref:`config.sh <decription_components>`
script file to run bash commands or the
:ref:`overlay tree <decription_components>` to include extra files.

The following example shows how to build a Docker base image based on
openSUSE Leap:

1. Make sure you have checked out the example image descriptions,
   see :ref:`example-descriptions`.

2. Install the required toolchain for Docker images building.

   Include the follwing repository:

   .. code:: bash

      $ zypper ar -f http://download.opensuse.org/repositories/Virtualization:/containers/<DIST>

   where the placeholder `<DIST>` is the preferred distribution. Then install
   :command:`umoci` and :command:`skopeo` tools

   .. code:: bash

      $ zypper in umoci skopeo

3. Build the image with KIWI:

   .. code:: bash

      $ sudo kiwi-ng --type docker system build \
          --description kiwi-descriptions/suse/x86_64/suse-leap-42.2-docker \
          --target-dir /tmp/myimage

4. Test the Docker image.

   First load the new image

   .. code:: bash

      $ docker load -i Docker-Leap-42.2.x86_64-1.0.0.docker.tar.xz

   then run the loaded image:

   .. code:: bash

       $ docker run -it opensuse:42.2 /bin/bash
