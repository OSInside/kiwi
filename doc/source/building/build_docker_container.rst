Build a Docker Container Image
==============================

.. hint::

   Make sure you have checked out the example image descriptions
   For details see :ref:`example-descriptions`

The following example shows how to build and run a container image
based on SUSE Leap for the docker container system.

.. note:: Requirements

   In order to successfully build a docker container the docker
   tools :command:`umoci` and :command:`skopeo` must be installed
   on the build host system.

.. code:: bash

    $ sudo kiwi-ng --type docker system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.2-docker \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.docker.tar.xz` below
:file:`/tmp/myimage`. For testing the docker image it's required
to have the docker subsystem installed and running. The following
command can be used to check if docker is installed and functional
on your system:

.. code:: bash

    $ docker images

The command above lists all available docker images. If the docker
daemon is running and responsive a list output is expected which
could also be empty if no images are available. In any other case
an error message is displayed which needs to be resolved prior to
continue with the next steps.

Once docker works on your system the KIWI built image needs to be
loaded into the docker system with the following command:

.. code:: bash

    $ docker load -i Docker-Leap-42.2.x86_64-1.0.0.docker.tar.xz

On success the docker image is available as part of the images list as follows:

.. code:: bash

    $ docker images

    REPOSITORY          TAG  ...
    opensuse            42.2 ...

In order to run an interactive shell session of the loaded container
the following command needs to be called:

.. code:: bash

    $ docker run -it opensuse:42.2 /bin/bash

Container Configuration
~~~~~~~~~~~~~~~~~~~~~~~

A docker container includes a set of information also called metadata.
The metadata information is provided within the KIWI XML description
as part of the ``<containerconfig>`` section. The following parameters
can be specified:

* ``maintainer``: @David, please describe meaning for the user
* ``cmd``: @David, please describe meaning for the user
* ``label``: @David, please describe meaning for the user
* ``expose``: @David, please describe meaning for the user
* ``env``: @David, please describe meaning for the user
* ``entrypoint``: @David, please describe meaning for the user
* ``volume``: @David, please describe meaning for the user
* ``user``: @David, please describe meaning for the user
* ``workdir``: @David, please describe meaning for the user

Map DockerFile directives to KIWI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The native build description in docker is provided by a so called
DockerFile. The DockerFile is a shell like key=value based file.
In addition to the metadata information as shown above other
additional information could be part of a DockerFile. KIWI can
not natively handle the contents of the DockerFile, thus the
following list shows how to map the DockerFile directive in
KIWI:

* `ADD`

  @David, please describe how this could be mapped in KIWI

* `RUN`

  @David, please describe how this could be mapped in KIWI

* `COPY`

  @David, please describe how this could be mapped in KIWI


Using an existing Docker Image as Base Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KIWI also supports building of a container image on top of another base image.
In that case, the resulting image will include the base image layers
plus a new one containing the changes added by KIWI. Building derived
images works in the same way as for the base images, the only difference
is that the base image must be specified in the description file, it can
be done using the **derived_from** optional attribute of ``<type>`` tag.
The value of the **derived_from** attribute is the URI of the image;
currently KIWI only supports references to local files (it expects a xz
compressed tarball image) and any other URI type that is supported by
the skopeo tool (e.g. DockerHub URIs as
``derived_from="docker://opensuse:leap"``). The following example
type specification shows how to specify a base image setup:

.. code:: xml

   <type image="docker" derived_from="docker://opensuse:leap">
       <containerconfig name="container_name" tag="container_tag" maintainer="tux">
           <entrypoint execute="myscript.sh"/>
           <subcommand clear="true"/>
       </containerconfig>
   </type>

.. note::

   The configuration metadata is inherited from the base image to
   the derived one, the only way to change the inherited metadata is by
   overwriting it. The ``entrypoint`` and ``subcommand`` statements
   builds an exception in a way that they can be wiped using the
   **clear** attribute as used in the above example


Export image from docker to be usable as Base Image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given there is an image in docker which should be used as a base image
for a KIWI build, we recommend to export the image from docker in the
following way:

.. code-block:: bash

    $ docker save opensuse:42.2 | xz > /tmp/opensuse-42.2.tar.xz

Once the command completed the :file:`/tmp/opensuse-42.2.tar.xz` could
be use as base image in the KIWI XML description as follows:

.. code:: xml

   <type image="docker" derived_from="file:///tmp/opensuse-42.2.tar.xz">
       ...
   </type>
