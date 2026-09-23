.. _image-description:

Image Description
=================

KIWI builds images from a description directory. The directory describes what
packages to install, how to configure the target system, and which image types
should be created from the prepared root tree.

.. contents:: On this page
   :local:
   :depth: 2

Description Directory Layout
----------------------------

A description directory usually contains these files:

:file:`config.xml` or :file:`*.kiwi`
   The main image description. It defines metadata, repositories, packages,
   users, image types, and optional profile-specific variants.

:file:`root/` or :file:`root.tar.gz`
   Overlay content copied into the prepared root tree after package
   installation.

:file:`config.sh`
   An optional shell hook executed near the end of the prepare step.

:file:`images.sh`
   An optional shell hook executed at the beginning of the create step.

:file:`config-cdroot.tar[.*]`
   Optional additional files for ISO-style images, such as licenses or offline
   documentation.

Referenced archives, drivers, certificate files, and include files
   Additional resources referenced from the image description itself.

Minimal Example
---------------

The following description is enough to prepare a root tree and create a simple
image from it:

.. code:: xml

   <image schemaversion="{schema_version}" name="example">
     <description type="system">
       <author>Example Author</author>
       <contact>example@example.invalid</contact>
       <specification>Small example image</specification>
     </description>

     <preferences>
       <version>1.0.0</version>
       <packagemanager>zypper</packagemanager>
       <type image="oem" filesystem="ext4"/>
     </preferences>

     <repository type="rpm-md">
       <source path="{exc_repo_leap}"/>
     </repository>

     <packages type="image">
       <package name="bash"/>
     </packages>
   </image>

Top-Level Schema Layout
-----------------------

The :file:`kiwi/schema/kiwi.rnc` schema organizes the document below the
:ref:`sec.image` root element in this order:

.. list-table:: Top-level sections
   :widths: 18 34 32 16
   :header-rows: 1

   * - Section
     - Purpose
     - Main attributes and children
     - Reference
   * - ``<image>``
     - Root node of the description.
     - Required: ``name``, ``schemaversion``. Optional: ``displayname``, ``id``.
     - :ref:`sec.image`
   * - ``<include>``
     - Insert the inner content of another XML description file.
     - ``from`` URI attribute.
     - :ref:`sec.include`
   * - ``<certificates>``
     - Import additional CA certificates during the build.
     - ``target_distribution`` with one or more ``<certificate name="..."/>`` entries.
     - :ref:`sec.certificates`
   * - ``<description>``
     - Define human-readable identity and ownership.
     - ``type`` plus ``<author>``, ``<contact>``, ``<specification>``, and optional ``<license>``.
     - :ref:`sec.description`
   * - ``<preferences>``
     - Define versions, package manager behavior, and one or more image types.
     - Optional ``arch`` and ``profiles`` filters; includes ``<version>``, ``<packagemanager>``, ``<type>``, locale, timezone, themes, and release settings.
     - :ref:`sec.preferences`
   * - ``<profiles>``
     - Group conditional variants of the same description.
     - ``<profile>`` entries with ``name``, ``description``, ``arch``, ``import``, and optional ``<requires>``.
     - :ref:`sec.profiles`
   * - ``<users>``
     - Create or adjust users and groups in the image.
     - User records, group membership, home, shell, SSH keys, and password data.
     - :ref:`sec.users`
   * - ``<drivers>``
     - Add driver files to the image description.
     - File references with optional profile filters.
     - :ref:`sec.drivers`
   * - ``<strip>``
     - Remove files, libraries, or toolchains from the prepared root tree.
     - Optional ``type`` and matching entries for files or package content.
     - :ref:`sec.strip`
   * - ``<repository>``
     - Point KIWI to package sources.
     - Repository type, source type, priority, GPG behavior, credentials, and source URLs.
     - :ref:`sec.repository`
   * - ``<containers>``
     - Define container registry sources used by container-based builds.
     - One or more registry definitions and registry-specific credentials.
     - :ref:`sec.registry`
   * - ``<packages>``
     - Define what KIWI installs, deletes, or imports.
     - ``type``, optional ``profiles``, ``patternType``, ``bootstrap_package`` with package, collection, product, file, ignore, and archive entries.
     - :ref:`sec.packages`
   * - ``<extension>``
     - Attach custom XML namespaces validated outside the built-in schema.
     - Arbitrary namespaced content.
     - :ref:`sec.extension`

What to Configure First
-----------------------

When you create or review an image description, work in this order:

#. Start with :ref:`sec.description` so the image has clear ownership and a
   purpose.
#. Add at least one :ref:`sec.preferences` block with a version, package
   manager, and one or more :ref:`type definitions <sec.preferences>`.
#. Add the :ref:`sec.repository` entries that provide the packages needed for
   the build.
#. Add one or more :ref:`sec.packages` sections to populate the root tree.
#. Add optional sections such as :ref:`sec.users`, :ref:`sec.profiles`, or
   :ref:`sec.certificates` only when the use case needs them.

Common Patterns
---------------

Use profiles when one description should build multiple variants.

.. code:: xml

   <profiles>
     <profile name="VMX" description="VMware output"/>
     <profile name="CLOUD" description="Cloud output"/>
   </profiles>

   <preferences profiles="VMX">
     <version>1.0.0</version>
     <packagemanager>zypper</packagemanager>
     <type image="oem" format="vmdk" filesystem="ext4"/>
   </preferences>

   <preferences profiles="CLOUD">
     <version>1.0.0</version>
     <packagemanager>zypper</packagemanager>
     <type image="oem" format="qcow2" filesystem="ext4"/>
   </preferences>

Use multiple package sections to separate bootstrap packages from the final
image content.

.. code:: xml

   <packages type="bootstrap">
     <package name="filesystem"/>
     <package name="glibc-locale"/>
   </packages>

   <packages type="image">
     <package name="bash"/>
     <package name="vim"/>
   </packages>

Complete Schema Reference
-------------------------

The exhaustive element and attribute reference is documented in
:doc:`image_description/elements`. That reference follows the schema in
:file:`kiwi/schema/kiwi.rnc` and covers:

* every top-level section allowed below ``<image>``;
* all common and type-specific attributes of ``<preferences><type>``;
* repository, package, user, profile, bootloader, storage, and container
  substructures; and
* examples for the most frequently used sections.

Use this page as the guide to the structure of a description directory and use
:doc:`image_description/elements` as the schema-backed lookup for every valid
section and attribute.

.. toctree::
   :maxdepth: 1

   image_description/elements.rst
