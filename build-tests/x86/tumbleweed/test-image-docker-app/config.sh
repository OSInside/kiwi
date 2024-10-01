#!/bin/bash

set -ex

# preserve rm for final deletion of unneeded files
cp /usr/bin/rm /usr/bin/die_hard

# force uninstall unneded packages
rpm -e --nodeps crypto-policies pam permissions-config coreutils bash-sh libreadline8 terminfo-base sed permctl fillup system-user-root compat-usrmerge-tools permissions grep bash boost-license1_86_0 findutils gpg2 krb5 libassuan9 libaugeas0 libboost_thread1_86_0 libbrotlicommon1 libbrotlidec1 libbz2-1 libcom_err2 libcurl4 libfa1 libgcrypt20 libglib-2_0-0 libgpg-error0 libgpgme11 libidn2-0 libkeyutils1 libksba8 liblua5_4-5 liblzma5 libnghttp2-14-1.62.1 libnpth0 libpsl5 libsigc-2_0-0 libsolv-tools-base libsqlite3-0 libssh4 libssh-config libudev1 libunistring5 libusb-1_0-0 libverto1 libxml2-2 libyaml-cpp0_8 libzck1 libzypp pinentry rpm rpm-config-SUSE zypper

# delete rpm database and more...
die_hard -r /usr/lib/sysimage/rpm /usr/bin/die_hard
