#!/bin/bash
# called from /etc/udev/rules.d/99-live-kiwi.rules
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type mountIso >/dev/null 2>&1 || . /lib/kiwi-live-lib.sh

PATH=/usr/sbin:/usr/bin:/sbin:/bin

# init debug log file if wanted
setupDebugMode

# initialize profile environment
initialize

# load required kernel modules
loadKernelModules

# provide ISO when remote
root=$(ProvideIso "$1")

# device nodes and types
initGlobalDevices "$root"

# live options and their default values
initGlobalOptions

# prepare overlay for generated systemd LiveOS_rootfs service
declare isodiskdev=${isodiskdev}
if getargbool 0 rd.live.overlay.persistent && [ -n "${isodiskdev}" ]; then
    if ! preparePersistentOverlay; then
        warn "Failed to setup persistent write space !"
        warn "Falling back to temporary overlay"
        prepareTemporaryOverlay
    fi
else
    prepareTemporaryOverlay
fi

# mount ISO device
iso_mount_point=$(mountIso)

# mount squashfs compressed container
container_mount_point=$(
    mountCompressedContainerFromIso "${iso_mount_point}"
)

# mount readonly root filesystem from container
mountReadOnlyRootImageFromContainer "${container_mount_point}"

need_shutdown

exit 0
