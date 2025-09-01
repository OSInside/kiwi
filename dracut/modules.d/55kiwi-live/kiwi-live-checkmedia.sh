#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type runMediaCheck >/dev/null 2>&1 || . /lib/kiwi-live-lib.sh

if getargbool 0 mediacheck || getargbool 0 rd.live.check; then
    declare root=${root}
    initGlobalDevices "${root#live:}"
    runMediaCheck
fi
