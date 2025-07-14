#!/bin/bash
set -ex

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd

#==========================================
# remove package docs
#------------------------------------------
rm -rf /usr/share/doc/packages/*
rm -rf /usr/share/doc/manual/*
