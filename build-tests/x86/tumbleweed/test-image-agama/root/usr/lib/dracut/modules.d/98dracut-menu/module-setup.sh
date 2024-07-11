#!/bin/bash

# called by dracut
check() {
    return 0
}

# called by dracut
depends() {
    echo "dracut-systemd"

    return 0
}

installkernel() {
    return 0
}

# called by dracut
install() {
    inst_script "$moddir/dracut-cmdline-menu.sh" /bin/dracut-cmdline-menu

    inst_simple "$moddir/dracut-cmdline-menu.service" "$systemdsystemunitdir/dracut-cmdline-menu.service"
    $SYSTEMCTL -q --root "$initdir" add-wants initrd.target dracut-cmdline-menu.service

    inst_hook pre-pivot 98 "$moddir/save-cmdline.sh"
}
