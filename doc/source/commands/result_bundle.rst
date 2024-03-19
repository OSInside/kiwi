kiwi-ng result bundle
=====================

.. _db_kiwi_result_bundle_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng result bundle -h | --help
   kiwi-ng result bundle --target-dir=<directory> --id=<bundle_id> --bundle-dir=<directory>
       [--bundle-format=<format>]
       [--zsync_source=<download_location>]
       [--package-as-rpm]
   kiwi-ng result bundle help

.. _db_kiwi_result_bundle_desc:

DESCRIPTION
-----------

Create a result bundle from the image build in the specified target directory.
Each resulting image contains the specified bundle identifier as part of its
filename. Uncompressed image files are also compressed as an XZ archive. An SHA
checksum is generated for each resulting image.

.. _db_kiwi_result_bundle_opts:

OPTIONS
-------

--bundle-dir=<directory>

  Directory containing the bundle results, compressed versions of
  image results, and SHA checksum files.

--bundle-format=<format>

  Specify the bundle format to create the bundle. If provided,
  this setting will overwrite an eventually provided `bundle_format`
  attribute from the main image description. The format string
  can contain placeholders for the following elements:

  * %N : Image name
  * %P : Concatenated profile name (_)
  * %A : Architecture name
  * %I : Bundle ID
  * %T : Image build type name
  * %M : Image Major version number
  * %m : Image Minor version number
  * %p : Image Patch version number
  * %v : Image Version string

--id=<bundle_id>

  Bundle ID. It is a free-form text appended to the image
  version information as part of the result image filename.

--target-dir=<directory>

  Directory containing the {kiwi} build results.

--zsync_source=<download_location>

  Download location of the bundle file or files. Only relevant if `zsync` is
  used to sync the bundle.

  * The zsync control file is created for the bundle files marked for compression.

  * All files in a bundle must be stored in the same download location.

--package-as-rpm

  Create an RPM package containing the result files.
