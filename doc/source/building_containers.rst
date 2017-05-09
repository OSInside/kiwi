Building Container Images
=========================

.. hint:: **Abstract**

   This page describes how to build container images with KIWI.
   This description applies for version |version|.

Currently KIWI supports OCI and Docker container formats. Container
images work the same way as any other image type in KIWI, the
:ref:`prepare step <prepare-step>` creates the build root and configures the
system and the :ref:`create step <create-step>` configures and creates
the resulting image with required container format. KIWI makes use of
:command:`umoci` and :command:`skopeo` tools in order to operate with
container images, because of that those tools must be present in
the build environment, KIWI has a runtime check to validate skopeo and
umoci are present in ``PATH`` when building a container image. Building
container images in KIWI is like building any other kind of image, the
specific part in the description file is included under the ``<type>``
section. Contcretely, it hanldes the following OCI or Docker like
configuration metadata:

  * ``maintainer``: string
  * ``cmd``: array of strings
  * ``label``: key-value dictionary of string-string
  * ``expose``: array of strings
  * ``env``: array of strings
  * ``entrypoint``: array of strings
  * ``volume``: array of strings
  * ``user``: string
  * ``workdir``: string

This information is handled in within the KIWI description file under
the ``<containerconfig>`` tag (see the
:ref:`schema documentation <k.image.preferences.type.containerconfig>`).
The above mentioned metadata is mapped into the KIWI description as
in the example below:

.. code:: xml

   <type image="docker">
       <containerconfig
           name="container_name" maintainer="tux"
           user="root" workingdir="/root" tag="container_tag">
           <entrypoint execute="/bin/bash">
               <argument name="-x"/>
           </entrypoint>
           <subcommand execute="ls">
               <argument name="-l"/>
           </subcommand>
           <expose>
               <port number="80"/>
               <port number="8080"/>
           </expose>
           <volumes>
               <volume name="/tmp"/>
               <volume name="/var/log"/>
           </volumes>
           <environment>
               <env name="PATH" value="/bin:/usr/bin:/home/user/bin"/>
               <env name="SOMEVAR" value="somevalue"/>
           </environment>
           <labels>
               <label name="somelabel" value="labelvalue"/>
               <label name="someotherlabel" value="anotherlabelvalue"/>
           </labels>
       </containerconfig>
   </type>

Other DockerFile directives like **ADD**, **RUN** and **COPY** are
covered by KIWI by other mechanisms, since they aren't metadata, they are
part of the image :ref:`prepare step <prepare-step>` (install packages,
include config files, arrange configurations, etc.). Files can be
included using the :ref:`overlay tree (directory) <image-components>`
and any configuration script can be included as part of the
:ref:`config.sh <custom-config.sh>` file. See a complete container
example `here <https://github.com/SUSE/kiwi-descriptions>`_.

.. tip:: Load Docker images

   KIWI images can be loaded to the Docker daemon by just running:

   .. code-block:: bash

      $ docker load -i my_image_file.tar.xz

Building derived images
-----------------------

KIWI also supports making a container image on top of another base image.
In that case, the resulting image will include the base image layers
plus a new one containing the changes added by KIWI. Building derived
images works in the same way as for the base images, the only difference
is that the base image must be specified in the description file, it can
be done using the **derived_from** optional attribute of ``<type>`` tag.
The value of the **derived_from** attribute is the URI of the image;
currently KIWI only supports references to local files (it expects a xz
compressed tarball image) and any other URI type that is supported by
the :command:skopeo tool (e.g. DockerHub URIs as
``derived_from="docker://opensuse:leap"``). The type section to make a
derived image from an openSUSE Leap base image could be:

.. code:: xml

   <type image="docker" derived_from="docker://opensuse:leap">
       <containerconfig name="container_name" tag="container_tag" maintainer="tux">
           <entrypoint execute="myscript.sh"/>
           <subcommand clear="true"/>
       </containerconfig>
   </type>

It is also relevant to note here the usage of ``<subcommand clear="true">``.
It forces the cleanup of any ``subcommand`` inherited from the base image.
Note that the configuration metadata is inhereted from the base image to
the derived one, the only way to change the inhereted metadata is by
overwriting it. Only ``entrypoint`` and ``subcommand`` are an exception
to that and they can be cleared using the **clear** attribute.

.. tip:: Use loaded images as a base image

   To make a derived image form an image already loaded in a Docker
   daemon the image must be saved as a tarball and then xz compressed.
   Consider the following example:

   .. code-block:: bash

      $ docker save opensuse:leap | xz > /tmp/opensuse-leap.tar.xz

   Then it would be in referenced by
   ``derived_from="file:///tmp/opensuse-leap.tar.xz"``.
