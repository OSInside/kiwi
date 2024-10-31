#!/bin/bash

set -ex

#=======================================
# Create kernel links
#---------------------------------------
pushd boot
rm -f image initrd
ln -s image-* image
ln -s initrd-* initrd
popd
