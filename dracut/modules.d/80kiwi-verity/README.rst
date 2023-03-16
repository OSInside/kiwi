kiwi-parse-verity
=================

Overview
--------

This tool is used to parse the information stored by
`Kiwi <https://osinside.github.io/kiwi/>`__ inside the unused space of a
disk partition when using a SquashFS root filesystem backed by
``dm-verity``. This data is stored at a known offset (generally 4096
bytes, or 1 block, from the end of the partition) and follows the layout
as described in the `Kiwi
documentation <https://osinside.github.io/kiwi/image_description/elements.html#preferences-type>`__
for the attribute ``embed_verity_metadata``.

Usage
-----

The following parameters are required in the Kiwi appliance description:

-  ``verity_blocks="all"``
-  ``embed_verity_metadata="true"``

The tool is used to pull a specific entry from the metadata and will
return that entry as plain text. It can be called using the following
syntax:

::

   kiwi-parse-verity -p <path to partition/device> -o <data type>

The data type is one of the entries stored by Kiwi inside the metadata,
such as ``root-hash`` or ``algorithm``. More information about the
parameters can be found by calling ``kiwi-parse-verity --help``.

You will probably need all of the metadata to successfully map the
device, as Kiwi sets up the ``dm-verity`` device with the
``--no-superblock`` option, which does not store any data inside the
partition, meaning all parameters need to be passed to it on the command
line.

Example
~~~~~~~

Detailed example of pulling all of the metadata from the partition and
mapping the device using ``veritysetup``:

::

   VERITY_ROOT=/dev/sda7

   ROOT_HASH=$(kiwi-parse-verity -p ${VERITY_ROOT} -o root-hash)
   ALGORITHM=$(kiwi-parse-verity -p ${VERITY_ROOT} -o algorithm)
   HASH_TYPE=$(kiwi-parse-verity -p ${VERITY_ROOT} -o hash-type)
   HASH_BLOCK_SIZE=$(kiwi-parse-verity -p ${VERITY_ROOT} -o hash-blocksize)
   DATA_BLOCK_SIZE=$(kiwi-parse-verity -p ${VERITY_ROOT} -o data-blocksize)
   SALT=$(kiwi-parse-verity -p ${VERITY_ROOT} -o salt)
   DATA_BLOCKS=$(kiwi-parse-verity -p ${VERITY_ROOT} -o data-blocks)
   HASH_START_BLOCK=$(kiwi-parse-verity -p ${VERITY_ROOT} -o hash-start-block)
   HASH_OFFSET=$(( ${HASH_START_BLOCK} * ${HASH_BLOCK_SIZE} ))

   veritysetup open ${VERITY_ROOT} verityRoot ${VERITY_ROOT} ${ROOT_HASH} \
       --no-superblock --hash ${ALGORITHM} --format ${HASH_TYPE} \
       --hash-block-size ${HASH_BLOCK_SIZE} --data-block-size ${DATA_BLOCK_SIZE} \
       --salt ${SALT} --data-blocks ${DATA_BLOCKS} --hash-offset ${HASH_OFFSET}

The device will then be mapped to ``/dev/mapper/verityRoot``.
