Build a Docker Container Image
==============================

.. hint::

   Make sure you have checked out the example image descriptions
   For details see :ref:`example-descriptions`

The following example shows how to build and run a container image
based on SUSE Leap for the docker container system.

Installing the Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Building Docker images with KIWI requires a couple of additional tools.
In practice, :command:`umoci` and :command:`skopeo` utilities are mandatory.
These tools are not yet in all regular openSUSE repositories, however a packaged
version can be found in the *Virtualization:containers* repository
`here <http://download.opensuse.org/repositories/Virtualization:/containers/>`_.
In order to install them first add the repository using the :command:`zypper ar`
command:

.. code:: bash

   $ zypper ar -f http://download.opensuse.org/repositories/Virtualization:/containers/<DIST>

where the placeholder `<DIST>` is the preferred distribution. Once the
repository has been added install the required utilities:

.. code:: bash

   $ zypper in umoci skopeo

Building the Image
~~~~~~~~~~~~~~~~~~

Run the following KIWI command in order to build the base image example.

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

* ``maintainer``: Specifies the author field of the container.
* ``cmd``: Provides the default execution parameters of the container.
* ``label``: Adds custom metadata to an image, is key-value pair.
* ``expose``: Informs at which ports is the container listening at runtime.
* ``env``: Sets an environment value, is key-value pair.
* ``entrypoint``: Sets the executable that the container will run, it can
  include parameters.
* ``volume``: Creates a mountpoint with the given name and marks it to hold
  external volumes from the host or from other contianers.
* ``user``: Sets the user name or UID to be used when running `cmd` and
  `entrypoint`.
* ``workdir``: Sets the working directory to be used when running `cmd` and
  `entrypoint`.

Map DockerFile Directives to KIWI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The native build description in docker is provided by a so called
DockerFile. The DockerFile is a shell like key=value based file.
In addition to the metadata information as shown above other
additional information could be part of a DockerFile. KIWI can
not natively handle the contents of the DockerFile, thus the
following list shows how to map the DockerFile directive in
KIWI:

* `ADD`

  In order to include a tarball and auto extract it in KIWI it can be done by
  including the files in the :ref:`overlay tree <decription_components>`,
  or by including an `<archive>` item inside the `<packages type="image">`
  section. **ADD** also handles remote content, in KIWI this should be done
  within the `config.sh` script.

* `RUN`

  In order to execute commands during build time in KIWI it can be done by
  extending the `config.sh` script. Note that the `config.sh` is executed
  after all the packages have been installed and after the overlay tree has
  been applied.

* `COPY`

  The equivalent in KIWI is to make use of the :ref:`overlay tree
  <decription_components>` in order to include files in a specific location.


Using an Existing Docker Image as Base Image
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
the skopeo tool (for example DockerHub URIs as
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
   overwriting it. Only the ``entrypoint`` and ``subcommand`` statements
   builds are an exception, they can be wiped using the ``clear`` attribute
   as used in the above example.


Export Image from Docker to Be Usable as Base Image
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
