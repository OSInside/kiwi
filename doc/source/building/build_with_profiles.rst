.. _building-build-with-profiles:

Building images with profiles
=============================

KIWI supports so-called profiles inside the XML image description, which
act as namespaces for additional settings to be applied on top of the
defaults. For further details see :ref:`xml-description-image-profiles`.


Local builds
------------

Local KIWI builds with a specific profile selected can be executed by
adding the command line flag `--profile=$PROFILE_NAME` to the KIWI
invocation, e.g.:

.. code-block:: shell-session

   $ sudo kiwi-ng --type iso system build \
         --profile=workstation \
         --description path/to/description/directory \
         --target-dir /tmp/myimage

Consult the manual page of :file:`kiwi` for further details:
:ref:`commands-kiwi`.


Building in the Open Build Service
----------------------------------

The Open Build Service (OBS) support profiles via the `multibuild
<https://openbuildservice.org/help/manuals/obs-reference-guide/cha.obs.multibuild.html>`_
feature. An example project using this feature is the
`openSUSE-Tumbleweed-JeOS
<https://build.opensuse.org/package/show/openSUSE:Factory/openSUSE-Tumbleweed-JeOS>`_
image.

To enable and use the profiles, follow these steps:

#. Add the following line to your :file:`config.xml`:

   .. code-block:: xml

      <!-- OBS-Profiles: @BUILD_FLAVOR@ -->

   It must be added before the opening `<image>` element and after the
   `<?xml?>` element, e.g.:

   .. code-block:: xml

      <?xml version="1.0" encoding="utf-8"?>
      <!-- OBS-Profiles: @BUILD_FLAVOR@ -->
      <image schemaversion="6.9" name="OpenSUSE-Leap-15.0">
        <!-- snip -->
      </image>

#. Add a file :file:`_multibuild` into your package's repository with the
   following contents:

   .. code-block:: xml

      <multibuild>
        <flavor>profile_1</flavor>
        <flavor>profile_2</flavor>
      </multibuild>

   where you add a line ``<flavor>$PROFILE</flavor>`` for each profile that
   you want OBS to build.


Note that OBS will by default exclude the build **without** any profile
enabled.

Running a build of a multibuild enabled repository via :file:`osc` can be
achieved via the `-M $PROFILE` flag:

.. code-block:: shell-session

   $ osc build -M $PROFILE
