#!/bin/bash
set -euxo pipefail

/usr/libexec/setup-etc-subvol

# test if there is a proper / mountpoint reference
findmnt -no UUID /

# show layout
findmnt
