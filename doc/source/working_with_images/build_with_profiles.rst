.. _building-build-with-profiles:

Building Images with Profiles
=============================

{kiwi} supports so-called *profiles* inside the XML image description. Profiles
act as namespaces for additional settings to be applied on top of the
defaults. For further details, see :ref:`image-profiles`.


Local Builds
------------

To execute local {kiwi} builds with a specific, selected profile, add the
command line flag `--profile=$PROFILE_NAME`:

.. code:: shell-session

   $ sudo kiwi-ng --type iso system build \
         --profile=workstation \
         --description kiwi-descriptions/suse/x86_64/{exc_description} \
         --target-dir /tmp/myimage

Consult the manual page of :file:`kiwi` for further details:
:ref:`db_commands_kiwi_synopsis`.


Building with the Open Build Service
------------------------------------

The Open Build Service (OBS) support profiles via the `multibuild
<https://openbuildservice.org/help/manuals/obs-reference-guide/cha.obs.multibuild.html>`_
feature. An example project using this feature is the
`openSUSE-Tumbleweed-JeOS
<https://build.opensuse.org/package/show/openSUSE:Factory/openSUSE-Tumbleweed-JeOS>`_
image.

To enable and use the profiles, follow these steps:

#. Add the following XML comment to your :file:`config.xml`:

   .. code:: xml

      <!-- OBS-Profiles: @BUILD_FLAVOR@ -->

   It must be added before the opening `<image>` element and after the
   `<?xml?>` element, e.g.:

   .. code:: xml

      <?xml version="1.0" encoding="utf-8"?>
      <!-- OBS-Profiles: @BUILD_FLAVOR@ -->
      <image schemaversion="{schema_version}" name="{exc_image_base_name}">
        <!-- snip -->
      </image>

#. Add a file :file:`_multibuild` into your package's repository with the
   following contents:

   .. code:: xml

      <multibuild>
        <flavor>profile_1</flavor>
        <flavor>profile_2</flavor>
      </multibuild>

   Add a line ``<flavor>$PROFILE</flavor>`` for each profile that
   you want OBS to build.


Note, by default, OBS excludes the build **without** any profile
enabled.

Running a build of a multibuild enabled repository via :file:`osc` can be
achieved via the `-M $PROFILE` flag:

.. code:: shell-session

   $ osc build -M $PROFILE
