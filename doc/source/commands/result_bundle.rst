kiwi-ng result bundle
=====================

.. _db_kiwi_result_bundle_synopsis:

SYNOPSIS
--------

.. code:: bash

   kiwi-ng [global options] service <command> [<args>]

   kiwi-ng result bundle -h | --help
   kiwi-ng result bundle --target-dir=<directory> --id=<bundle_id> --bundle-dir=<directory>
       [--zsync_source=<download_location>]
       [--package-as-rpm]
   kiwi-ng result bundle help

.. _db_kiwi_result_bundle_desc:

DESCRIPTION
-----------

Create result bundle from the image build results in the specified target
directory. Each result image will contain the specified bundle identifier
as part of its filename. Uncompressed image files will also become xz
compressed and a sha sum will be created from every result image.

.. _db_kiwi_result_bundle_opts:

OPTIONS
-------

--bundle-dir=<directory>

  directory containing the bundle results, compressed versions of
  image results and their sha sums

--id=<bundle_id>

  bundle id, could be a free form text and is appended to the image
  version information if present as part of the result image filename

--target-dir=<directory>

  directory containing the kiwi build results

--zsync_source=<download_location>

  Specify the download location from which the bundle file(s)
  can be fetched from. The information is effective if `zsync` is
  used to sync the bundle.

  * The zsync control file is only created for those bundle files
    which are marked for compression because in a {kiwi} build only those
    are meaningful for a partial binary file download.

  * It is expected that all files from a bundle are placed to the same
    download location

--package-as-rpm

  Take all result files and create an rpm package out of it
