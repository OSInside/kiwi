kiwi result bundle
==================

SYNOPSIS
--------

.. program-output:: bash -c "kiwi-ng result bundle | awk 'BEGIN{ found=1} /global options:/{found=0} {if (found) print }'"

DESCRIPTION
-----------

Create result bundle from the image build results in the specified target
directory. Each result image will contain the specified bundle identifier
as part of its filename. Uncompressed image files will also become xz
compressed and a sha sum will be created from every result image.

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
