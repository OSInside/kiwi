#!/bin/bash
# s390 network hardware setup
# ----
#======================================
# Functions...
#--------------------------------------
. /include

portname=VSWL2
readchannel=0.0.0800
writechannel=0.0.0801
datachannel=0.0.0802
qeth_up=1

#======================================
# Include kernel parameters
#--------------------------------------
includeKernelParameters

#======================================
# Bring the device online
#--------------------------------------
qeth_configure -p $portname -l \
    $readchannel $writechannel $datachannel $qeth_up

