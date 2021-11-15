#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3

# For image tests with an extra boot partition the
# kernel must not be a symlink to another area of
# the filesystem. Latest changes on SUSE changed the
# layout of the kernel which breaks every image with
# an extra boot partition
#
# All of the following is more than a hack and I
# don't like it all
#
# Complains and discussions about this please with
# the SUSE kernel team as we in kiwi can just live
# with the consequences of this change
#
pushd /

for file in /boot/* /boot/.*; do
    if [ -L ${file} ];then
        link_target=$(readlink ${file})
        if [[ ${link_target} =~ usr/lib/modules ]];then
            mv ${link_target} ${file}
        fi
    fi
done
