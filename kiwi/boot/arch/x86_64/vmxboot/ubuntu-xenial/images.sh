#!/bin/sh
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

echo "Configure image: [$kiwi_iname]..."

#==========================================
# setup build day
#------------------------------------------
baseSetupBuildDay

#==========================================
# remove unneded kernel files
#------------------------------------------
debianStripKernel

#==========================================
# remove unneeded files
#------------------------------------------
debianStripInitrd

#==========================================
# umount
#------------------------------------------
baseCleanMount

exit 0
