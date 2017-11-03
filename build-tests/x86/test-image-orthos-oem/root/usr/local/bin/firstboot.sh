#!/bin/sh

FLAG=/var/lib/firstboot/runme_at_boot

cd /tmp
for i in change_root_password.sh after_install.sh; do
    wget ftp://music.arch.suse.de/scripts/$i
    if [ -f ./$i ]; then
        chmod 755 ./$i
        ./$i
    else
        echo "$i could not be executed"
    fi
done

rm $FLAG
