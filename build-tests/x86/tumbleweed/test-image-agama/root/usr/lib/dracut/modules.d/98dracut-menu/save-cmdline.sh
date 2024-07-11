#! /bin/sh

[ -e /dracut-state.sh ] && . /dracut-state.sh

rm -f "$NEWROOT/etc/cmdline.d/10-liveroot.conf"

if [ -e /etc/cmdline.d/98-cmdline-menu.conf ] ; then
  cp /etc/cmdline.d/98-cmdline-menu.conf "$NEWROOT/etc/cmdline-menu.conf"
else
  echo "root=$root" >"$NEWROOT/etc/cmdline-menu.conf"
fi

echo "$CMDLINE" >"$NEWROOT/etc/cmdline-full.conf"
