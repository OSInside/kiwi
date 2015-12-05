#================
# FILE          : functions.sh
#----------------
# PROJECT       : openSUSE Build-Service
# COPYRIGHT     : (c) 2006 SUSE LINUX Products GmbH, Germany
#               :
# AUTHOR        : Marcus Schaefer <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : This module contains common used functions
#               : for the suse linuxrc and preinit boot image
#               : files
#               : 
#               :
# STATUS        : Development
#----------------
#======================================
# Exports (General)
#--------------------------------------
export BOOTABLE_FLAG="$(echo -ne '\x80')"
export ELOG_FILE=/var/log/boot.kiwi
export TRANSFER_ERRORS_FILE=/tmp/transfer.errors
export UFONT=/usr/share/fbiterm/fonts/b16.pcf.gz
export CONSOLE_FONT=/usr/share/kbd/consolefonts/default8x16.gz
export HYBRID_PERSISTENT_FS=btrfs
export HYBRID_PERSISTENT_ID=83
export HYBRID_PERSISTENT_DIR=/read-write
export UTIMER_INFO=/dev/utimer
export bootLoaderOK=0
export enablePlymouth=1
export IFS_ORIG=$IFS
export MEDIACHECK_OK_TIMER=5
export partitionerWriteStatus=0

#======================================
# lookup
#--------------------------------------
function lookup {
    bash -c "PATH=$PATH:/sbin:/usr/sbin:/bin:/usr/bin type -p $1"
}

#======================================
# Exports (console)
#--------------------------------------
test -z "$ELOG_BOOTSHELL" && export ELOG_BOOTSHELL=/dev/tty2
test -z "$ELOG_EXCEPTION" && export ELOG_EXCEPTION=/dev/console

#======================================
# Exports (General)
#--------------------------------------
test -z "$RECOVERY_THEME"     && export RECOVERY_THEME=openSUSE
test -z "$splitroot_size"     && export splitroot_size=512
test -z "$arch"               && export arch=$(uname -m)
test -z "$haveDASD"           && export haveDASD=0
test -z "$haveZFCP"           && export haveZFCP=0
test -z "$ELOG_STOPPED"       && export ELOG_STOPPED=0
test -z "$PARTITIONER"        && export PARTITIONER=parted
test -z "$DEFAULT_VGA"        && export DEFAULT_VGA=0x314
test -z "$HAVE_MODULES_ORDER" && export HAVE_MODULES_ORDER=1
test -z "$DIALOG_LANG"        && export DIALOG_LANG=ask
test -z "$TERM"               && export TERM=linux
test -z "$LANG"               && export LANG=en_US.utf8
test -z "$UTIMER"             && export UTIMER=0
test -z "$PARTED_HAVE_ALIGN"  && export PARTED_HAVE_ALIGN=0
test -z "$PARTED_HAVE_MACHINE"&& export PARTED_HAVE_MACHINE=0
test -z "$DHCPCD_HAVE_PERSIST"&& export DHCPCD_HAVE_PERSIST=1
if lookup parted &>/dev/null;then
    if parted -h | grep -q '\-\-align';then
        export PARTED_HAVE_ALIGN=1
    fi
    if parted -h | grep -q '\-\-machine';then
        export PARTED_HAVE_MACHINE=1
    fi
    if [ $PARTED_HAVE_MACHINE -eq 0 ];then
        export PARTITIONER=unsupported
    fi
fi
if lookup dhcpcd &>/dev/null;then
    if dhcpcd -p 2>&1 | grep -q 'Usage';then
        export DHCPCD_HAVE_PERSIST=0
    fi
fi

#======================================
# Exports (arch specific)
#--------------------------------------
if [[ $arch =~ ppc64 ]];then
    test -z "$loader" && export loader=yaboot
elif [[ $arch =~ arm ]];then
    test -z "$loader" && export loader=uboot
elif [[ $arch =~ s390 ]];then
    test -z "$loader" && export loader=zipl
else
    test -z "$loader" && export loader=grub
fi

#======================================
# Exports boot options
#--------------------------------------
failsafe="ide=nodma apm=off noresume edd=off"
failsafe="$failsafe powersaved=off nohz=off"
failsafe="$failsafe highres=off processsor.max+cstate=1"
failsafe="$failsafe nomodeset x11failsafe"

#======================================
# hideSplash
#--------------------------------------
function hideSplash {
    # /.../
    # Only in case of one active console kiwi hides
    # the splash screen for it to allow interactive dialog
    # sessions on this console. In any other case the user
    # can control a custom behavior using the handleSplash
    # hook called at the end of this function
    # ----
    local IFS=$IFS_ORIG
    local console_count=$(activeConsoles)
    if [ $console_count -eq 1 ];then
        test -e /proc/splash && echo verbose > /proc/splash
        if lookup plymouthd &>/dev/null;then
            plymouth hide-splash
            # reset tty after plymouth messed with it
            consoleInit
        fi
    fi
    runHook handleSplash "$@"
}

#======================================
# Dialog
#--------------------------------------
function Dialog {
    local IFS=$IFS_ORIG
    local code=1
    export DIALOG_CANCEL=1
    hideSplash
cat > /tmp/fbcode << EOF
dialog \
    --ok-label "$TEXT_OK" \
    --cancel-label "$TEXT_CANCEL" \
    --yes-label "$TEXT_YES" \
    --no-label "$TEXT_NO" \
    --exit-label "$TEXT_EXIT" \
    $@
echo \$? > /tmp/fbcode
EOF
    if FBOK;then
        fbiterm -m $UFONT -- bash -e /tmp/fbcode
    else
        bash -e /tmp/fbcode
    fi
    code=$(cat /tmp/fbcode)
    return $code
}
#======================================
# Debug
#--------------------------------------
function Debug {
    # /.../
    # print message if variable DEBUG is set to 1
    # -----
    local IFS=$IFS_ORIG
    if test "$DEBUG" = 1;then
        echo "+++++> $1"
    fi
}
#======================================
# Echo
#--------------------------------------
function Echo {
    # /.../
    # print a message to the controling terminal
    # ----
    local IFS=$IFS_ORIG
    if [ $ELOG_STOPPED = 0 ];then
        set +x
    fi
    if [ ! $UTIMER = 0 ] && kill -0 $UTIMER &>/dev/null;then
        kill -HUP $UTIMER
        local prefix=$(cat $UTIMER_INFO)
    else
        local prefix="===>"
    fi
    local option=""
    local optn=""
    local opte=""
    while getopts "bne" option;do
        case $option in
            b) prefix="    " ;;
            n) optn="-n" ;;
            e) opte="-e" ;;
            *) echo "Invalid argument: $option" ;;
        esac
    done
    shift $(($OPTIND - 1))
    if [ $ELOG_STOPPED = 0 ];then
        set -x
    fi
    echo $optn $opte "$prefix $1"
    if [ $ELOG_STOPPED = 0 ];then
        set +x
    fi
    OPTIND=1
    if [ $ELOG_STOPPED = 0 ];then
        set -x
    fi
}
#======================================
# WaitKey
#--------------------------------------
function WaitKey {
    # /.../
    # if DEBUG is set wait for ENTER to continue
    # ----
    local IFS=$IFS_ORIG
    if test "$DEBUG" = 1;then
        Echo -n "Press ENTER to continue..."
        read
    fi
}
#======================================
# importFile
#--------------------------------------
function importFile {
    # /.../
    # import the config.<MAC> style format. the function
    # will export each entry of the file as variable into
    # the current shell environment
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    # create clean input, no empty lines and comments
    cat - | grep -v '^$' | grep -v '^[ \t]*#' > /tmp/srcme
    # remove start/stop quoting from values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=[\"']\(.*\)[\"']#\1=\2#" /tmp/srcme
    # remove backslash quotes if any
    sed -i -e s"#\\\\\(.\)#\1#g" /tmp/srcme
    # quote simple quotation marks
    sed -i -e s"#'\+#'\\\\''#g" /tmp/srcme
    # add '...' quoting to values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=\(.*\)#$prefix\1='\2'#" /tmp/srcme
    source /tmp/srcme &>/dev/null
    while read line;do
        key=$(echo "$line" | cut -d '=' -f1)
        eval "export $key" &>/dev/null
    done < /tmp/srcme
    if [ ! -z "$ERROR_INTERRUPT" ];then
        Echo -e "$ERROR_INTERRUPT"
        systemException "*** interrupted ****" "shell"
    fi
}
#======================================
# unsetFile
#--------------------------------------
function unsetFile {
    # /.../
    # unset variables specified within the given file.
    # the file must be in the config.<MAC> style format
    # ----
    local IFS="
    "
    local prefix=$1 #change name of key with a prefix
    while read line;do
        echo $line | grep -qi "^#" && continue
        key=`echo "$line" | cut -d '=' -f1`
        if [ -z "$key" ];then
            continue
        fi
        Debug "unset $prefix$key"
        eval unset "$prefix$key"
    done
}
#======================================
# condenseConfigData
#--------------------------------------
function condenseConfigData {
    # /.../
    # if multiple same config files (config files with same deployment path)
    # are present on the CONF line,
    # only last one will be kept (this preserves compatibility)
    # ----
    local IFS=","
    local conf=( $1 )
    local cconf
    local sep=''
    for (( i=0; i<${#conf[@]}; i++ ));do
        local configDest=`echo "${conf[$i]}" | cut -d ';' -f 2`
        if test ! -z $configDest;then
            local copythis=1
            for (( j=i+1; j<${#conf[@]}; j++ ));do
                local cmpconfigDest=`echo "${conf[$j]}" | cut -d ';' -f 2`
                if [ "$cmpconfigDest" = "$configDest" ];then
                    copythis=0
                    break
                fi
            done
            [ $copythis -eq '1' ] && cconf="${cconf}${sep}${conf[$i]}"
            sep=$IFS
        fi
    done
    echo "$cconf"
}
#======================================
# systemException
#--------------------------------------
function systemException {
    # /.../
    # print a message to the controling terminal followed
    # by an action. Possible actions are reboot, wait, shutdown,
    # and opening a shell
    # ----
    local IFS=$IFS_ORIG
    set +x
    local what=$2
    local nuldev=/dev/null
    local ttydev=$ELOG_EXCEPTION
    local prefix=/mnt
    for dev in $nuldev $prefix/$nuldev; do
        if [ -e $dev ];then
            nuldev=$dev; break
        fi
    done
    for dev in $ttydev $prefix/$ttydev; do
        if [ -e $dev ];then
            ttydev=$dev; break
        fi
    done
    hideSplash
    if [ $enablePlymouth -eq 1 ]; then
        plymouth quit
    fi
    if [ $what = "reboot" ];then
        if cat /proc/cmdline 2>/dev/null | grep -qi "kiwidebug=1";then
            what="shell"
        fi
    fi
    runHook preException "$@"
    Echo -e "$1"
    case "$what" in
    "reboot")
        # in order to see all log information in case of a reboot exception
        # we print the current log contents to the console. On systems like
        # public clouds the console information is stored and provided to
        # the user. Thus it makes sense to be verbose here
        cat $ELOG_FILE
        Echo "rebootException: reboot in 120 sec..."; sleep 120
        /sbin/reboot -f -i >$nuldev
    ;;
    "wait")
        Echo "waitException: waiting for ever..."
        while true;do sleep 100;done
    ;;
    "waitkey")
        Echo "waitException: Press any key to continue: "
        read
    ;;
    "shell")
        if [ ! -z "$DROPBEAR_PID" ] && [ ! -z "$IPADDR" ];then
            Echo "You can connect via ssh to this system"
            Echo "ssh root@${IPADDR}"
        fi
        echo reset > /root/.bashrc
        setctsid $ttydev sulogin -e $ttydev
    ;;
    "user_reboot")
        Echo "reboot triggered by user"
        Echo "reboot in 30 sec..."; sleep 30
        /sbin/reboot -f -i >$nuldev
    ;;
    *)
        Echo "unknownException..."
    ;;
    esac
}
#======================================
# copyDevices
#--------------------------------------
function copyDeviceNodes {
    local IFS=$IFS_ORIG
    local search=$1
    local prefix=$2
    local dtype
    local major
    local minor
    local perms
    if [ -z "$search" ];then
        search=/dev
    fi
    pushd $search >/dev/null
    for i in *;do
        if [ -e $prefix/$i ];then
            continue
        fi
        if [ -b $i ];then
            dtype=b
        elif [ -c $i ];then
            dtype=c
        elif [ -p $i ];then
            dtype=p
        else
            continue
        fi
        info=`stat $i -c "0%a:0x%t:0x%T"`
        major=`echo $info | cut -f2 -d:`
        minor=`echo $info | cut -f3 -d:`
        perms=`echo $info | cut -f1 -d:`
        if [ $dtype = "p" ];then
            mknod -m $perms $prefix/$i $dtype
        else
            mknod -m $perms $prefix/$i $dtype $major $minor
        fi
    done
    popd >/dev/null
}
#======================================
# createInitialDevices
#--------------------------------------
function createInitialDevices {
    local IFS=$IFS_ORIG
    local prefix=$1
    #======================================
    # create master dev dir
    #--------------------------------------
    mkdir -p $prefix
    if [ ! -d $prefix ];then
        return
    fi
    #======================================
    # mount devtmpfs or tmpfs
    #--------------------------------------
    if mount -t devtmpfs -o mode=0755,nr_inodes=0 devtmpfs $prefix; then
        export have_devtmpfs=true
    else
        export have_devtmpfs=false
        mount -t tmpfs -o mode=0755,nr_inodes=0 udev $prefix
        mknod -m 0666 $prefix/tty     c 5 0
        mknod -m 0600 $prefix/console c 5 1
        mknod -m 0666 $prefix/ptmx    c 5 2
        mknod -m 0666 $prefix/null c 1 3
        mknod -m 0600 $prefix/kmsg c 1 11
        mknod -m 0660 $prefix/snapshot c 10 231
        mknod -m 0666 $prefix/random c 1 8
        mknod -m 0644 $prefix/urandom c 1 9
    fi
    #======================================
    # mount shared mem tmpfs
    #--------------------------------------
    mkdir -m 1777 $prefix/shm
    mount -t tmpfs -o mode=1777 tmpfs $prefix/shm
    #======================================
    # mount udev db tmpfs
    #--------------------------------------
    mkdir -p -m 0755 /run
    mkdir -p -m 0755 /var/run
    if [[ ! $kiwi_iname =~ SLE.11 ]];then
        mount -t tmpfs -o mode=0755,nodev,nosuid tmpfs /run
        mount --bind /run /var/run
    fi
    #======================================
    # mount devpts tmpfs
    #--------------------------------------
    mkdir -m 0755 $prefix/pts
    mount -t devpts -o mode=0620,gid=5 devpts $prefix/pts
    #======================================
    # link default descriptors
    #--------------------------------------
    ln -s /proc/self/fd $prefix/fd
    ln -s fd/0 $prefix/stdin
    ln -s fd/1 $prefix/stdout
    ln -s fd/2 $prefix/stderr
    #======================================
    # create directories in /run
    #--------------------------------------
    mkdir -p -m 0755 /run/lock
    mkdir -p -m 0755 /run/log
}
#======================================
# mount_rpc_pipefs
#--------------------------------------
function mount_rpc_pipefs {
    local IFS=$IFS_ORIG
    # See if the file system is there yet
    if [ ! -e /var/lib/nfs/rpc_pipefs ];then
        return 0
    fi
    case `stat -c "%t" -f /var/lib/nfs/rpc_pipefs 2>/dev/null` in
    *67596969*)
        return 0;;
    esac
    mount -t rpc_pipefs rpc_pipefs /var/lib/nfs/rpc_pipefs
}
#======================================
# umount_rpc_pipefs
#--------------------------------------
function umount_rpc_pipefs {
    local IFS=$IFS_ORIG
    # See if the file system is there
    case `stat -c "%t" -f /var/lib/nfs/rpc_pipefs 2>/dev/null` in
    *67596969*)
        umount /var/lib/nfs/rpc_pipefs
    esac
}
#======================================
# setupNFSServices
#--------------------------------------
function setupNFSServices {
    local IFS=$IFS_ORIG
    mount_rpc_pipefs
    if [ -x /sbin/rpcbind ];then
        startproc /sbin/rpcbind
    fi
    if [ -x /usr/sbin/rpc.statd ];then
        startproc /usr/sbin/rpc.statd --no-notify
    fi
    if [ -x /usr/sbin/rpc.idmapd ];then
        startproc /usr/sbin/rpc.idmapd
    fi
}
#======================================
# mountSystemFilesystems
#--------------------------------------
function mountSystemFilesystems {
    local IFS=$IFS_ORIG
    if [ ! -e /proc/cmdline ];then
        mount -t proc  proc   /proc
    fi
    if [ ! -e /sys/kernel ];then
        mount -t sysfs sysfs  /sys
    fi
    if [ -e /run/initramfs/shutdown ];then
        chmod u+x /run/initramfs/shutdown
    fi
}
#======================================
# umountSystemFilesystems
#--------------------------------------
function umountSystemFilesystems {
    local IFS=$IFS_ORIG
    umount_rpc_pipefs
    umount /dev/pts &>/dev/null
    umount /sys     &>/dev/null
    umount /proc    &>/dev/null
}
#======================================
# createFramebufferDevices
#--------------------------------------
function createFramebufferDevices {
    local IFS=$IFS_ORIG
    if [ -f /proc/fb ]; then
        while read fbnum fbtype; do
            if [ $(($fbnum < 32)) ] ; then
                if [ ! -c /dev/fb$fbnum ];then
                    Echo "Creating framebuffer device: /dev/fb$fbnum"
                    mknod -m 0660 /dev/fb$fbnum c 29 $fbnum
                fi
            fi
        done < /proc/fb
    fi
}
#======================================
# errorLogStop
#--------------------------------------
function errorLogStop {
    local IFS=$IFS_ORIG
    set +x
    export ELOG_STOPPED=1
    exec < $ELOG_EXCEPTION &> $ELOG_EXCEPTION
}
#======================================
# errorLogContinue
#--------------------------------------
function errorLogContinue {
    local IFS=$IFS_ORIG
    exec 2>>$ELOG_FILE
    exec < $ELOG_EXCEPTION > $ELOG_EXCEPTION
    export ELOG_STOPPED=0
    set -x
}
#======================================
# errorLogStart
#--------------------------------------
function errorLogStart {
    # /.../
    # Log all errors and the debug information to the
    # file set in ELOG_FILE.
    # ----
    local IFS=$IFS_ORIG
    local umountProc=0
    if [ ! -f $ELOG_FILE ];then
        #======================================
        # Header for main stage log
        #--------------------------------------
        echo "KIWI Log:" >> $ELOG_FILE
    else
        #======================================
        # Header for pre-init stage log
        #--------------------------------------
        startUtimer
        echo "KIWI PreInit Log" >> $ELOG_FILE
    fi
    #======================================
    # Contents of .profile environment
    #--------------------------------------
    if [ -f .profile ];then
        echo "KIWI .profile contents:" >> $ELOG_FILE
        cat .profile >> $ELOG_FILE
    fi
    #======================================
    # Redirect stderr to ELOG_FILE
    #--------------------------------------
    exec 2>>$ELOG_FILE
    #======================================
    # Mount proc for cmdline quiet check
    #--------------------------------------
    if [ ! -e /proc/cmdline ];then
        mount -t proc proc /proc
        umountProc=1
    fi
    if cat /proc/cmdline | grep -qi "quiet";then
        #======================================
        # Redirect/Clean stdout if quiet is set
        #--------------------------------------
        exec >/dev/null
        if [ -x /usr/bin/setterm ];then
            setterm -clear all
            setterm -background black
        fi
    else
        #======================================
        # Redirect stdout to console
        #--------------------------------------
        exec < $ELOG_EXCEPTION > $ELOG_EXCEPTION
    fi
    #======================================
    # Clean proc
    #--------------------------------------
    if [ $umountProc -eq 1 ];then
        umount /proc
    fi
    #======================================
    # Enable shell debugging
    #--------------------------------------
    set -x
}
#======================================
# udevPending
#--------------------------------------
function udevPending {
    local IFS=$IFS_ORIG
    local umountProc=0
    if [ ! -e /proc/cmdline ];then
        mount -t proc proc /proc
        umountProc=1
    fi
    local timeout=30
    local udevadmExec=$(lookup udevadm 2>/dev/null)
    if [ -x $udevadmExec ];then
        $udevadmExec settle --timeout=$timeout
    else
        # udevsettle exists on old distros and is not
        # affected by the move from sbin to usr
        /sbin/udevsettle --timeout=$timeout
    fi
    if [ $umountProc -eq 1 ];then
        umount /proc
    fi
}
#======================================
# udevTrigger
#--------------------------------------
function udevTrigger {
    local IFS=$IFS_ORIG
    local udevadmExec=$(lookup udevadm 2>/dev/null)
    if [ -x $udevadmExec ];then
        $udevadmExec trigger
    else
        /sbin/udevtrigger
    fi
}
#======================================
# udevSystemStart
#--------------------------------------
function udevSystemStart {
    # /.../
    # start udev daemon
    # ----
    local IFS=$IFS_ORIG
    local udev_bin=/usr/lib/systemd/systemd-udevd
    if [ ! -x $udev_bin ];then
        udev_bin=/sbin/udevd
    fi
    if [ ! -x $udev_bin ];then
        udev_bin=/lib/udev/udevd
    fi
    if [ ! -x $udev_bin ];then
        systemException \
            "Can't find udev daemon" \
        "reboot"
    fi
    $udev_bin --daemon
    export UDEVD_PID=$(pidof $udev_bin | tr ' ' ,)
}
#======================================
# udevSystemStop
#--------------------------------------
function udevSystemStop {
    # /.../
    # stop udev while in pre-init phase.
    # ----
    local IFS=$IFS_ORIG
    local udevadmExec=$(lookup udevadm 2>/dev/null)
    local umountProc=0
    if [ ! -e "/proc/mounts" ];then
        mount -t proc proc /proc
        umountProc=1
    fi
    if [ -x $udevadmExec ];then
        # ignore error messages here, because if the process is not
        # stopped properly here, it will be killed the hard way a few
        # lines down
        $udevadmExec control --exit &>/dev/null
    fi
    if [ -z "$UDEVD_PID" ];then
        . /iprocs
    fi
    local IFS=,
    for p in $UDEVD_PID; do
        if kill -0 $p &>/dev/null;then
            udevPending
            kill $p
        fi
    done
    if [ $umountProc -eq 1 ];then
        umount /proc
    fi
}
#======================================
# udevStart
#--------------------------------------
function udevStart {
    # /.../
    # start the udev daemon.
    # ----
    local IFS=$IFS_ORIG
    #======================================
    # Check time according to build day
    #--------------------------------------
    if [ -f /build_day ];then
        importFile < /build_day
        current_day="$(LC_ALL=C date -u '+%Y%m%d')"
        if [ "$current_day" -lt "$build_day" ] ; then
            LC_ALL=C date -us "$build_day"
            sleep 3
            export SYSTEM_TIME_INCORRECT=$current_day
        fi
    fi
    #======================================
    # Check for modules.order
    #--------------------------------------
    if ! ls /lib/modules/*/modules.order &>/dev/null;then
        # /.../
        # without modules.order in place we prevent udev from loading
        # the storage modules because it does not make a propper
        # choice if there are multiple possible modules available.
        # Example:
        # udev prefers ata_generic over ata_piix but the hwinfo
        # order is ata_piix first which also seems to make more
        # sense.
        # -----
        rm -f /etc/udev/rules.d/*-drivers.rules
        rm -f /lib/udev/rules.d/*-drivers.rules
        HAVE_MODULES_ORDER=0
    fi
    #======================================
    # Start the daemon
    #--------------------------------------
    # static nodes
    createInitialDevices /dev
    # load modules required before udev
    moduleLoadBeforeUdev
    # start the udev daemon
    udevSystemStart
    echo UDEVD_PID=$UDEVD_PID >> /iprocs
    # trigger events for all devices
    udevTrigger
    # wait for events to finish
    udevPending
    # init console
    consoleInit
    # start plymouth if it exists and enabled
    for o in $(cat /proc/cmdline) ; do
        case "$o" in
            plymouth.enable=0*|rd.plymouth=0*)
            enablePlymouth=0
            break
            ;;
        esac
    done
    if [ $enablePlymouth -eq 1 ]; then
        startPlymouth
    fi
}
#======================================
# moduleLoadBeforeUdev
#--------------------------------------
function moduleLoadBeforeUdev {
    # /.../
    # load modules which have to be loaded before the
    # udev daemon is started in this function
    # ----
    loadAGPModules
}
#======================================
# loadAGPModules
#--------------------------------------
function loadAGPModules {
    local IFS=$IFS_ORIG
    local krunning=$(uname -r)
    for i in /lib/modules/$krunning/kernel/drivers/char/agp/*; do
        test -e $i || continue
        modprobe $(echo $i | sed "s#.*\\/\\([^\\/]\\+\\).ko#\\1#")
    done
}
#======================================
# udevKill
#--------------------------------------
function udevKill {
    local IFS=$IFS_ORIG
    udevSystemStop
}
#======================================
# activeConsoles
#--------------------------------------
function activeConsoles {
    local IFS=$IFS_ORIG
    for i in $(cat /sys/class/tty/console/active 2>/dev/null);do
        echo $i
    done | wc -l
}
#======================================
# consoleInit
#--------------------------------------
function consoleInit {
    local IFS=$IFS_ORIG
    local udev_console=/lib/udev/console_init
    local systemd_console=/usr/lib/systemd/systemd-vconsole-setup
    if [ -x $udev_console ];then
        $udev_console /dev/console
    elif [ -x $systemd_console ];then
        $systemd_console
    fi
}
#======================================
# startPlymouth
#--------------------------------------
function startPlymouth {
    local IFS=$IFS_ORIG
    local consoledev
    if lookup plymouthd &>/dev/null;then
        # first trigger graphics subsystem
        udevadm trigger --action=add --attr-match=class=0x030000 &>/dev/null
        # next trigger graphics and tty subsystem
        udevadm trigger --action=add --subsystem-match=graphics \
            --subsystem-match=drm --subsystem-match=tty &>/dev/null
        udevadm settle --timeout=30
        mkdir --mode 755 /run/plymouth
        consoleInit
        plymouth-set-default-theme $kiwi_splash_theme &>/dev/null
        plymouthd --attach-to-session --pid-file /run/plymouth/pid &>/dev/null
        plymouth show-splash &>/dev/null
        # reset tty after plymouth messed with it
        consoleInit
    fi
}
#======================================
# startDropBear
#--------------------------------------
function startDropBear {
    # /.../
    # start dropbear ssh server if installed
    # ---
    local IFS=$IFS_ORIG
    local auth_keys="/root/.ssh/authorized_keys"
    if [ -z "$kiwidebug" ];then
        return
    fi
    if lookup dropbear &>/dev/null;then
        mkdir -p /root/.ssh
        fetchFile KIWI/debug_ssh.pub $auth_keys
        if [ ! -e $auth_keys ]; then
            return
        fi
        mkdir -p /etc/dropbear
        if [ ! -f /etc/dropbear/dropbear_dss_host_key ];then
            dropbearkey -t dss -f /etc/dropbear/dropbear_dss_host_key
        fi
        if [ ! -f /etc/dropbear/dropbear_rsa_host_key ];then
            dropbearkey -t rsa -f /etc/dropbear/dropbear_rsa_host_key
        fi
        Echo "Starting dropbear ssh server"
        dropbear
        export DROPBEAR_PID=$(pidof /usr/sbin/dropbear)
        echo DROPBEAR_PID=$DROPBEAR_PID >> /iprocs
    fi
}
#======================================
# installBootLoader
#--------------------------------------
function installBootLoader {
    # /.../
    # generic function to install the boot loader.
    # The selection of the bootloader happens according to
    # the architecture of the system
    # ----
    local IFS=$IFS_ORIG
    local arch=$(uname -m)
    case $arch-$loader in
        i*86-grub)       installBootLoaderGrub ;;
        x86_64-grub)     installBootLoaderGrub ;;
        i*86-grub2)      installBootLoaderGrub2 ;;
        s390*-grub2)     installBootLoaderGrub2 ;;
        x86_64-grub2)    installBootLoaderGrub2 ;;
        ppc64*-grub2)    installBootLoaderGrub2 ;;
        ppc*)            installBootLoaderYaboot ;;
        arm*)            installBootLoaderUBoot ;;
        i*86-syslinux)   installBootLoaderSyslinux ;;
        x86_64-syslinux) installBootLoaderSyslinux ;;
        i*86-extlinux)   installBootLoaderSyslinux ;;
        x86_64-extlinux) installBootLoaderSyslinux ;;
        s390-zipl)       installBootLoaderS390 ;;
        s390x-zipl)      installBootLoaderS390 ;;
        s390x-grub2_s390x_emu)  installBootLoaderS390Grub ;;
        aarch64-uboot)   installBootLoaderUBoot ;;
        aarch64-grub2)   installBootLoaderGrub2 ;;
        *)
        systemException \
            "*** boot loader install for $arch-$loader not implemented ***" \
        "reboot"
    esac
    #
    # Warning message is disabled because sometimes the message
    # can't be displayed on the console which leads to a stopped
    # system but the user has no clue why
    #
    #if [ ! $? = 0 ];then
    #    if lookup dialog &>/dev/null;then
    #        Dialog \
    #            --backtitle \"$TEXT_BOOT_SETUP_FAILED\" \
    #            --msgbox "\"$TEXT_BOOT_SETUP_FAILED_INFO\"" 10 70
    #    else
    #        systemException \
    #            "$TEXT_BOOT_SETUP_FAILED\n\n$TEXT_BOOT_SETUP_FAILED_INFO" \
    #        "waitkey"
    #    fi
    #fi
    case $arch in
        i*386|x86_64)
            masterBootID=$(printf 0x%04x%04x $RANDOM $RANDOM)
            Echo "writing new MBR ID to master boot record: $masterBootID"
            echo $masterBootID > /boot/mbrid
            masterBootIDHex=$(echo $masterBootID |\
                sed 's/^0x\(..\)\(..\)\(..\)\(..\)$/\\x\4\\x\3\\x\2\\x\1/')
            echo -e -n $masterBootIDHex | dd of=$imageDiskDevice \
                bs=1 count=4 seek=$((0x1b8))
            ;;
        *)
            echo "skiped writing MBR ID for $arch"
            ;;
    esac
}
#======================================
# installBootLoaderRecovery
#--------------------------------------
function installBootLoaderRecovery {
    # /.../
    # generic function to install the boot loader into
    # the recovery partition. The selection of the bootloader
    # happens according to the architecture of the system
    # ----
    local IFS=$IFS_ORIG
    local arch=$(uname -m)
    case $arch-$loader in
        i*86-grub)       installBootLoaderGrubRecovery ;;
        x86_64-grub)     installBootLoaderGrubRecovery ;;
        i*86-grub2)      installBootLoaderGrub2Recovery ;;
        x86_64-grub2)    installBootLoaderGrub2Recovery ;;
        s390*-grub2)     installBootLoaderGrub2Recovery ;;
        i*86-syslinux)   installBootLoaderSyslinuxRecovery ;;
        x86_64-syslinux) installBootLoaderSyslinuxRecovery ;;
        i*86-extlinux)   installBootLoaderSyslinuxRecovery ;;
        x86_64-extlinux) installBootLoaderSyslinuxRecovery ;;
        s390-zipl)       installBootLoaderS390Recovery ;;
        s390x-zipl)      installBootLoaderS390Recovery ;;
        *)
        systemException \
            "*** boot loader setup for $arch-$loader not implemented ***" \
        "reboot"
    esac
}
#======================================
# installBootLoaderUBoot
#--------------------------------------
function installBootLoaderUBoot {
    # /.../
    # installation of uboot can't be done in a generic
    # way because each arm board behaves differently.
    # Thus we are only calling a hook script here
    # ----
    local IFS=$IFS_ORIG
    if [ "$kiwi_bootloader" = "berryboot" ];then
        runHook installBerryBoot "$@"
    else
        runHook installUBoot "$@"
    fi
}
#======================================
# installBootLoaderS390Grub
#--------------------------------------
function installBootLoaderS390Grub {
    # /.../
    # Create/Delete
    # - create active_devices.txt
    # - delete kiwi initrd/kernel .vmx files
    # Run grub2-mkconfig
    # - create new boot/grub2/grub.cfg
    # Run grub2-install
    # - creates a new boot/zipl/config
    # - creates zipl initrd which loads grub2/kexec
    # - install zipl
    # ----
    local IFS=$IFS_ORIG
    local confTool=grub2-mkconfig
    local instTool=grub2-install
    local confFile_grub=/boot/grub2/grub.cfg
    local active_devs=/boot/zipl/active_devices.txt
    local deviceID=$(cat /sys/firmware/ipl/device)
    #======================================
    # mount zipl jump partition
    #--------------------------------------
    if [ ! -z "$kiwi_JumpPart" ];then
        local jdev=$(ddn $imageDiskDevice $kiwi_JumpPart)
        local label=$(blkid $jdev -s LABEL -o value)
        if [ "$label" = "ZIPL" ];then
            mkdir -p /boot/zipl
            if ! mount $jdev /boot/zipl;then
                Echo "Failed to mount zipl boot partition"
                return 1
            fi
        fi
    fi
    #======================================
    # Create active devices information
    #--------------------------------------
    echo $deviceID > $active_devs
    #======================================
    # create grub2 configuration
    #--------------------------------------
    if ! lookup $confTool &>/dev/null;then
        Echo "System image doesn't provide $confTool"
        Echo "Can't create bootloader configuration"
        return 1
    fi
    $confTool > $confFile_grub
    if [ ! $? = 0 ];then
        Echo "Failed to create grub2 boot configuration"
        return 1
    fi
    #======================================
    # Run grub2-install
    #--------------------------------------
    if ! lookup $instTool &>/dev/null;then
        Echo "System image doesn't provide $instTool"
        Echo "Can't install bootloader"
        return 1
    fi
    if ! $instTool;then
        Echo "Failed to install bootloader"
        return 1
    fi
    #======================================
    # Delete kiwi initrd files
    #--------------------------------------
    rm -f /boot/zipl/*.vmx
    #======================================
    # umount zipl boot partition
    #--------------------------------------
    mountpoint -q /boot/zipl && umount /boot/zipl
    return 0
}
#======================================
# installBootLoaderS390
#--------------------------------------
function installBootLoaderS390 {
    local IFS=$IFS_ORIG
    if [ -x /sbin/zipl ];then
        Echo "Installing boot loader..."
        zipl -c /etc/zipl.conf 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install boot loader"
            return 1
        fi
    else
        Echo "Image doesn't have zipl installed"
        Echo "Can't install boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderSyslinux
#--------------------------------------
function installBootLoaderSyslinux {
    local IFS=$IFS_ORIG
    local syslmbr=/usr/share/syslinux/mbr.bin
    if [ -e $syslmbr ];then
        Echo "Installing boot loader..."
        if [ $loader = "syslinux" ];then
            if ! syslinux $imageBootDevice;then
                Echo "Failed to install boot loader"
                return 1
            fi
        else
            if ! extlinux --install /boot/syslinux;then
                Echo "Failed to install boot loader"
                return 1
            fi
        fi
        dd if=$syslmbr of=$imageDiskDevice bs=512 count=1 conv=notrunc
    else
        Echo "Image doesn't have syslinux (mbr.bin) installed"
        Echo "Can't install boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderGrub
#--------------------------------------
function installBootLoaderGrub {
    # /.../
    # install the grub according to the contents of
    # /etc/grub.conf and /boot/grub/menu.lst
    # ----
    local IFS=$IFS_ORIG
    if lookup grub &>/dev/null;then
        Echo "Installing boot loader..."
        grub --batch --no-floppy < /etc/grub.conf 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install boot loader"
            return 1
        fi
        if [[ $kiwi_iname =~ boot-rhel ]];then
            # on rhel systems grub.conf is a link to menu.lst.
            rm -f /etc/grub.conf
            ln -s /boot/grub/menu.lst /etc/grub.conf
        fi
    else
        Echo "Image doesn't have grub installed"
        Echo "Can't install boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderGrub2
#--------------------------------------
function installBootLoaderGrub2 {
    # /.../
    # configure and install grub2 according to the
    # contents of /boot/grub2/grub.cfg
    # ----
    local IFS=$IFS_ORIG
    local confTool=grub2-mkconfig
    local instTool=grub2-install
    local confFile_grub_bios=/boot/grub2/grub.cfg
    local confFile_uefi=/boot/efi/EFI/BOOT/grub.cfg
    local confFile_grub=$confFile_grub_bios
    local bios_grub=/boot/grub2/i386-pc
    local product=/etc/products.d/baseproduct
    local elilo_efi=/usr/lib64/efi/elilo.efi
    local grub_efi=/boot/efi/EFI/BOOT/grub.efi
    local isEFI=0
    #======================================
    # check for EFI and mount EFI partition
    #--------------------------------------
    if [ ! -z "$kiwi_JumpPart" ];then
        local jdev=$(ddn $imageDiskDevice $kiwi_JumpPart)
        local label=$(blkid $jdev -s LABEL -o value)
        if [ "$label" = "EFI" ];then
            mkdir -p /boot/efi
            if ! mount $jdev /boot/efi;then
                Echo "Failed to mount EFI boot partition"
                return 1
            fi
            isEFI=1
        fi
    fi
    #======================================
    # check for elilo compat mode
    #--------------------------------------
    export elilo_compat=0
    if [ $isEFI -eq 1 ] && [ -e $product ] && [ -e $elilo_efi ];then
        local product=$(readlink $product)
        local vendor=SuSE
        local efipath=/boot/efi/EFI
        if [[ "$product" =~ "SUSE_SLE" ]];then
            #======================================
            # check for recovery uuid
            #--------------------------------------
            if [ -z "$reco_uuid" ]; then
                reco_uuid=$(blkid -o value -s UUID -t LABEL=recovery)
            fi
            #======================================
            # check for bootloader displayname
            #--------------------------------------
            if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
                kiwi_oemtitle=$kiwi_displayname
            fi
            #======================================
            # write elilo.conf
            #--------------------------------------
            . /etc/default/grub
            local timeout=10
            if [ ! -z "$kiwi_boot_timeout" ];then
                timeout=$kiwi_boot_timeout
            fi
cat > /etc/elilo.conf << EOF
# Modified by YaST2.
timeout = $timeout
##YaST - boot_efilabel = "$kiwi_oemtitle"
vendor-directory = $vendor
secure-boot = on
prompt
image  = /boot/vmlinuz
###Don't change this comment - YaST2 identifier: Original name: linux###
initrd = /boot/initrd
label  = linux
append = "$GRUB_CMDLINE_LINUX_DEFAULT"
description = "$kiwi_oemtitle"
root = $(getDiskID $imageRootDevice)
EOF
            #====================================================
            # setup kernel symlinks
            #----------------------------------------------------
            local kversion=$(uname -r)
            ln -sf /boot/vmlinuz-$kversion /boot/vmlinuz
            ln -sf /boot/initrd-$kversion /boot/initrd
            #====================================================
            # create vendor directory
            #----------------------------------------------------
            mkdir -p $efipath/$vendor
            #======================================
            # update sysconfig/bootloader
            #--------------------------------------
            sed -i -e s'@LOADER_TYPE.*@LOADER_TYPE="elilo"@' \
                /etc/sysconfig/bootloader
            #======================================
            # set up boot files and configurations
            #--------------------------------------
            # create elilo.conf and grub.cfg and
            # copy boot files to /boot/efi
            # ----
            elilo -vv
            #====================================================
            # Append recovery entry to elilo written grub.cfg
            #----------------------------------------------------
            if [ "$kiwi_oemrecovery" = "true" ];then
cat >> $efipath/$vendor/grub.cfg << EOF
menuentry 'Recovery' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    configfile /boot/grub2/grub.cfg
}
EOF
            fi
            #======================================
            # write efi variable to NvRam
            #--------------------------------------
            # this is for the efi boot manager to show a better
            # title for this system
            # ----
            elilo --refresh-EBM -vv
            #====================================================
            # create versionized kernel/initrd
            #----------------------------------------------------
            cp -a $efipath/$vendor/vmlinuz $efipath/$vendor/vmlinuz-$kversion
            cp -a $efipath/$vendor/initrd $efipath/$vendor/initrd-$kversion
            #====================================================
            # sync vendor directory with standard boot path
            #----------------------------------------------------
            cp -a $efipath/$vendor/* $efipath/BOOT
            #======================================
            # set flag to indicate elilo is used
            #--------------------------------------
            elilo_compat=1
            #======================================
            # return early for elilo case
            #--------------------------------------
            mountpoint -q /boot/efi && umount /boot/efi
            return 0
        fi
    fi
    if ! lookup $confTool &>/dev/null;then
        Echo "Image doesn't have grub2 installed"
        Echo "Can't install boot loader"
        return 1
    fi
    #======================================
    # create grub2 configuration
    #--------------------------------------
    $confTool > $confFile_grub
    if [ ! $? = 0 ];then
        Echo "Failed to create grub2 boot configuration"
        return 1
    fi
    if [ -e $confFile_grub_bios ];then
        cp $confFile_grub $confFile_grub_bios
    fi
    if [ $isEFI -eq 1 ] && [ -e $confFile_uefi ];then
        cp $confFile_grub $confFile_uefi
        umount /boot/efi
    fi
    #======================================
    # install grub2 in BIOS mode
    #--------------------------------------
    if [ ! -z "$kiwi_OfwGrub" ];then
        # install powerpc grub2
        $instTool $imagePrepDevice 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install boot loader"
            return 1
        fi
    elif [ $isEFI -eq 0 ];then
        # use plain grub2-install in standard bios mode
        $instTool $imageDiskDevice 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install boot loader"
            return 1
        fi
    elif [ ! -z "$kiwi_BiosGrub" ] && [ -d $bios_grub ];then
        # force install of bios grub2 in efi legacy mode
        $instTool --force --target i386-pc $imageDiskDevice 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install legacy boot loader"
            return 1
        fi
    else
        Echo "No bootloader installaton required"
    fi
    return 0
}
#======================================
# installBootLoaderYaboot
#--------------------------------------
function installBootLoaderYaboot {
    # /.../
    # install the lilo/yaboot bootloader
    # ----
    local IFS=$IFS_ORIG
    if [ -x /sbin/lilo ];then
        Echo "Installing boot loader..."
        /sbin/lilo 1>&2
        if [ ! $? = 0 ];then
            Echo "Failed to install boot loader"
            return 1
        fi
    else
        Echo "Image doesn't have lilo installed"
        Echo "Can't install boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderS390Recovery
#--------------------------------------
function installBootLoaderS390Recovery {
    local IFS=$IFS_ORIG
    Echo "*** zipl: recovery boot not implemented ***"
    return 1
}
#======================================
# installBootLoaderSyslinuxRecovery
#--------------------------------------
function installBootLoaderSyslinuxRecovery {
    local IFS=$IFS_ORIG
    local syslmbr=/usr/share/syslinux/mbr.bin
    if [ -e $syslmbr ];then
        if [ $loader = "syslinux" ];then
            if ! syslinux $imageRecoveryDevice;then
                Echo "Failed to install recovery boot loader"
                return 1
            fi
        else
            if ! extlinux --install /reco-save/boot/syslinux;then
                Echo "Failed to install recovery boot loader"
                return 1
            fi
        fi
    else
        Echo "Image doesn't have syslinux (mbr.bin) installed"
        Echo "Can't install recovery boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderGrubRecovery
#--------------------------------------
function installBootLoaderGrubRecovery {
    # /.../
    # install the grub into the recovery partition.
    # By design the recovery partition is always the
    # last primary partition of the disk
    # ----
    local IFS=$IFS_ORIG
    local input=/grub.input
    local gdevreco=$((recoid - 1))
    if [ ! -e /etc/redhat-release ];then
        echo "device (hd0) $imageDiskDevice" > $input
    fi
    echo "root (hd0,$gdevreco)"  >> $input
    echo "setup (hd0,$gdevreco)" >> $input
    echo "quit"          >> $input
    if lookup grub &>/dev/null;then
        if [ -e /etc/redhat-release ];then
            mount -L recovery /mnt
            (cd /mnt/boot/grub && ln -s menu.lst grub.conf)
            umount /mnt
        fi
        if ! grub --batch < $input 1>&2;then
            Echo "Failed to install recovery boot loader"
            return 1
        fi
        rm -f $input
    else
        Echo "Image doesn't have grub installed"
        Echo "Can't install recovery boot loader"
        return 1
    fi
    return 0
}
#======================================
# installBootLoaderGrub2Recovery
#--------------------------------------
function installBootLoaderGrub2Recovery {
    # /.../
    # install grub2 into the recovery partition
    # By design the recovery partition is always the
    # last primary partition of the disk
    # ----
    local IFS=$IFS_ORIG
    local confTool=grub2-mkconfig
    local confFile_grub_bios=/boot/grub2/grub.cfg
    local confFile_uefi=/boot/efi/EFI/BOOT/grub.cfg
    local confFile_grub=$confFile_grub_bios
    local bios_grub=/reco-save/boot/grub2/i386-pc
    local isEFI=0
    #======================================
    # check for EFI and mount EFI partition
    #--------------------------------------
    if [ ! -z "$kiwi_JumpPart" ];then
        local jdev=$(ddn $imageDiskDevice $kiwi_JumpPart)
        local label=$(blkid $jdev -s LABEL -o value)
        if [ "$label" = "EFI" ];then
            mkdir -p /boot/efi
            if ! mount $jdev /boot/efi;then
                Echo "Failed to mount EFI boot partition"
                return 1
            fi
            isEFI=1
        fi
    fi
    #======================================
    # check for elilo compat mode
    #--------------------------------------
    if [ "$elilo_compat" -eq 1 ];then
        # the recovery menu entry has been appended already
        # as part of the regular installBootLoaderGrub2. This is
        # done to ensure the entry is recreated after a recovery
        # run because elilo doesn't support that
        return 0
    fi
    #======================================
    # check tool status
    #--------------------------------------
    if ! lookup $confTool &>/dev/null;then
        Echo "Image doesn't have grub2 installed"
        Echo "Can't install recovery boot loader"
        mountpoint -q /boot/efi && umount /boot/efi
        return 1
    fi
    #======================================
    # install grub2 into partition
    #--------------------------------------
    # this allows a bios to directly jump there, e.g with a function key
    grub2-bios-setup -f -d $bios_grub $imageRecoveryDevice 1>&2
    if [ ! $? = 0 ];then
        Echo "Failed to install recovery boot loader"
    fi
    #======================================
    # create custom recovery entry
    #--------------------------------------
cat > /etc/grub.d/40_custom << DONE
#!/bin/bash
cat << EOF
menuentry 'Recovery' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    configfile /boot/grub2/grub.cfg
}
EOF
DONE
    #======================================
    # create grub2 config file
    #--------------------------------------
    $confTool > $confFile_grub
    if [ ! $? = 0 ];then
        Echo "Failed to create recovery grub2 boot configuration"
        mountpoint -q /boot/efi && umount /boot/efi
        return 1
    fi
    if [ $isEFI -eq 1 ] && [ -e $confFile_uefi ];then
        cp $confFile_grub $confFile_uefi
    fi
    mountpoint -q /boot/efi && umount /boot/efi
    return 0
}
#======================================
# updateModuleDependencies
#--------------------------------------
function updateModuleDependencies {
    # /.../
    # update the kernel module dependencies list
    # ---
    local IFS=$IFS_ORIG
    local depmodExec=$(lookup depmod 2>/dev/null)
    if [ ! -x "$depmodExec" ];then
        Echo "Could not find depmod executable"
        Echo "Skipping module dependency update"
        systemIntegrity=unknown
        return
    fi
    if ! $depmodExec -a;then
        Echo "Module dependency update failed."
        systemIntegrity=unknown
    fi
}

#======================================
# setupInitrd
#--------------------------------------
function setupInitrd {
    # /.../
    # call mkinitrd to create the distro initrd
    # ----
    local IFS=$IFS_ORIG
    bootLoaderOK=1
    local umountProc=0
    local umountSys=0
    local systemMap=0
    local dracutExec=$(lookup dracut 2>/dev/null)
    local mkinitrdExec=$(lookup mkinitrd 2>/dev/null)
    local params
    local running
    local rlinux
    local rinitrd
    local kernel_version=$(uname -r)
    for i in $(find /boot/ -name "System.map*");do
        systemMap=1
    done
    setupDefaultTheme
    if [ $systemMap -eq 1 ];then
        #======================================
        # Cleanup
        #--------------------------------------
        rm -f /boot/initrd-*.img
        #======================================
        # Prepare for tool call
        #--------------------------------------
        if [ ! -e /proc/mounts ];then
            mount -t proc proc /proc
            umountProc=1
        fi
        if [ ! -e /sys/block ];then
            mount -t sysfs sysfs /sys
            umountSys=1
        fi
        modprobe dm-mod &>/dev/null
        updateModuleDependencies
        #======================================
        # Call initrd creation tool
        #--------------------------------------
        if [ -x "$dracutExec" ]; then
            # 1. dracut
            Echo "Creating dracut based initrd"
            params=" -f /boot/initrd-$kernel_version $kernel_version"
            if ! $dracutExec -H $params;then
                Echo "Can't create initrd with dracut"
                systemIntegrity=unknown
                bootLoaderOK=0
            fi
        elif [ -x "$mkinitrdExec" ]; then
            # 2. mkinitrd
            Echo "Creating mkinitrd based initrd"
            if grep -qi param_B $mkinitrdExec;then
                params="-B"
            fi
            if ! $mkinitrdExec $params;then
                Echo "Can't create initrd with mkinitrd"
                systemIntegrity=unknown
                bootLoaderOK=0
            fi
        else
            # no tool found
            Echo "Coudn't find a tool to create initrd image"
            systemIntegrity=unknown
            bootLoaderOK=0
        fi
        #======================================
        # Cleanup kiwi firstboot initrd
        #--------------------------------------
        if [ $bootLoaderOK = "1" ];then
            if [ -f /boot/initrd.vmx ];then
                rm -f /boot/initrd.vmx
            fi
            if [ -f /boot/linux.vmx ];then
                rm -f /boot/linux.vmx
            fi
            if [ -f /boot/initrd.uboot ];then
                rm -f /boot/initrd.uboot
            fi
        fi
        #======================================
        # Loader exceptions
        #--------------------------------------
        if [ "$loader" = "syslinux" ];then
            # /.../
            # if syslinux is used we need to make sure to copy
            # the kernel and initrd to /boot on the boot partition.
            # This is normally done by the boot -> . link but we
            # can't create links on fat
            # ----
            IFS="," ; for i in $KERNEL_LIST;do
                if test -z "$i";then
                    continue
                fi
                kernel=`echo $i | cut -f1 -d:`
                initrd=`echo $i | cut -f2 -d:`
                break
            done
            IFS=$IFS_ORIG
            mkdir -p /boot/boot
            cp /boot/$kernel /boot/boot/
            cp /boot/$initrd /boot/boot/
        fi
        #======================================
        # Cleanup mounts
        #--------------------------------------
        rmmod dm-mod &>/dev/null
        if [ $umountSys -eq 1 ];then
            umount /sys
        fi
        if [ $umountProc -eq 1 ];then
            umount /proc
        fi
    else
        Echo "Image doesn't include kernel system map"
        Echo "Can't create initrd"
        systemIntegrity=unknown
        bootLoaderOK=0
    fi
    #======================================
    # Display a warning on failure
    #--------------------------------------
    # Warning message is disabled because sometimes the message
    # can't be displayed on the console which leads to a stopped
    # system but the user has no clue why
    #
    #if [ $bootLoaderOK = 0 ];then
    #    if lookup dialog &>/dev/null;then
    #        Dialog \
    #            --backtitle \"$TEXT_BOOT_SETUP_FAILED\" \
    #            --msgbox "\"$TEXT_BOOT_SETUP_FAILED_INFO\"" 10 70
    #    else
    #        systemException \
    #            "$TEXT_BOOT_SETUP_FAILED\n\n$TEXT_BOOT_SETUP_FAILED_INFO" \
    #        "waitkey"
    #    fi
    #fi
}
#======================================
# setupDefaultTheme
#--------------------------------------
function setupDefaultTheme {
    local IFS=$IFS_ORIG
    if lookup plymouthd &>/dev/null;then
        plymouth-set-default-theme $kiwi_splash_theme &>/dev/null
    fi
}
#======================================
# setupBootLoader
#--------------------------------------
function setupBootLoader {
    # /.../
    # generic function to setup the boot loader configuration.
    # The selection of the bootloader happens according to
    # the architecture of the system
    # ----
    local IFS=$IFS_ORIG
    local arch=`uname -m`
    local para=""
    while [ $# -gt 0 ];do
        # quote simple quotation marks
        arg=$(echo $1 | sed -e s"#'#'\\\\''#g")
        para="$para '$arg'"
        shift
    done
    case $arch-$loader in
        i*86-grub)       eval setupBootLoaderGrub $para ;;
        x86_64-grub)     eval setupBootLoaderGrub $para ;;
        i*86-grub2)      eval setupBootLoaderGrub2 $para ;;
        x86_64-grub2)    eval setupBootLoaderGrub2 $para ;;
        ppc64*-grub2)    eval setupBootLoaderGrub2 $para ;;
        s390*-grub2)     eval setupBootLoaderGrub2 $para ;;
        i*86-syslinux)   eval setupBootLoaderSyslinux $para ;;
        x86_64-syslinux) eval setupBootLoaderSyslinux $para ;;
        i*86-extlinux)   eval setupBootLoaderSyslinux $para ;;
        x86_64-extlinux) eval setupBootLoaderSyslinux $para ;;
        s390-zipl)       eval setupBootLoaderS390 $para ;;
        s390x-zipl)      eval setupBootLoaderS390 $para ;;
        s390x-grub2_s390x_emu)  eval setupBootLoaderS390Grub $para ;;
        ppc*)            eval setupBootLoaderYaboot $para ;;
        aarch64-uboot)   eval setupBootLoaderUBoot $para ;;
        aarch64-grub2)   eval setupBootLoaderGrub2 $para ;;
        arm*-grub2)      eval setupBootLoaderGrub2 $para ;;
        arm*)            eval setupBootLoaderUBoot $para ;;
        *)
        systemException \
            "*** boot loader setup for $arch-$loader not implemented ***" \
        "reboot"
    esac
    setupBootThemes "/config"
}
#======================================
# setupBootThemes
#--------------------------------------
function setupBootThemes {
    local IFS=$IFS_ORIG
    local destprefix=$1
    local prefix=$2
    if [ -z "$prefix" ];then
        prefix=/mnt
    fi
    #======================================
    # Splash theme setup
    #--------------------------------------
    if [ ! -z "$kiwi_splash_theme" ];then
        local theme=$kiwi_splash_theme
        #======================================
        # gfxboot default setup
        #--------------------------------------
        local orig_bootsplash=$prefix/etc/sysconfig/bootsplash
        local inst_bootsplash=$destprefix/etc/sysconfig/bootsplash
        mkdir -p $destprefix/etc/sysconfig
        touch $inst_bootsplash
        #======================================
        # check for bootsplash config in sysimg
        #--------------------------------------
        if [ -f $orig_bootsplash ];then
            cp $orig_bootsplash $inst_bootsplash
        fi
        #======================================
        # change/create bootsplash config
        #--------------------------------------
        if cat $inst_bootsplash | grep -q -E "^THEME"; then
            sed -i "s/^THEME=.*/THEME=\"$theme\"/" $inst_bootsplash
        else
            echo "THEME=\"$theme\"" >> $inst_bootsplash
        fi
        #======================================
        # plymouth splash
        #--------------------------------------
        if lookup plymouthd &>/dev/null;then
            local orig_plymouthconf=$prefix/etc/plymouth/plymouth.conf
            local inst_plymouthconf=$destprefix/etc/plymouth/plymouth.conf
            mkdir -p $destprefix/etc/plymouth
            touch $inst_plymouthconf
            #======================================
            # check for plymouth config in sysimg
            #--------------------------------------
            if [ -f $orig_plymouthconf ];then
                cp $orig_plymouthconf $inst_plymouthconf
            fi
            #======================================
            # change/create plymouth config
            #--------------------------------------
            if cat $inst_plymouthconf | grep -q -E "^Theme"; then
                sed -i "s/^Theme=.*/Theme=\"$theme\"/" $inst_plymouthconf
            else
                echo "[Daemon]" > $inst_plymouthconf
                echo "Theme=\"$theme\"" >> $inst_plymouthconf
            fi
        fi
    fi
}
#======================================
# setupBootLoaderRecovery
#--------------------------------------
function setupBootLoaderRecovery {
    # /.../
    # generic function to setup the boot loader configuration
    # for the recovery partition. The selection of the bootloader
    # happens according to the architecture of the system
    # ----
    local IFS=$IFS_ORIG
    local arch=$(uname -m)
    local para=""
    while [ $# -gt 0 ];do
        # quote simple quotation marks
        arg=$(echo $1 | sed -e s"#'#'\\\\''#g")
        para="$para '$arg'"
        shift
    done
    case $arch-$loader in
        i*86-grub)       eval setupBootLoaderGrubRecovery $para ;;
        x86_64-grub)     eval setupBootLoaderGrubRecovery $para ;;
        i*86-grub2)      eval setupBootLoaderGrub2Recovery $para ;;
        x86_64-grub2)    eval setupBootLoaderGrub2Recovery $para ;;
        s390*-grub2)     eval setupBootLoaderGrub2Recovery $para ;;
        i*86-syslinux)   eval setupBootLoaderSyslinuxRecovery $para ;;
        x86_64-syslinux) eval setupBootLoaderSyslinuxRecovery $para ;;
        i*86-extlinux)   eval setupBootLoaderSyslinuxRecovery $para ;;
        x86_64-extlinux) eval setupBootLoaderSyslinuxRecovery $para ;;
        s390-zipl)       eval setupBootLoaderS390Recovery $para ;;
        s390x-zipl)      eval setupBootLoaderS390Recovery $para ;;
        s390x-grub2_s390x_emu)  eval setupBootLoaderS390Recovery $para ;;
        *)
        systemException \
            "*** boot loader setup for $arch-$loader not implemented ***" \
        "reboot"
    esac
}
#======================================
# setupBootLoaderS390Recovery
#--------------------------------------
function setupBootLoaderS390Recovery {
    local IFS=$IFS_ORIG
    systemException \
        "*** zipl: recovery boot not implemented ***" \
    "reboot"
}
#======================================
# setupBootLoaderSyslinuxRecovery
#--------------------------------------
function setupBootLoaderSyslinuxRecovery {
    # /.../
    # create syslinux configuration for the recovery boot system
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gnum=$3         # boot partition ID
    local rdev=$4         # root partition
    local gfix=$5         # syslinux title postfix
    local swap=$6         # optional swap partition
    local conf=$destsPrefix/boot/syslinux/syslinux.cfg
    local kernel=""
    local initrd=""
    local fbmode=$vga
    if [ -z "$fbmode" ];then
        fbmode=$DEFAULT_VGA
    fi
    rdev_recovery=$imageRootDevice
    diskByID=$(getDiskID $rdev_recovery)
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # import syslinux into recovery
    #--------------------------------------
    cp -a $mountPrefix/boot/syslinux $destsPrefix/boot
    #======================================
    # setup config file name
    #--------------------------------------
    if [ $loader = "extlinux" ];then
        conf=$destsPrefix/boot/syslinux/extlinux.conf
    fi
    #======================================
    # create syslinux.cfg file
    #--------------------------------------
    echo "implicit 1"                   > $conf
    echo "prompt   1"                  >> $conf
    echo "TIMEOUT $kiwi_boot_timeout"  >> $conf
    echo "display isolinux.msg"        >> $conf
    if [ -f "$mountPrefix/boot/syslinux/bootlogo" ];then
        if \
            [ -f "$mountPrefix/boot/syslinux/gfxboot.com" ] || \
            [ -f "$mountPrefix/boot/syslinux/gfxboot.c32" ]
        then
            echo "ui gfxboot bootlogo isolinux.msg" >> $conf
        else
            echo "gfxboot bootlogo"                 >> $conf
        fi
    fi
    kernel=linux.vmx   # this is a copy of the kiwi linux.vmx file
    initrd=initrd.vmx  # this is a copy of the kiwi initrd.vmx file
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        #======================================
        # Reboot
        #--------------------------------------
        title=$(makeLabel "Cancel/Reboot")
        echo "DEFAULT $title"                              >> $conf
        echo "label $title"                                >> $conf
        echo " localboot 0x80"                             >> $conf
        #======================================
        # Recovery
        #--------------------------------------
        title=$(makeLabel "Recover/Repair System")
        echo "label $title"                                >> $conf
        if xenServer $kernel $mountPrefix;then
            systemException \
                "*** $loader: Xen dom0 boot not implemented ***" \
            "reboot"
        else
            echo "kernel /boot/$kernel"                    >> $conf
            echo -n "append initrd=/boot/$initrd"          >> $conf
            echo -n " root=$diskByID"                      >> $conf
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
            fi
            echo -n " vga=$fbmode"                         >> $conf
            echo -n " $KIWI_INITRD_PARAMS"                 >> $conf
            echo -n " $KIWI_KERNEL_OPTIONS"                >> $conf
            echo " KIWI_RECOVERY=$recoid"                  >> $conf
            echo " showopts"                               >> $conf
        fi
        #======================================
        # Restore
        #--------------------------------------
        title=$(makeLabel "Restore Factory System")
        echo "label $title"                                >> $conf
        if xenServer $kernel $mountPrefix;then
            systemException \
                "*** $loader: Xen dom0 boot not implemented ***" \
            "reboot"
        else
            echo "kernel /boot/$kernel"                    >> $conf
            echo -n "append initrd=/boot/$initrd"          >> $conf
            echo -n " root=$diskByID"                      >> $conf
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
            fi
            echo -n " vga=$fbmode"                         >> $conf
            echo -n " $KIWI_INITRD_PARAMS"                 >> $conf
            echo -n " $KIWI_KERNEL_OPTIONS"                >> $conf
            echo " KIWI_RECOVERY=$recoid RESTORE=1"        >> $conf
            echo " showopts"                               >> $conf
        fi
    fi
}
#======================================
# setupBootLoaderGrubRecovery
#--------------------------------------
function setupBootLoaderGrubRecovery {
    # /.../
    # create menu.lst file for the recovery boot system
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gfix=$3         # grub title
    local menu=$destsPrefix/boot/grub/menu.lst
    local kernel=""
    local initrd=""
    local fbmode=$vga
    local gdevreco=$((recoid - 1))
    if [ -z "$fbmode" ];then
        fbmode=$DEFAULT_VGA
    fi
    gdev_recovery="(hd0,$gdevreco)"
    rdev_recovery=$imageRootDevice
    diskByID=$(getDiskID $rdev_recovery)
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # import grub stages into recovery
    #--------------------------------------
    mkdir -p $destsPrefix/boot/grub
    cp $mountPrefix/boot/grub/stage1 $destsPrefix/boot/grub
    cp $mountPrefix/boot/grub/stage2 $destsPrefix/boot/grub
    #======================================
    # create recovery menu.lst
    #--------------------------------------
    echo "timeout 30" > $menu
    echo "gfxmenu $gdev_recovery/boot/message" >> $menu
    kernel=vmlinuz # this is a copy of the kiwi linux.vmx file
    initrd=initrd  # this is a copy of the kiwi initrd.vmx file
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        #======================================
        # Make the cancel option default
        #--------------------------------------
        echo "default 0"                                  >> $menu
        #======================================
        # Reboot
        #--------------------------------------
        title=$(makeLabel "Cancel/Reboot")
        echo "title $title"                               >> $menu
        echo " reboot"                                    >> $menu
        #======================================
        # Recovery
        #--------------------------------------
        title=$(makeLabel "Recover/Repair System")
        echo "title $title"                               >> $menu
        if xenServer $kernel $mountPrefix;then
            echo " root $gdev_recovery"                   >> $menu
            echo " kernel /boot/xen.gz"                   >> $menu
            echo -n " module /boot/$kernel"               >> $menu
            echo -n " root=$diskByID $console"            >> $menu
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
            fi
            echo -n " vga=$fbmode"                        >> $menu
            echo -n " $KIWI_INITRD_PARAMS"                >> $menu
            echo -n " $KIWI_KERNEL_OPTIONS"               >> $menu
            echo -n " KIWI_RECOVERY=$recoid"              >> $menu
            echo " showopts"                              >> $menu
            echo " module /boot/$initrd"                  >> $menu
        else
            echo -n " kernel $gdev_recovery/boot/$kernel" >> $menu
            echo -n " root=$diskByID $console"            >> $menu
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
            fi
            echo -n " vga=$fbmode"                        >> $menu
            echo -n " $KIWI_INITRD_PARAMS"                >> $menu
            echo -n " $KIWI_KERNEL_OPTIONS"               >> $menu
            echo -n " KIWI_RECOVERY=$recoid"              >> $menu
            echo " showopts"                              >> $menu
            echo " initrd $gdev_recovery/boot/$initrd"    >> $menu
        fi
        #======================================
        # Restore
        #--------------------------------------
        title=$(makeLabel "Restore Factory System")
        echo "title $title"                               >> $menu
        if xenServer $kernel $mountPrefix;then
            echo " root $gdev_recovery"                   >> $menu
            echo " kernel /boot/xen.gz"                   >> $menu
            echo -n " module /boot/$kernel"               >> $menu
            echo -n " root=$diskByID $console"            >> $menu
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
            fi
            echo -n " vga=$fbmode"                        >> $menu
            echo -n " $KIWI_INITRD_PARAMS"                >> $menu
            echo -n " $KIWI_KERNEL_OPTIONS"               >> $menu
            echo -n " KIWI_RECOVERY=$recoid"              >> $menu
            echo " showopts"                              >> $menu
            echo " module /boot/$initrd"                  >> $menu
        else
            echo -n " kernel $gdev_recovery/boot/$kernel" >> $menu
            echo -n " root=$diskByID $console"            >> $menu
            if [ ! -z "$imageDiskDevice" ];then
                echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
            fi
            echo -n " vga=$fbmode"                        >> $menu
            echo -n " $KIWI_INITRD_PARAMS"                >> $menu
            echo -n " $KIWI_KERNEL_OPTIONS"               >> $menu
            echo -n " KIWI_RECOVERY=$recoid RESTORE=1"    >> $menu
            echo " showopts"                              >> $menu
            echo " initrd $gdev_recovery/boot/$initrd"    >> $menu
        fi
    fi
}
#======================================
# setupBootLoaderGrub2Recovery
#--------------------------------------
function setupBootLoaderGrub2Recovery {
    # /.../
    # create grub.cfg file for the recovery boot system
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gfix=$3         # grub title
    local kernel=vmlinuz  # this is a copy of the kiwi linux.vmx file
    local initrd=initrd   # this is a copy of the kiwi initrd.vmx file
    local conf=$destsPrefix/boot/grub2/grub.cfg
    local theme=$RECOVERY_THEME
    #======================================
    # setup ID device names
    #--------------------------------------
    local rootByID=$(getDiskID $imageRootDevice)
    local diskByID=$(getDiskID $imageDiskDevice)
    if [ "$FSTYPE" = "zfs" ];then
        rootByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # operate only in recovery mode
    #--------------------------------------
    if [ -z "$kiwi_oemrecovery" ];then
        return
    fi
    #======================================
    # import grub2 modules into recovery
    #--------------------------------------
    mkdir -p $destsPrefix/boot
    cp -a $mountPrefix/boot/grub2 $destsPrefix/boot/
    rm -f $destsPrefix/boot/grub2/grub.cfg
    rm -f $destsPrefix/boot/grub2/bootpart.cfg
    #======================================
    # check for kernel options
    #--------------------------------------
    local cmdline="KIWI_RECOVERY=$recoid"
    if [ ! -z "$KIWI_KERNEL_OPTIONS" ];then
        cmdline="$cmdline $KIWI_KERNEL_OPTIONS"
    fi
    if [ ! -z "$KIWI_INITRD_PARAMS" ];then
        cmdline="$cmdline $KIWI_INITRD_PARAMS";
    fi
    if [ ! -z "$rootByID" ];then
        cmdline="$cmdline root=$rootByID"
    fi
    if [ ! -z "$diskByID" ];then
        cmdline="$cmdline disk=$diskByID"
    fi
    if [ -e /dev/xvc0 ];then
        cmdline="$cmdline console=xvc console=tty"
    elif [ -e /dev/hvc0 ];then
        cmdline="$cmdline console=hvc console=tty"
    fi
    #======================================
    # create recovery grub.cfg
    #--------------------------------------
cat > $conf << EOF
insmod ext2
insmod gettext
insmod part_msdos
insmod chain
insmod png
insmod vbe
insmod vga
insmod gzio
set default=0
search --no-floppy --fs-uuid --set=root $reco_uuid
set font=/boot/unicode.pf2
if loadfont \$font ;then
    set gfxmode=auto
    insmod gfxterm
    insmod gfxmenu
    terminal_input gfxterm
    if terminal_output gfxterm; then true; else
        terminal gfxterm
    fi
fi
if loadfont /boot/grub2/themes/$theme/ascii.pf2;then
    loadfont /boot/grub2/themes/$theme/DejaVuSans-Bold14.pf2
    loadfont /boot/grub2/themes/$theme/DejaVuSans10.pf2
    loadfont /boot/grub2/themes/$theme/DejaVuSans12.pf2
    loadfont /boot/grub2/themes/$theme/ascii.pf2
    set theme=/boot/grub2/themes/$theme/theme.txt
    set bgimg=/boot/grub2/themes/$theme/background.png
    background_image -m stretch \$bgimg
fi
if [ \$grub_platform = "efi" ]; then
    set linux=linuxefi
    set initrd=initrdefi
else
    set linux=linux
    set initrd=initrd
fi
set timeout=30
EOF
    if xenServer $kernel $mountPrefix;then
cat >> $conf << EOF
menuentry 'Recover/Repair System' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    echo Loading Xen...
    multiboot /boot/xen.gz dummy
    echo Loading $kernel...
    set gfxpayload=keep
    module /boot/$kernel dummy $cmdline $kiwi_cmdline showopts
    echo Loading $initrd...
    module /boot/$initrd dummy
}
menuentry 'Restore Factory System' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    echo Loading Xen...
    multiboot /boot/xen.gz dummy
    echo Loading $kernel...
    set gfxpayload=keep
    module /boot/$kernel dummy $cmdline $kiwi_cmdline RESTORE=1 showopts
    echo Loading $initrd...
    module /boot/$initrd dummy
}
EOF
    else
cat >> $conf << EOF
menuentry 'Recover/Repair System' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    echo Loading $kernel...
    set gfxpayload=keep
    \$linux /boot/$kernel $cmdline $kiwi_cmdline showopts
    echo Loading $initrd...
    \$initrd /boot/$initrd
}
menuentry 'Restore Factory System' --class os {
    search --no-floppy --fs-uuid --set=root $reco_uuid
    echo Loading $kernel...
    set gfxpayload=keep
    \$linux /boot/$kernel $cmdline $kiwi_cmdline RESTORE=1 showopts
    echo Loading $initrd...
    \$initrd /boot/$initrd
}
EOF
    fi
}
#======================================
# setupBootLoaderUBoot
#--------------------------------------
function setupBootLoaderUBoot {
    # /.../
    # The setup of the uboot boot.script can't be done
    # in a generic way because each arm board behaves
    # differently. Thus we are only calling a hook
    # script here
    # ----
    local IFS=$IFS_ORIG
    if [ "$kiwi_bootloader" = "berryboot" ];then
        runHook setupBerryBoot "$@"
    else
        runHook setupUBoot "$@"
    fi
}
#======================================
# setupBootLoaderS390Grub
#--------------------------------------
function setupBootLoaderS390Grub {
    # /.../
    # create grub2 configuration for s390
    # ----
    local IFS=$IFS_ORIG
    #======================================
    # function paramters
    #--------------------------------------
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gnum=$3         # grub boot partition ID
    local rdev=$4         # grub root partition
    local gfix=$5         # grub title postfix
    local swap=$6         # optional swap partition
    #======================================
    # local variables
    #--------------------------------------
    local kname=$(uname -r)
    local loader_type=grub2
    local timeout=10
    local title
    local cmdline
    local vesa
    #======================================
    # setup path names
    #--------------------------------------
    local orig_sysimg_profile=$mountPrefix/image/.profile
    local inst_default_grub=$destsPrefix/etc/default/grub
    local inst_default_grubdev=$destsPrefix/etc/default/grub_installdevice
    local inst_default_grubmap=$destsPrefix/boot/grub2/device.map
    local inst_sysb=$destsPrefix/etc/sysconfig/bootloader
    #======================================
    # setup ID device names
    #--------------------------------------
    local rootByID=$(getDiskID $rdev)
    local swapByID=$(getDiskID $swap swap)
    local diskByID=$(getDiskID $imageDiskDevice)
    if [ "$FSTYPE" = "zfs" ];then
        rootByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $orig_sysimg_profile ];then
        importFile < $orig_sysimg_profile
    fi
    #======================================
    # setup title name
    #--------------------------------------
    if [ -z "$gfix" ];then
        gfix="unknown"
    fi
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    if ! echo $gfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
        title=$(makeLabel "$gfix")
    elif [ -z "$kiwi_oemtitle" ];then
        title=$(makeLabel "$kname [ $gfix ]")
    else
        title=$(makeLabel "$kiwi_oemtitle [ $gfix ]")
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$rootByID" ];then
        cmdline="$cmdline root=$rootByID"
    fi
    if [ ! -z "$diskByID" ];then
        cmdline="$cmdline disk=$diskByID"
    fi
    if [ ! -z "$swapByID" ];then
        cmdline="$cmdline resume=$swapByID"
    fi
    if [ ! -z "$kiwi_cmdline" ];then
        cmdline="$cmdline $kiwi_cmdline"
    fi
    if [[ ! $cmdline =~ quiet ]];then
        cmdline="$cmdline quiet"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ ! -z "$kiwi_boot_timeout" ];then
        timeout=$kiwi_boot_timeout
    fi
    #======================================
    # write etc/default/grub
    #--------------------------------------
    mkdir -p $destsPrefix/etc/default
cat > $inst_default_grub << EOF
GRUB_DISTRIBUTOR=$(printf %q "$title")
GRUB_DEFAULT=0
GRUB_HIDDEN_TIMEOUT=0
GRUB_HIDDEN_TIMEOUT_QUIET=true
GRUB_TIMEOUT=$timeout
GRUB_CMDLINE_LINUX_DEFAULT="$cmdline"
GRUB_TERMINAL=console
EOF
    #======================================
    # enable rollback capability
    #--------------------------------------
    if [ "$FSTYPE" = "btrfs" ];then
        echo "SUSE_BTRFS_SNAPSHOT_BOOTING=true" >> $inst_default_grub
    fi
    #======================================
    # write etc/default/grub_installdevice
    #--------------------------------------
cat > $inst_default_grubdev << EOF
$diskByID
EOF
    #======================================
    # write boot/grub2/device.map
    #--------------------------------------
    mkdir -p $destsPrefix/boot/grub2
cat > $inst_default_grubmap << EOF
(hd0) $diskByID
EOF
    #======================================
    # write sysconfig/bootloader
    #--------------------------------------
    mkdir -p $destsPrefix/etc/sysconfig
cat > $inst_sysb << EOF
LOADER_TYPE=$loader_type
DEFAULT_APPEND="$cmdline"
FAILSAFE_APPEND="$failsafe $cmdline"
EOF
}
#======================================
# setupBootLoaderS390
#--------------------------------------
function setupBootLoaderS390 {
    # /.../
    # create /etc/zipl.conf used for the
    # zipl bootloader
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local znum=$3         # boot partition ID
    local rdev=$4         # root partition
    local zfix=$5         # zipl title postfix
    local swap=$6         # optional swap partition
    local conf=$destsPrefix/etc/zipl.conf
    local sysb=$destsPrefix/etc/sysconfig/bootloader
    local kname=""
    local kernel=""
    local initrd=""
    local title=""
    #======================================
    # check for device by ID
    #--------------------------------------
    local diskByID=$(getDiskID $rdev)
    local swapByID=$(getDiskID $swap swap)
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # check for bootloader displayname
    #--------------------------------------
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $mountPrefix/image/.profile ];then
        importFile < $mountPrefix/image/.profile
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$kiwi_cmdline" ];then
        KIWI_KERNEL_OPTIONS="$KIWI_KERNEL_OPTIONS $kiwi_cmdline"
    fi
    #======================================
    # check for syslinux title postfix
    #--------------------------------------
    if [ -z "$zfix" ];then
        zfix="unknown"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ -z "$kiwi_boot_timeout" ];then
        kiwi_boot_timeout=100;
    fi
    #======================================
    # create directory structure
    #--------------------------------------
    for dir in $conf $sysb;do
        dir=`dirname $dir`; mkdir -p $dir
    done
    #======================================
    # create zipl.conf file
    #--------------------------------------
    local count
    local title_default
    local title_failsafe
    echo "[defaultboot]"                      > $conf
    echo "defaultmenu = menu"                >> $conf
    echo ":menu"                             >> $conf
    echo "    default = 1"                   >> $conf
    echo "    prompt = 1"                    >> $conf
    echo "    target = /boot/zipl"           >> $conf
    echo "    timeout = $kiwi_boot_timeout"  >> $conf
    count=1
    IFS="," ; for i in $KERNEL_LIST;do
        if test -z "$i";then
            continue
        fi
        kname=${KERNEL_NAME[$count]}
        if ! echo $zfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
            if [ "$count" = "1" ];then
                title_default=$(makeLabel "$zfix")
            else
                title_default=$(makeLabel "$kname ( $zfix )")
            fi
        elif [ -z "$kiwi_oemtitle" ];then
            title_default=$(makeLabel "$kname ( $zfix )")
        else
            if [ "$count" = "1" ];then
                title_default=$(makeLabel "$kiwi_oemtitle ( $zfix )")
            else
                title_default=$(makeLabel "$kiwi_oemtitle-$kname ( $zfix )")
            fi
        fi
        title_failsafe=$(makeLabel "Failsafe -- $title_default")
        echo "    $count = $title_default"  >> $conf
        count=$((count + 1))
        echo "    $count = $title_failsafe" >> $conf
        count=$((count + 1))
    done
    count=1
    IFS="," ; for i in $KERNEL_LIST;do
        if test -z "$i";then
            continue
        fi
        kernel=`echo $i | cut -f1 -d:`
        initrd=`echo $i | cut -f2 -d:`
        kname=${KERNEL_NAME[$count]}
        if ! echo $zfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
            if [ "$count" = "1" ];then
                title_default=$(makeLabel "$zfix")
            else
                title_default=$(makeLabel "$kname ( $zfix )")
            fi
        elif [ -z "$kiwi_oemtitle" ];then
            title_default=$(makeLabel "$kname ( $zfix )")
        else
            if [ "$count" = "1" ];then
                title_default=$(makeLabel "$kiwi_oemtitle ( $zfix )")
            else
                title_default=$(makeLabel "$kiwi_oemtitle-$kname ( $zfix )")
            fi
        fi
        title_failsafe=$(makeLabel "Failsafe -- $title_default")
        #======================================
        # create standard entry
        #--------------------------------------
        echo "[$title_default]"                  >> $conf
        echo "target  = /boot/zipl"              >> $conf
        echo "image   = /boot/$kernel"           >> $conf
        echo "ramdisk = /boot/$initrd,0x2000000" >> $conf
        echo -n "parameters = \"root=$diskByID"  >> $conf
        if [ ! -z "$imageDiskDevice" ];then
            echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
        fi
        if [ ! -z "$swap" ];then
            echo -n " resume=$swapByID" >> $conf
        fi
        echo -n " $KIWI_INITRD_PARAMS"  >> $conf
        echo -n " $KIWI_KERNEL_OPTIONS" >> $conf
        echo " showopts\""              >> $conf
        #======================================
        # create failsafe entry
        #--------------------------------------
        echo "[$title_failsafe]"                 >> $conf
        echo "target  = /boot/zipl"              >> $conf
        echo "image   = /boot/$kernel"           >> $conf
        echo "ramdisk = /boot/$initrd,0x2000000" >> $conf
        echo -n "parameters = \"root=$diskByID"  >> $conf
        if [ ! -z "$imageDiskDevice" ];then
            echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
        fi
        echo -n " $KIWI_INITRD_PARAMS"         >> $conf
        echo -n " $KIWI_KERNEL_OPTIONS"        >> $conf
        echo -n " x11failsafe"                 >> $conf
        echo " showopts\""                     >> $conf
        count=$((count + 1))
    done
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        systemException \
            "*** zipl: recovery chain loading not implemented ***" \
        "reboot"
    fi
    #======================================
    # create sysconfig/bootloader
    #--------------------------------------
    echo "LOADER_TYPE=\"$loader\""                            > $sysb
    echo "LOADER_LOCATION=\"mbr\""                           >> $sysb
    echo -n "DEFAULT_APPEND=\"root=$diskByID"                >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo " showopts\""                                       >> $sysb
    echo -n "FAILSAFE_APPEND=\"root=$diskByID"               >> $sysb
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo -n " x11failsafe noresume\""                        >> $sysb
}
#======================================
# setupBootLoaderSyslinux
#--------------------------------------
function setupBootLoaderSyslinux {
    # /.../
    # create syslinux.cfg used for the
    # syslinux bootloader
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gnum=$3         # boot partition ID
    local rdev=$4         # root partition
    local gfix=$5         # syslinux title postfix
    local swap=$6         # optional swap partition
    local conf=$destsPrefix/boot/syslinux/syslinux.cfg
    local sysb=$destsPrefix/etc/sysconfig/bootloader
    local console=""
    local kname=""
    local kernel=""
    local initrd=""
    local title=""
    local fbmode=$vga
    if [ ! -z "$kiwi_oemrecovery" ];then
        local gdevreco=$recoid
    fi
    if [ -z "$fbmode" ];then
        fbmode=$DEFAULT_VGA
    fi
    #======================================
    # check for device by ID
    #--------------------------------------
    local diskByID=$(getDiskID $rdev)
    local swapByID=$(getDiskID $swap swap)
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # check for bootloader displayname
    #--------------------------------------
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $mountPrefix/image/.profile ];then
        importFile < $mountPrefix/image/.profile
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$kiwi_cmdline" ];then
        KIWI_KERNEL_OPTIONS="$KIWI_KERNEL_OPTIONS $kiwi_cmdline"
    fi
    #======================================
    # setup config file name
    #--------------------------------------
    if [ $loader = "extlinux" ];then
        conf=$destsPrefix/boot/syslinux/extlinux.conf
    fi
    #======================================
    # check for syslinux title postfix
    #--------------------------------------
    if [ -z "$gfix" ];then
        gfix="unknown"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ -z "$kiwi_boot_timeout" ];then
        kiwi_boot_timeout=100;
    fi
    #======================================
    # create directory structure
    #--------------------------------------
    for dir in $conf $sysb;do
        dir=`dirname $dir`; mkdir -p $dir
    done
    #======================================
    # create syslinux.cfg file
    #--------------------------------------
    echo "implicit 1"                   > $conf
    echo "prompt   1"                  >> $conf
    echo "TIMEOUT $kiwi_boot_timeout"  >> $conf
    echo "display isolinux.msg"        >> $conf
    if [ -f "$mountPrefix/boot/syslinux/bootlogo" ];then
        if \
            [ -f "$mountPrefix/boot/syslinux/gfxboot.com" ] || \
            [ -f "$mountPrefix/boot/syslinux/gfxboot.c32" ]
        then
            echo "ui gfxboot bootlogo isolinux.msg" >> $conf
        else
            echo "gfxboot bootlogo"                 >> $conf
        fi
    fi
    local count=1
    IFS="," ; for i in $KERNEL_LIST;do
        if test ! -z "$i";then
            #======================================
            # setup syslinux requirements
            #--------------------------------------
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            kname=${KERNEL_NAME[$count]}
            if ! echo $gfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$gfix")
                else
                    title=$(makeLabel "$kname [ $gfix ]")
                fi
            elif [ -z "$kiwi_oemtitle" ];then
                title=$(makeLabel "$kname [ $gfix ]")
            else
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$kiwi_oemtitle [ $gfix ]")
                else
                    title=$(makeLabel "$kiwi_oemtitle-$kname [ $gfix ]")
                fi
            fi
            #======================================
            # create standard entry
            #--------------------------------------
            echo "DEFAULT $title"                              >> $conf
            echo "label $title"                                >> $conf
            if xenServer $kname $mountPrefix;then
                systemException \
                    "*** $loader: Xen dom0 boot not implemented ***" \
                "reboot"
            else
                echo "kernel /boot/$kernel"                    >> $conf
                echo -n "append initrd=/boot/$initrd"          >> $conf
                echo -n " root=$diskByID $console"             >> $conf
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
                fi
                echo -n " vga=$fbmode"                         >> $conf
                if [ ! -z "$swap" ];then
                    echo -n " resume=$swapByID"                >> $conf
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"         >> $conf
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"         >> $conf
                fi
                echo -n " $KIWI_INITRD_PARAMS"                 >> $conf
                echo -n " $KIWI_KERNEL_OPTIONS"                >> $conf
                echo " showopts"                               >> $conf
            fi
            #======================================
            # create Failsafe entry
            #--------------------------------------
            title=$(makeLabel "Failsafe -- $title")
            echo "label $title"                                >> $conf
            if xenServer $kname $mountPrefix;then
                systemException \
                    "*** $loader: Xen dom0 boot not implemented ***" \
                "reboot"
            else
                echo "kernel /boot/$kernel"                    >> $conf
                echo -n "append initrd=/boot/$initrd"          >> $conf
                echo -n " root=$diskByID $console"             >> $conf
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)"  >> $conf
                fi
                echo -n " vga=$fbmode"                         >> $conf
                if [ ! -z "$swap" ];then
                    echo -n " resume=$swapByID"                >> $conf
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"         >> $conf
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"         >> $conf
                fi
                echo -n " $KIWI_INITRD_PARAMS"                 >> $conf
                echo -n " $KIWI_KERNEL_OPTIONS"                >> $conf
                echo -n " $failsafe"                           >> $conf
                echo " showopts"                               >> $conf
            fi
            count=$((count + 1))
        fi
    done
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        echo "label Recovery"                             >> $conf
        echo "kernel chain"                               >> $conf
        echo "append hd0 $gdevreco"                       >> $conf
    fi
    #======================================
    # create sysconfig/bootloader
    #--------------------------------------
    echo "LOADER_TYPE=\"$loader\""                           > $sysb
    echo "LOADER_LOCATION=\"mbr\""                           >> $sysb
    echo "DEFAULT_VGA=\"$fbmode\""                           >> $sysb 
    echo -n "DEFAULT_APPEND=\"root=$diskByID"                >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo " showopts\""                                       >> $sysb
    echo "FAILSAFE_VGA=\"$fbmode\""                          >> $sysb
    echo -n "FAILSAFE_APPEND=\"root=$diskByID"               >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo -n " $failsafe"                                     >> $sysb
    echo "\""                                                >> $sysb
}
#======================================
# setupBootLoaderGrub
#--------------------------------------
function setupBootLoaderGrub {
    # /.../
    # create grub.conf and menu.lst file used for
    # installing the bootloader
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gnum=$3         # grub boot partition ID
    local rdev=$4         # grub root partition
    local gfix=$5         # grub title postfix
    local swap=$6         # optional swap partition
    local menu=$destsPrefix/boot/grub/menu.lst
    local conf=$destsPrefix/etc/grub.conf
    local dmap=$destsPrefix/boot/grub/device.map
    local sysb=$destsPrefix/etc/sysconfig/bootloader
    local stage=/boot/grub/stage2
    local console=""
    local kname=""
    local kernel=""
    local initrd=""
    local title=""
    local rdisk=""
    local fbmode=$vga
    if [ ! -z "$kiwi_oemrecovery" ];then
        local gdevreco=$((recoid - 1))
    fi
    if [ -z "$fbmode" ];then
        fbmode=$DEFAULT_VGA
    fi
    #======================================
    # check for device by ID
    #--------------------------------------
    local diskByID=$(getDiskID $rdev)
    local swapByID=$(getDiskID $swap swap)
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $mountPrefix/image/.profile ];then
        importFile < $mountPrefix/image/.profile
    fi
    #======================================
    # check for bootloader displayname
    #--------------------------------------
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$kiwi_cmdline" ];then
        KIWI_KERNEL_OPTIONS="$KIWI_KERNEL_OPTIONS $kiwi_cmdline"
    fi
    #======================================
    # check for grub device
    #--------------------------------------
    if [ -z "$gnum" ];then
        gnum=1
    fi
    #======================================
    # check for grub title postfix
    #--------------------------------------
    if [ -z "$gfix" ];then
        gfix="unknown"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ -z "$kiwi_boot_timeout" ];then
        kiwi_boot_timeout=10;
    fi
    #======================================
    # create directory structure
    #--------------------------------------
    for dir in $menu $conf $dmap $sysb;do
        dir=`dirname $dir`; mkdir -p $dir
    done
    #======================================
    # setup grub device node
    #--------------------------------------
    gdev="(hd0,$gnum)"
    #======================================
    # create menu.lst file
    #--------------------------------------
    echo "timeout $kiwi_boot_timeout"  > $menu
    if [ -f $mountPrefix/boot/grub/splash.xpm.gz ];then
        echo "splashimage=$gdev/boot/grub/splash.xpm.gz" >> $menu
    elif [ -f /image/loader/message ] || [ -f /boot/message ];then
        echo "gfxmenu $gdev/boot/message" >> $menu
    fi
    local count=1
    IFS="," ; for i in $KERNEL_LIST;do
        if test ! -z "$i";then
            #======================================
            # create grub requirements
            #--------------------------------------
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            kname=${KERNEL_NAME[$count]}
            if ! echo $gfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$gfix")
                else
                    title=$(makeLabel "$kname [ $gfix ]")
                fi
            elif [ -z "$kiwi_oemtitle" ];then
                title=$(makeLabel "$kname [ $gfix ]")
            else
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$kiwi_oemtitle [ $gfix ]")
                else
                    title=$(makeLabel "$kiwi_oemtitle-$kname [ $gfix ]")
                fi
            fi
            #======================================
            # create standard entry
            #--------------------------------------
            echo "title $title"                                   >> $menu
            if xenServer $kname $mountPrefix;then
                echo " root $gdev"                                >> $menu
                echo " kernel /boot/xen.gz"                       >> $menu
                echo -n " module /boot/$kernel"                   >> $menu
                echo -n " root=$diskByID"                         >> $menu
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
                fi
                echo -n " $console vga=$fbmode"                   >> $menu
                if [ ! -z "$swap" ];then
                    echo -n " resume=$swapByID"                   >> $menu
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"            >> $menu
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"            >> $menu
                fi
                echo -n " $KIWI_INITRD_PARAMS"                    >> $menu
                echo -n " $KIWI_KERNEL_OPTIONS"                   >> $menu
                echo " showopts"                                  >> $menu
                echo " module /boot/$initrd"                      >> $menu
            else
                echo -n " kernel $gdev/boot/$kernel"              >> $menu
                echo -n " root=$diskByID"                         >> $menu
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
                fi
                echo -n " $console vga=$fbmode"                   >> $menu
                if [ ! -z "$swap" ];then
                    echo -n " resume=$swapByID"                   >> $menu
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"            >> $menu
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"            >> $menu
                fi
                echo -n " $KIWI_INITRD_PARAMS"                    >> $menu
                echo -n " $KIWI_KERNEL_OPTIONS"                   >> $menu
                echo " showopts"                                  >> $menu
                echo " initrd $gdev/boot/$initrd"                 >> $menu
            fi
            #======================================
            # create failsafe entry
            #--------------------------------------
            title=$(makeLabel "Failsafe -- $title")
            echo "title $title"                                   >> $menu
            if xenServer $kname $mountPrefix;then
                echo " root $gdev"                                >> $menu
                echo " kernel /boot/xen.gz"                       >> $menu
                echo -n " module /boot/$kernel"                   >> $menu
                echo -n " root=$diskByID"                         >> $menu
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
                fi
                echo -n " $console vga=$fbmode"                   >> $menu
                echo -n " $KIWI_INITRD_PARAMS"                    >> $menu
                echo -n " $KIWI_KERNEL_OPTIONS"                   >> $menu
                echo -n " $failsafe"                              >> $menu
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"            >> $menu
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"            >> $menu
                fi
                echo " showopts"                                  >> $menu
                echo " module /boot/$initrd"                      >> $menu
            else
                echo -n " kernel $gdev/boot/$kernel"              >> $menu
                echo -n " root=$diskByID"                         >> $menu
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $menu
                fi
                echo -n " $console vga=$fbmode"                   >> $menu
                echo -n " $KIWI_INITRD_PARAMS"                    >> $menu
                echo -n " $KIWI_KERNEL_OPTIONS"                   >> $menu
                echo -n " $failsafe"                              >> $menu
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"            >> $menu
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc console=tty"            >> $menu
                fi
                echo " showopts"                                  >> $menu
                echo " initrd $gdev/boot/$initrd"                 >> $menu
            fi
            count=$((count + 1))
        fi
    done
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        echo "title Recovery"                             >> $menu
        echo " rootnoverify (hd0,$gdevreco)"              >> $menu
        echo " chainloader +1"                            >> $menu
    fi
    #======================================
    # create grub.conf file
    #--------------------------------------
    echo "root $gdev" > $conf
    if dd if=$rdev bs=1 count=512 | file - | grep -q Bootloader;then
        echo "setup --stage2=$stage $gdev" >> $conf
    else
        echo "setup --stage2=$stage (hd0)" >> $conf
    fi
    echo "quit" >> $conf
    #======================================
    # create grub device map
    #--------------------------------------
    rdisk=`echo $rdev | sed -e s"@[0-9]@@g"`
    if [ ! -z "$imageDiskDevice" ];then
        rdisk=$imageDiskDevice
    fi
    rdisk=$(getDiskID $rdisk)
    echo "(hd0) $rdisk" > $dmap
    #======================================
    # create sysconfig/bootloader
    #--------------------------------------
    echo "LOADER_TYPE=\"grub\""                               > $sysb
    echo "LOADER_LOCATION=\"mbr\""                           >> $sysb
    echo "DEFAULT_VGA=\"$fbmode\""                           >> $sysb  
    echo -n "DEFAULT_APPEND=\"root=$diskByID"                >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo " showopts\""                                       >> $sysb
    echo "FAILSAFE_VGA=\"$fbmode\""                          >> $sysb
    echo -n "FAILSAFE_APPEND=\"root=$diskByID"               >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo -n " $failsafe"                                     >> $sysb
    echo "\""                                                >> $sysb
}
#======================================
# setupBootLoaderGrub2
#--------------------------------------
function setupBootLoaderGrub2 {
    # /.../
    # create/update default grub2 configuration
    # ----
    local IFS=$IFS_ORIG
    #======================================
    # function paramters
    #--------------------------------------
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local gnum=$3         # grub boot partition ID
    local rdev=$4         # grub root partition
    local gfix=$5         # grub title postfix
    local swap=$6         # optional swap partition
    #======================================
    # local variables
    #--------------------------------------
    local kname=$(uname -r)
    local title
    local cmdline
    local timeout
    local vesa
    local loader_type="grub2"
    #======================================
    # vesa hex => resolution table
    #--------------------------------------
    vesa[0x301]="640x480"
    vesa[0x310]="640x480"
    vesa[0x311]="640x480"
    vesa[0x312]="640x480"
    vesa[0x303]="800x600"
    vesa[0x313]="800x600"
    vesa[0x314]="800x600"
    vesa[0x315]="800x600"
    vesa[0x305]="1024x768"
    vesa[0x316]="1024x768"
    vesa[0x317]="1024x768"
    vesa[0x318]="1024x768"
    vesa[0x307]="1280x1024"
    vesa[0x319]="1280x1024"
    vesa[0x31a]="1280x1024"
    vesa[0x31b]="1280x1024"
    #======================================
    # setup ID device names
    #--------------------------------------
    local rootByID=$(getDiskID $rdev)
    local swapByID=$(getDiskID $swap swap)
    local diskByID=$(getDiskID $imageDiskDevice)
    if [ "$FSTYPE" = "zfs" ];then
        rootByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # setup path names
    #--------------------------------------
    local orig_sysimg_profile=$mountPrefix/image/.profile
    local inst_default_grub=$destsPrefix/etc/default/grub
    local inst_default_grubdev=$destsPrefix/etc/default/grub_installdevice
    local inst_default_grubmap=$destsPrefix/boot/grub2/device.map
    local unifont=$mountPrefix/usr/share/grub2/unicode.pf2
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $orig_sysimg_profile ];then
        importFile < $orig_sysimg_profile
    fi
    #======================================
    # setup title name
    #--------------------------------------
    if [ -z "$gfix" ];then
        gfix="unknown"
    fi
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    if ! echo $gfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
        title=$(makeLabel "$gfix")
    elif [ -z "$kiwi_oemtitle" ];then
        title=$(makeLabel "$kname [ $gfix ]")
    else
        title=$(makeLabel "$kiwi_oemtitle [ $gfix ]")
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$KIWI_KERNEL_OPTIONS" ];then
        cmdline="$cmdline $KIWI_KERNEL_OPTIONS"
    fi
    if [ ! -z "$KIWI_INITRD_PARAMS" ];then
        cmdline="$cmdline $KIWI_INITRD_PARAMS";
    fi
    if [ ! -z "$rootByID" ];then
        cmdline="$cmdline root=$rootByID"
    fi
    if [ ! -z "$diskByID" ];then
        cmdline="$cmdline disk=$diskByID"
    fi
    if [ ! -z "$swapByID" ];then
        cmdline="$cmdline resume=$swapByID"
    fi
    if [ ! -z "$kiwi_cmdline" ];then
        cmdline="$cmdline $kiwi_cmdline"
    fi
    if [ -e /dev/xvc0 ];then
        cmdline="$cmdline console=xvc console=tty"
    elif [ -e /dev/hvc0 ];then
        cmdline="$cmdline console=hvc console=tty"
    fi
    if [[ ! $cmdline =~ quiet ]];then
        cmdline="$cmdline quiet"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ -z "$kiwi_boot_timeout" ];then
        timeout=10;
    fi
    #======================================
    # write etc/default/grub
    #--------------------------------------
    mkdir -p $destsPrefix/etc/default
cat > $inst_default_grub << EOF
GRUB_DISTRIBUTOR=$(printf %q "$title")
GRUB_DEFAULT=0
GRUB_HIDDEN_TIMEOUT=0
GRUB_HIDDEN_TIMEOUT_QUIET=true
GRUB_TIMEOUT=$timeout
GRUB_CMDLINE_LINUX_DEFAULT="$cmdline"
GRUB_CMDLINE_LINUX=""
EOF
    #======================================
    # set terminal mode
    #--------------------------------------
    if [ -e $unifont ];then
        echo "GRUB_TERMINAL=gfxterm"  >> $inst_default_grub
    else
        echo "GRUB_TERMINAL=console"  >> $inst_default_grub
    fi
    #======================================
    # write etc/default/grub_installdevice
    #--------------------------------------
cat > $inst_default_grubdev << EOF
$diskByID
EOF
    #======================================
    # write boot/grub2/device.map
    #--------------------------------------
    mkdir -p $destsPrefix/boot/grub2
cat > $inst_default_grubmap << EOF
(hd0) $diskByID
EOF
    #======================================
    # Use linuxefi/initrdefi if needed
    #--------------------------------------
    if [ "$kiwi_firmware" = "uefi" ] || [ "$kiwi_firmware" = "efi" ];then
        case $arch in
          i?86|x86_64)
            echo "GRUB_USE_LINUXEFI=true"  >> $inst_default_grub
            echo "GRUB_USE_INITRDEFI=true" >> $inst_default_grub
            ;;
        esac
        loader_type="grub2-efi"
    fi
    #======================================
    # write vesa vga setup
    #--------------------------------------
    if [ ! -z "$kiwi_vga" ] && [ ! -z "${vesa[$kiwi_vga]}" ];then
        echo "GRUB_GFXMODE=${vesa[$kiwi_vga]}" >> $inst_default_grub
        echo "GRUB_GFXPAYLOAD_LINUX=${vesa[$kiwi_vga]}" >> $inst_default_grub
    else
        echo "GRUB_GFXMODE=${vesa[$DEFAULT_VGA]}" >> $inst_default_grub
        echo "GRUB_GFXPAYLOAD_LINUX=keep" >> $inst_default_grub
    fi
    #======================================
    # write bootloader theme setup
    #--------------------------------------
    if [ ! -z "$kiwi_loader_theme" ];then
        local theme=/boot/grub2/themes/$kiwi_loader_theme/theme.txt
        local bgpng=/boot/grub2/themes/$kiwi_loader_theme/background.png
        echo "GRUB_THEME=\"$theme\""      >> $inst_default_grub
        echo "GRUB_BACKGROUND=\"$bgpng\"" >> $inst_default_grub
    fi
    #======================================
    # write bootloader timeout setup
    #--------------------------------------
    if [ ! -z "$kiwi_boot_timeout" ];then
        echo "GRUB_TIMEOUT=\"$kiwi_boot_timeout\"" >> $inst_default_grub
    fi
    #======================================
    # enable rollback capability
    #--------------------------------------
    if [ "$FSTYPE" = "btrfs" ];then
        echo "SUSE_BTRFS_SNAPSHOT_BOOTING=true" >> $inst_default_grub
    fi
    #======================================
    # create sysconfig/bootloader
    #--------------------------------------
    mkdir -p $destsPrefix/etc/sysconfig
    local sysb=$destsPrefix/etc/sysconfig/bootloader
    echo "LOADER_TYPE=\"$loader_type\""            > $sysb
    echo "LOADER_LOCATION=\"mbr\""                >> $sysb
    echo "DEFAULT_APPEND=\"$cmdline\""            >> $sysb
    echo "FAILSAFE_APPEND=\"$failsafe $cmdline\"" >> $sysb
    #======================================
    # Cleanup protective MBR
    #--------------------------------------
    if [ ! -z "$needProtectiveMBR" ];then
        updateProtectiveMBR
    fi
}
#======================================
# setupBootLoaderYaboot
#--------------------------------------
function setupBootLoaderYaboot {
    # /.../
    # create lilo.conf file used for installing the bootloader
    # this file is converted to yaboot.conf therefore lilo.conf
    # has some restrictions
    # ----
    local IFS=$IFS_ORIG
    local mountPrefix=$1  # mount path of the image
    local destsPrefix=$2  # base dir for the config files
    local lnum=$3         # lilo boot partition ID
    local rdev=$4         # lilo root partition
    local lfix=$5         # lilo title postfix
    local swap=$6         # optional swap partition
    local conf=$destsPrefix/etc/lilo.conf
    local sysb=$destsPrefix/etc/sysconfig/bootloader
    local console=""
    local kname=""
    local kernel=""
    local initrd=""
    local title=""
    local rdisk=""
    local fbmode=$vga
    local loader_type=lilo
    if [[ $arch =~ ppc64 ]];then
        loader_type=ppc
    fi
    if [ -z "$fbmode" ];then
        fbmode=$DEFAULT_VGA
    fi
    #======================================
    # check for device by ID
    #--------------------------------------
    local diskByID=`getDiskID $rdev`
    local swapByID=`getDiskID $swap swap`
    if [ "$FSTYPE" = "zfs" ];then
        diskByID="ZFS=kiwipool/ROOT/system-1"
    fi
    #======================================
    # check for bootloader displayname
    #--------------------------------------
    if [ -z "$kiwi_oemtitle" ] && [ ! -z "$kiwi_displayname" ];then
        kiwi_oemtitle=$kiwi_displayname
    fi
    #======================================
    # check for system image .profile
    #--------------------------------------
    if [ -f $mountPrefix/image/.profile ];then
        importFile < $mountPrefix/image/.profile
    fi
    #======================================
    # check for kernel options
    #--------------------------------------
    if [ ! -z "$kiwi_cmdline" ];then
        KIWI_KERNEL_OPTIONS="$KIWI_KERNEL_OPTIONS $kiwi_cmdline"
    fi
    #======================================
    # check for lilo title postfix
    #--------------------------------------
    if [ -z "$lfix" ];then
        lfix="unknown"
    fi
    #======================================
    # check for boot TIMEOUT
    #--------------------------------------
    if [ -z "$kiwi_boot_timeout" ];then
        kiwi_boot_timeout=10;
    fi
    #======================================
    # setup lilo boot device
    #--------------------------------------
    rdisk=`echo $rdev | sed -e s"@[0-9]@@g"`
    if [ ! -z "$imageDiskDevice" ];then
        rdisk=$imageDiskDevice
    fi
    rdev=$(ddn $(dn $rdisk) $lnum)
    #======================================
    # create directory structure
    #--------------------------------------
    for dir in $conf $sysb;do
        dir=`dirname $dir`; mkdir -p $dir
    done
    #======================================
    # create lilo.conf file
    #--------------------------------------
    local timeout=$((kiwi_boot_timeout * 10))
    echo "boot=$rdev"                                        >  $conf
    echo "activate"                                          >> $conf
    echo "timeout=$timeout"                                  >> $conf
    local count=1
    IFS="," ; for i in $KERNEL_LIST;do
        if test ! -z "$i";then
            #======================================
            # create lilo requirements
            #--------------------------------------
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            kname=${KERNEL_NAME[$count]}
            if ! echo $lfix | grep -E -q "OEM|USB|VMX|NET|unknown";then
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$lfix")
                else
                    title=$(makeLabel "$kname [ $lfix ]")
                fi
            elif [ -z "$kiwi_oemtitle" ];then
                title=$(makeLabel "$kname [ $lfix ]")
            else
                if [ "$count" = "1" ];then
                    title=$(makeLabel "$kiwi_oemtitle [ $lfix ]")
                else
                    title=$(makeLabel "$kiwi_oemtitle-$kname [ $lfix ]")
                fi
            fi
            #======================================
            # create standard entry
            #--------------------------------------
            if xenServer $kname $mountPrefix;then
                systemException \
                    "*** lilo: Xen dom0 boot not implemented ***" \
                "reboot"
            else
                echo "default=\"$title\""                 >> $conf
                echo "image=/boot/$kernel"                    >> $conf
                echo "label=\"$title\""                       >> $conf
                echo "initrd=/boot/$initrd"                   >> $conf
                echo -n "append=\"sysrq=1 panic=9"            >> $conf
                echo -n " root=$diskByID"                     >> $conf
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $conf
                fi
                echo -n " $console vga=$fbmode"               >> $conf
                if [ ! -z "$swap" ];then                     
                    echo -n " resume=$swapByID"               >> $conf
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"        >> $conf
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc0 console=tty"       >> $conf
                fi
                echo -n " $KIWI_INITRD_PARAMS"                >> $conf
                echo -n " $KIWI_KERNEL_OPTIONS"               >> $conf
                echo " showopts\""                            >> $conf
            fi
            #======================================
            # create failsafe entry
            #--------------------------------------
            title=$(makeLabel "Failsafe -- $title")
            if xenServer $kname $mountPrefix;then
                systemException \
                    "*** lilo: Xen dom0 boot not implemented ***" \
                "reboot"
            else
                echo "image=/boot/$kernel"                    >> $conf
                echo "label=\"$title\""                       >> $conf
                echo "initrd=/boot/$initrd"                   >> $conf
                echo -n "append=\"sysrq=1 panic=9"            >> $conf
                echo -n " root=$diskByID"                     >> $conf
                if [ ! -z "$imageDiskDevice" ];then
                    echo -n " disk=$(getDiskID $imageDiskDevice)" >> $conf
                fi
                echo -n " $console vga=$fbmode"               >> $conf
                if [ ! -z "$swap" ];then
                    echo -n " resume=$swapByID"               >> $conf
                fi
                if [ -e /dev/xvc0 ];then
                    echo -n " console=xvc console=tty"        >> $conf
                elif [ -e /dev/hvc0 ];then
                    echo -n " console=hvc0 console=tty"       >> $conf
                fi
                echo -n " $KIWI_INITRD_PARAMS"                >> $conf
                echo -n " $KIWI_KERNEL_OPTIONS"               >> $conf
                echo -n " $failsafe"                          >> $conf
                echo " showopts\""                            >> $conf
            fi
            count=$((count + 1))
        fi
    done
    #======================================
    # create recovery entry
    #--------------------------------------
    if [ ! -z "$kiwi_oemrecovery" ];then
        systemException \
            "*** lilo: recovery chain loading not implemented ***" \
        "reboot"
    fi
    #======================================
    # create sysconfig/bootloader
    #--------------------------------------
    echo "LOADER_TYPE=\"$loader_type\""                       > $sysb
    echo "LOADER_LOCATION=\"mbr\""                           >> $sysb
    echo "DEFAULT_VGA=\"$fbmode\""                           >> $sysb 
    echo -n "DEFAULT_APPEND=\"root=$diskByID"                >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo " showopts\""                                       >> $sysb
    echo "FAILSAFE_VGA=\"$fbmode\""                          >> $sysb
    echo -n "FAILSAFE_APPEND=\"root=$diskByID"               >> $sysb
    if [ ! -z "$swap" ];then
        echo -n " resume=$swapByID"                          >> $sysb
    fi
    echo -n " $KIWI_INITRD_PARAMS $KIWI_KERNEL_OPTIONS"      >> $sysb
    echo -n " $failsafe"                                     >> $sysb
    echo "\""                                                >> $sysb
}
#======================================
# setupDefaultPXENetwork
#--------------------------------------
function setupDefaultPXENetwork {
    # /.../
    # create the /sysconfig/network file according to the PXE
    # boot interface.
    # ----
    local IFS=$IFS_ORIG
    if [ -z "$PXE_IFACE" ];then
        return
    fi
    local prefix=$1
    local niface=$prefix/etc/sysconfig/network/ifcfg-$PXE_IFACE
    mkdir -p $prefix/etc/sysconfig/network
    cat > $niface < /dev/null
    echo "BOOTPROTO='dhcp'"    >> $niface
    echo "STARTMODE='ifplugd'" >> $niface
    echo "USERCONTROL='no'"    >> $niface
}
#======================================
# setupDefaultFstab
#--------------------------------------
function setupDefaultFstab {
    # /.../
    # Update or create new /etc/fstab file with the default entries
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    local nfstab=$prefix/etc/fstab
    mkdir -p $prefix/etc
    grep -q devpts $nfstab || \
        echo "devpts  /dev/pts          devpts  mode=0620,gid=5 0 0"  >> $nfstab
    grep -q proc $nfstab || \
        echo "proc    /proc             proc    defaults        0 0"  >> $nfstab
    grep -q sysfs $nfstab || \
        echo "sysfs   /sys              sysfs   noauto          0 0"  >> $nfstab
    grep -q debugfs $nfstab || test -e /sys/kernel/debug && \
        echo "debugfs /sys/kernel/debug debugfs noauto          0 0"  >> $nfstab
    grep -q usbfs $nfstab || test -e /proc/bus/usb && \
        echo "usbfs   /proc/bus/usb     usbfs   noauto          0 0"  >> $nfstab
    grep -q /run $nfstab || test -e /run && \
        echo "tmpfs   /run              tmpfs   noauto          0 0"  >> $nfstab
}
#======================================
# updateRootDeviceFstab
#--------------------------------------
function updateRootDeviceFstab {
    # /.../
    # add one line to the fstab file for the root device
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    local config_tmp=$1
    local rdev=$2
    local nfstab=$config_tmp/etc/fstab
    local diskByID=$(getDiskID $rdev)
    local opts=defaults
    #======================================
    # check for custom options
    #--------------------------------------
    if [ ! -z "$kiwi_fsmountoptions" ] && [ ! $FSTYPE = "zfs" ];then
        opts=$kiwi_fsmountoptions
    fi
    #======================================
    # check for NFSROOT
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        local server=$(echo $rdev | cut -f3 -d" ")
        local option=$(echo $rdev | cut -f2 -d" ")
        echo "$server / nfs $option 0 0" >> $nfstab
        return
    fi
    #======================================
    # check for device by ID
    #--------------------------------------
    if [ -z "$UNIONFS_CONFIG" ]; then
        echo "$diskByID / $FSTYPE $opts 1 1" >> $nfstab
    else
        echo "/dev/root / auto defaults 1 1" >> $nfstab
    fi
    #======================================
    # check for LVM volume setup
    #--------------------------------------
    if [ "$haveLVM" = "yes" ];then
        local variable
        local volume
        local content
        local volpath
        local mpoint
        local mppath
        for i in $(cat /.profile | grep -E 'kiwi_LVM_|kiwi_allFreeVolume');do
            variable=$(echo $i|cut -f1 -d=)
            volume=$(echo $i| cut -f3- -d_ | cut -f1 -d=)
            content=$(echo $i|cut -f2 -d= | tr -d \' | tr -d \")
            volpath=$(echo $content | cut -f3 -d:)
            if [ -z "$volpath" ];then
                volpath=$(echo $volume | tr _ /)
            fi
            mpoint=$(echo $volpath | sed -e s@^LV@@)
            mppath="/dev/$kiwi_lvmgroup/$volume"
            if \
                [ ! $volume = "LVRoot" ] && \
                [ ! $volume = "LVComp" ] && \
                [ ! $volume = "LVSwap" ]
            then
                echo "$mppath /$mpoint $FSTYPE $opts 1 2" >> $nfstab
            fi
        done
    elif [ "$FSTYPE" = "btrfs" ];then
        local fsuuid=$(blkid $rdev -s UUID -o value)
        for subvol in $(btrfs subvol list $prefix |grep -v @ |cut -f9 -d' ');do
            echo "UUID=$fsuuid /$subvol btrfs subvol=@/$subvol 0 0" >> $nfstab
        done
    fi
}
#======================================
# updateSwapDeviceFstab
#--------------------------------------
function updateSwapDeviceFstab {
    # /.../
    # add one line to the fstab file for the swap device
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    local sdev=$2
    local diskByID=`getDiskID $sdev`
    local nfstab=$prefix/etc/fstab
    echo "$diskByID swap swap defaults 0 0" >> $nfstab
}
#======================================
# updateBootDeviceFstab
#--------------------------------------
function updateBootDeviceFstab {
    # /.../
    # add temporary bind mounted boot entry to fstab
    # ----
    local IFS=$IFS_ORIG
    local config_tmp=$1
    local sdev=$2
    local nfstab=$config_tmp/etc/fstab
    local mount=boot_bind
    local prefix=/mnt
    #======================================
    # Store boot entry
    #--------------------------------------
    if [ -e $prefix/$mount ];then
        local diskByID=$(getDiskID $sdev)
        if [ ! -z "$FSTYPE" ];then
            FSTYPE_SAVE=$FSTYPE
        fi
        probeFileSystem $sdev
        if [ -z "$FSTYPE" ] || [ "$FSTYPE" = "unknown" ];then
            FSTYPE="auto"
        fi
        echo "$diskByID /$mount $FSTYPE defaults 1 2" >> $nfstab
        echo "/$mount/boot /boot none bind 0 0" >> $nfstab
        if [ ! -z "$FSTYPE_SAVE" ];then
            FSTYPE=$FSTYPE_SAVE
        fi
    fi
    #======================================
    # Store boot/efi entry
    #--------------------------------------
    if [ ! -z "$kiwi_JumpPart" ];then
        local jdev=$(ddn $imageDiskDevice $kiwi_JumpPart)
        local fstype=$(blkid $jdev -s TYPE -o value)
        local label=$(blkid $jdev -s LABEL -o value)
        if [ ! -z "$fstype" ] && [ "$label" = "EFI" ];then
            jdev=$(getDiskID $jdev)
            echo "$jdev /boot/efi $fstype defaults 0 0" >> $nfstab
        fi
        if [ ! -z "$fstype" ] && [ "$label" = "ZIPL" ];then
            jdev=$(getDiskID $jdev)
            echo "$jdev /boot/zipl $fstype defaults 0 0" >> $nfstab
        fi
    fi
}
#======================================
# updateOtherDeviceFstab
#--------------------------------------
function updateOtherDeviceFstab {
    # /.../
    # check the contents of the $PART variable and
    # add one line to the fstab file for each partition
    # which has a mount point defined.
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    local prefix=$2
    local nfstab=$prefix/etc/fstab
    local index=0
    local field=0
    local count=0
    local device
    local diskByID
    local IFS=","
    if [ -z "$prefix" ];then
        prefix=/mnt
    fi
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        if \
            [ ! -z "$partMount" ]       && \
            [ ! "$partMount" = "x" ]    && \
            [ ! "$partMount" = "swap" ] && \
            [ ! "$partMount" = "/" ]
        then
            if [ ! -z "$RAID" ];then
                device=/dev/md$((count - 1))
            else
                device=$(ddn $DISK $count)
            fi
            probeFileSystem $device
            if [ ! "$FSTYPE" = "luks" ] && [ ! "$FSTYPE" = "unknown" ];then
                if [ ! -d $prefix/$partMount ];then
                    mkdir -p $prefix/$partMount
                fi
                diskByID=$(getDiskID $device)
                echo "$diskByID $partMount $FSTYPE defaults 0 0" >> $nfstab
            fi
        fi
    done
}
#======================================
# setupKernelModules
#--------------------------------------
function setupKernelModules {
    # /.../
    # create sysconfig/kernel file which includes the
    # kernel modules to become integrated into the initrd
    # if created by the distro mkinitrd tool
    # ----
    local IFS=$IFS_ORIG
    local destprefix=$1
    local prefix=$2
    if [ -z "$prefix" ];then
        prefix=/mnt
    fi
    local sysimg_ktempl=$prefix/var/adm/fillup-templates/sysconfig.kernel
    local sysimg_syskernel=$prefix/etc/sysconfig/kernel
    local syskernel=$destprefix/etc/sysconfig/kernel
    local newstyle_mkinitrd=$prefix/lib/mkinitrd/scripts/boot-usb.sh
    local key
    local val
    mkdir -p $destprefix/etc/sysconfig
    #======================================
    # include USB host controllers
    #--------------------------------------
    local USB_MODULES="ehci-hcd ohci-hcd uhci-hcd xhci-hcd"
    INITRD_MODULES="$INITRD_MODULES $USB_MODULES"
    #======================================
    # check for mkinitrd capabilities
    #--------------------------------------
    if [ ! -e $newstyle_mkinitrd ];then
        # /.../
        # if boot-usb.sh does not exist we are based on an old
        # mkinitrd version which requires all modules as part of
        # sysconfig/kernel. Therefore we include USB core modules
        # required to support USB storage like USB sticks
        # ----
        USB_MODULES="usbcore usb-storage sd"
        INITRD_MODULES="$INITRD_MODULES $USB_MODULES"
        # /.../
        # old mkinitrd cannot figure this out on its own
        # ---
        if [ -e /sys/devices/virtio-pci ];then
            Echo 'Adding virtio kernel modules to initrd.'
            INITRD_MODULES="$INITRD_MODULES virtio-blk virtio-pci"
        fi
    fi
    #======================================
    # use system image config or template
    #--------------------------------------
    if [ -f $sysimg_syskernel ];then
        cp $sysimg_syskernel $syskernel
    elif [ -f $sysimg_ktempl ];then
        cp $sysimg_ktempl $syskernel
    fi
    #======================================
    # update config file
    #--------------------------------------
    for key in INITRD_MODULES DOMU_INITRD_MODULES;do
        if [ $key = "INITRD_MODULES" ];then
            val=$INITRD_MODULES
        fi
        if [ $key = "DOMU_INITRD_MODULES" ];then
            val=$DOMURD_MODULES
        fi
        if [ -z "$val" ];then
            continue
        fi
        sed -i -e \
            s"@^$key=\"\(.*\)\"@$key=\"\1 $val\"@" \
        $syskernel
    done
}
#======================================
# getKernelBootParameters
#--------------------------------------
function getKernelBootParameters {
    # /.../
    # check contents of bootloader configuration
    # and extract cmdline parameters
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    local params
    local files="
        $prefix/boot/syslinux/syslinux.cfg
        $prefix/boot/syslinux/extlinux.conf
        $prefix/boot/grub/menu.lst
        $prefix/etc/lilo.conf
        $prefix/etc/zipl.conf
    "
    for c in $files;do
        if [ -f $c ];then
            params=$(cat $c | grep 'root=' | head -n1)
            break
        fi
    done
    params=$(echo $params | sed -e 's@^append=@@')
    params=$(echo $params | sed -e 's@^append@@')
    params=$(echo $params | sed -e 's@^module@@')
    params=$(echo $params | sed -e 's@^kernel@@')
    params=$(echo $params | sed -e 's@^parameters=@@')
    params=$(echo $params | sed -e 's@"@@g')
    params=$(echo $params)
    echo $params
}
#======================================
# kernelCheck
#--------------------------------------
function kernelCheck {
    # /.../
    # Check the running kernel against the kernel
    # installed in the image. If the version does not 
    # match we need to reboot to activate the system
    # image kernel. This is done by either using kexec
    # or a real reboot is triggered
    # ----
    local IFS=$IFS_ORIG
    local kactive=`uname -r`
    local kreboot=1
    local prefix=$1
    local kernel
    local initrd
    local params
    #======================================
    # check installed and running kernel
    #--------------------------------------
    for i in $prefix/lib/modules/*;do
        if [ ! -d $i ];then
            continue
        fi
        kinstname=${i##*/}
        if [ $kinstname = $kactive ];then
            kreboot=0
            break
        fi
    done
    #======================================
    # check for forced reboot
    #--------------------------------------
    if [ ! -z "$FORCE_KEXEC" ];then
        kreboot=2
    fi
    #======================================
    # evaluate kreboot condition
    #--------------------------------------
    case $kreboot in
        1) Echo "Kernel versions do not match..." ;;
        2) Echo "kexec based reboot forced..." ;;
        0) return ;;
    esac
    #======================================
    # trigger reboot if kexec doesn't exist
    #--------------------------------------
    if [ ! -f /sbin/kexec ];then
        Echo "Reboot triggered in 5 sec..."
        sleep 5 ; /sbin/reboot -f -i
    fi
    #======================================
    # trigger reboot using kexec
    #--------------------------------------
    if [ -f /sbin/kexec ];then
        #======================================
        # find installed kernel / initrd
        #--------------------------------------
        if [ -z "$KERNEL_LIST" ] ; then
            kernelList $prefix
        fi
        IFS="," ; for i in $KERNEL_LIST;do
            if test -z "$i";then
                continue
            fi
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            break
        done
        IFS=$IFS_ORIG
        if [ ! -f $prefix/boot/$kernel ] || [ ! -f $prefix/boot/$initrd ];then
            Echo "Can't find $kernel / $initrd in system image"
            Echo "Reboot triggered in 5 sec..."
            sleep 5 ; /sbin/reboot -f -i
        fi
        #======================================
        # extract bootloader cmdline params
        #--------------------------------------
        params=$(getKernelBootParameters $prefix)
        #======================================
        # load and run kernel...
        #--------------------------------------
        kexec -l $prefix/boot/$kernel \
            --append="$params" --initrd=$prefix/boot/$initrd
        if [ ! $? = 0 ];then
            Echo "Failed to load kernel"
            Echo "Reboot triggered in 5 sec..."
            sleep 5 ; /sbin/reboot -f -i
        fi
        #======================================
        # go for gold
        #--------------------------------------
        exec kexec -e
    fi
}
#======================================
# probeFileSystem
#--------------------------------------
function probeFileSystem {
    # /.../
    # probe for the filesystem type. The function will
    # read 128 kB of the given device and check the
    # filesystem header data to detect the type of the
    # filesystem
    # ----
    local IFS=$IFS_ORIG
    FSTYPE=unknown
    FSTYPE=$(blkid $1 -s TYPE -o value)
    case $FSTYPE in
        btrfs)       FSTYPE=btrfs ;;
        ext4)        FSTYPE=ext4 ;;
        ext3)        FSTYPE=ext3 ;;
        ext2)        FSTYPE=ext2 ;;
        reiserfs)    FSTYPE=reiserfs ;;
        squashfs)    FSTYPE=squashfs ;;
        luks)        FSTYPE=luks ;;
        crypto_LUKS) FSTYPE=luks ;;
        vfat)        FSTYPE=vfat ;;
        clicfs)      FSTYPE=clicfs ;;
        xfs)         FSTYPE=xfs ;;
        udf)         FSTYPE=udf ;;
        zfs_member)  FSTYPE=zfs ;;
        *)
            FSTYPE=unknown
        ;;
    esac
    if [ $FSTYPE = "unknown" ];then
        dd if=$1 of=/tmp/filesystem-$$ bs=128k count=1 >/dev/null
    fi
    if [ $FSTYPE = "unknown" ];then
        if grep -q ^CLIC /tmp/filesystem-$$;then
            FSTYPE=clicfs
        fi
        if grep -q ^hsqs /tmp/filesystem-$$;then
            FSTYPE=squashfs
        fi
    fi
    export FSTYPE
}
#======================================
# getSystemIntegrity
#--------------------------------------
function getSystemIntegrity {
    # /.../
    # check the variable SYSTEM_INTEGRITY which contains
    # information about the status of all image portions
    # per partition. If a number is given as parameter only
    # the information from the image assigned to this partition
    # is returned
    # ----
    local IFS=$IFS_ORIG
    if [ -z "$SYSTEM_INTEGRITY" ];then
        echo "clean"
    else
        echo $SYSTEM_INTEGRITY | cut -f$1 -d:
    fi
}
#======================================
# getSystemMD5Status
#--------------------------------------
function getSystemMD5Status {
    # /.../
    # return the md5 status of the given image number.
    # the function works similar to getSystemIntegrity
    # ----
    local IFS=$IFS_ORIG
    echo $SYSTEM_MD5STATUS | cut -f$1 -d:
}
#======================================
# waitForIdleEventQueue
#--------------------------------------
function waitForIdleEventQueue {
    local IFS=$IFS_ORIG
    local devs=0
    local p_devs=1
    local timeout=5
    Echo -n "Waiting for devices to settle..."
    while true;do
        udevPending
        devs=$(ls -1 /dev | wc -l)
        if [ $devs -eq $p_devs ];then
            break
        fi
        p_devs=$devs
        sleep $timeout
        echo -n .
    done
    echo
}
#======================================
# probeUSB
#--------------------------------------
function probeUSB {
    local IFS=$IFS_ORIG
    local module=""
    local stdevs=""
    local hwicmd="/usr/sbin/hwinfo"
    if [ $HAVE_MODULES_ORDER = 0 ];then
        #======================================
        # load host controller modules
        #--------------------------------------
        IFS="%"
        for i in \
            `$hwicmd --usb | grep "Driver [IA]" | 
            sed -es"@modprobe\(.*\)\"@\1%@" | tr -d "\n"`
        do
            if echo $i | grep -q "#0";then
                module=`echo $i | cut -f2 -d"\"" | tr -d " "`
                module=`echo $module | sed -es"@modprobe@@g"`
                IFS=";"
                for m in $module;do
                    if ! echo $stdevs | grep -q $m;then
                        stdevs="$stdevs $m"
                    fi
                done
            fi
        done
        for i in \
            `$hwicmd --usb-ctrl | grep "Driver [IA]" | 
            sed -es"@modprobe\(.*\)\"@\1%@" | tr -d "\n"`
        do
            if echo $i | grep -q "#0";then
                module=`echo $i | cut -f2 -d"\"" | tr -d " "`
                module=`echo $module | sed -es"@modprobe@@g"`
                IFS=";"
                for m in $module;do
                    if ! echo $stdevs | grep -q $m;then
                        stdevs="$stdevs $m"
                    fi
                done
            fi
        done
        IFS=$IFS_ORIG
        stdevs=`echo $stdevs`
        for module in $stdevs;do
            Echo "Probing module: $module"
            modprobe $module >/dev/null
        done
        #======================================
        # check load status for host controller
        #--------------------------------------
        if [ -z "$stdevs" ];then
            return
        fi
        #======================================
        # manually load storage/input drivers
        #--------------------------------------
        for i in usbhid usb-storage;do
            modprobe $i &>/dev/null
        done
    fi
}
#======================================
# probeDevices
#--------------------------------------
function probeDevices {
    local IFS=$IFS_ORIG
    local skipUSB=$1
    udevPending
    if [ $HAVE_MODULES_ORDER = 0 ];then
        waitForIdleEventQueue
    fi
    #======================================
    # probe USB devices and load modules
    #--------------------------------------
    if [ -z "$skipUSB" ];then
        probeUSB
    fi
    #======================================
    # probe Disk devices and load modules
    #--------------------------------------
    if [ $HAVE_MODULES_ORDER = 0 ];then
        Echo "Including required kernel modules..."
        IFS="%"
        local module=""
        local stdevs=""
        local hwicmd="/usr/sbin/hwinfo"
        for i in \
            `$hwicmd --storage | grep "Driver [IA]" | 
            sed -es"@modprobe\(.*\)\"@\1%@" | tr -d "\n"`
        do
            if echo $i | grep -q "#0";then
                module=`echo $i | cut -f2 -d"\"" | tr -d " "`
                module=`echo $module | sed -es"@modprobe@@g"`
                IFS=";"
                for m in $module;do
                    if ! echo $stdevs | grep -q $m;then
                        stdevs="$stdevs $m"
                    fi
                done
            fi
        done
        IFS=$IFS_ORIG
        stdevs=`echo $stdevs`
        if [ ! -z "$kiwikernelmodule" ];then
            for module in $kiwikernelmodule;do
                Echo "Probing module (cmdline): $module"
                INITRD_MODULES="$INITRD_MODULES $module"
                modprobe $module >/dev/null
            done
        fi
        for module in $stdevs;do
            loadok=1
            for broken in $kiwibrokenmodule;do
                if [ $broken = $module ];then
                    Echo "Prevent loading module: $module"
                    loadok=0; break
                fi
            done
            if [ $loadok = 1 ];then
                Echo "Probing module: $module"
                INITRD_MODULES="$INITRD_MODULES $module"
                modprobe $module >/dev/null
            fi
        done
        hwinfo --block &>/dev/null
        # /.../
        # older systems require ide-disk to be present at any time
        # for details on this crappy call see bug: #250241
        # ----
        modprobe ide-disk &>/dev/null
    else
        if [ ! -z "$kiwikernelmodule" ];then
            for module in $kiwikernelmodule;do
                Echo "Probing module (cmdline): $module"
                INITRD_MODULES="$INITRD_MODULES $module"
                modprobe $module >/dev/null
            done
        fi
    fi
    #======================================
    # Manual loading of modules
    #--------------------------------------
    for i in rd brd edd dm-mod xennet xenblk virtio_blk loop squashfs;do
        modprobe $i &>/dev/null
    done
    udevPending
    if [ $HAVE_MODULES_ORDER = 0 ];then
        waitForIdleEventQueue
    fi
}
#======================================
# USBStickDevice
#--------------------------------------
function USBStickDevice {
    local IFS=$IFS_ORIG
    stickFound=0
    local mode=$1
    local prefix=/mnt
    #======================================
    # search for USB removable devices
    #--------------------------------------
    for device in /sys/bus/usb/drivers/usb-storage/*;do
        if [ ! -L $device ];then
            continue
        fi
        descriptions=$device/host*/target*/*/block*
        for description in $descriptions;do
            if [ ! -d $description ];then
                continue
            fi
            isremovable=$description/removable
            storageID=$(echo $description | cut -f1 -d: | xargs basename)
            devicebID=$(basename $description | cut -f2 -d:)
            if [ $devicebID = "block" ];then
                devicebID=`ls -1 $description`
                isremovable=$description/$devicebID/removable
            fi
            serial="/sys/bus/usb/devices/$storageID/serial"
            device="/dev/$devicebID"
            if [ ! -b $device ];then
                continue;
            fi
            if [ ! -f $isremovable ];then
                continue;
            fi
            if ! partitionSize $device >/dev/null;then
                continue;
            fi
            if [ ! -f $serial ];then
                serial="USB Stick (unknown type)"
            else
                serial=`cat $serial`
            fi
            removable=`cat $isremovable`
            # /.../
            # don't check the removable flag, it could be wrong
            # especially for USB hard disks connected via a
            # USB caddy, details in bug: 535113
            # ----
            removable=1
            if [ $removable -eq 1 ];then
                stickRoot=$device
                stickDevice=$(ddn $device 1)
                for devnr in 1 2;do
                    dev=$(ddn $stickRoot $devnr)
                    if ! kiwiMount "$dev" "$prefix" "-o ro";then
                        continue
                    fi
                    if [ "$mode" = "install" ];then
                        # /.../
                        # USB stick search for install media
                        # created with kiwi
                        # ----
                        if \
                            [ ! -e $prefix/config.isoclient ] && \
                            [ ! -e $prefix/config.usbclient ]
                        then
                            umountSystem
                            continue
                        fi
                    elif [ "$mode" = "kexec" ];then
                        # /.../
                        # USB stick search for hotfix media
                        # with kernel/initrd for later kexec
                        # ----
                        if \
                            [ ! -e $prefix/linux.kexec ] && \
                            [ ! -e $prefix/initrd.kexec ]
                        then
                            umountSystem
                            continue
                        fi
                    else
                        # /.../
                        # USB stick search for Linux system tree
                        # created with kiwi
                        # ----
                        if [ ! -e $prefix/etc/ImageVersion ]; then
                            umountSystem
                            continue
                        fi
                    fi
                    stickFound=1
                    umountSystem
                    break
                done
                if [ "$stickFound" = 0 ];then
                    continue
                fi
                stickSerial=$serial
                return
            fi
        done
    done
}
#======================================
# CDMountOption
#--------------------------------------
function CDMountOption {
    # /.../
    # checks for the ISO 9660 extension and prints the
    # mount option required to mount the device in full
    # speed mode
    # ----
    local IFS=$IFS_ORIG
    local id=$(blkid -o value -s TYPE $1)
    if [ "$id" = "iso9660" ];then
        echo "-t iso9660"
    fi
    if [ "$id" = "udf" ]; then
        echo "-t udf"
    fi
}
#======================================
# searchImageISODevice
#--------------------------------------
function searchImageISODevice {
    # /.../
    # search all devices for the MBR ID stored in the
    # iso header. This function is called to identify the
    # live media and/or install media
    # ----
    local IFS=$IFS_ORIG
    local mbrVID
    local mbrIID
    local count=0
    local isoinfo=/usr/bin/isoinfo
    mkdir -p /cdrom
    if [ ! -x $isoinfo ]; then
       isoinfo=/usr/lib/genisoimage/isoinfo
    fi
    if [ ! -x $isoinfo ];then
        systemException \
            "Can't find isoinfo tool in initrd" \
        "reboot"
    fi
    if [ ! -f /boot/mbrid ];then
        systemException \
            "Can't find MBR id file in initrd" \
        "reboot"
    fi
    mbrIID=$(cat /boot/mbrid)
    udevPending
    #======================================
    # Check for ISO file on storage media
    #--------------------------------------
    if [ ! -z "$isofrom_device" ] && [ ! -z "$isofrom_system" ];then
        Echo "Looking up ISO on $isofrom_device..."
        mkdir /isofrom
        if [[ $isofrom_device =~ nfs: ]];then
            setupNetwork
            isofrom_device=$(echo $isofrom_device | cut -c 5-)
            mount -t nfs -o nolock $isofrom_device /isofrom
        else
            waitForStorageDevice $isofrom_device
            mount $isofrom_device /isofrom
        fi
        if [ ! $? = 0 ];then
            systemException \
                "Failed to mount ISO storage device !" \
            "reboot"
        fi
        biosBootDevice=$(loop_setup /isofrom/$isofrom_system)
        if [ ! $? = 0 ];then
            systemException \
                "Failed to loop setup ISO system !" \
            "reboot"
        fi
        return 0
    fi
    #======================================
    # Search ISO header in device list
    #--------------------------------------
    Echo -n "Searching for boot device in Application ID..."
    while true;do
        for i in /dev/*;do
            if [ ! -b $i ];then
                continue
            fi
            mbrVID=$(
                $isoinfo -d -i $i 2>/dev/null|grep "Application id:"|cut -f2 -d:
            )
            mbrVID=$(echo $mbrVID)
            if [ "$mbrVID" = "$mbrIID" ];then
                # /.../
                # found ISO header on a device, now check if there is
                # also a partition for this device with the same
                # information and prefer that device if it exists
                # ----
                biosBootDevice=$i
                for n in 1 2;do
                    local pdev=$(ddn $i $n)
                    if [ -e $pdev ];then
                        mbrVID=$(
                            $isoinfo -d -i $pdev 2>/dev/null |\
                            grep "Application id:"|cut -f2 -d:
                        )
                        mbrVID=$(echo $mbrVID)
                        if [ "$mbrVID" = "$mbrIID" ];then
                            biosBootDevice=$pdev
                            echo; return 0
                        fi
                    fi
                done
                echo; return 0
            fi
        done
        if [ $count -eq 30 ];then
            systemException \
                "Failed to find MBR identifier !" \
            "reboot"
        fi
        count=$(($count + 1))
        echo -n .
        sleep 1
    done
}
#======================================
# runMediaCheck
#--------------------------------------
function runMediaCheck {
    # /.../
    # run checkmedia program on the specified device
    # ----
    local IFS=$IFS_ORIG
    local device_iso=$biosBootDevice
    local device_sdx=$(dn $biosBootDevice)
    if [ -e "$device_sdx" ];then
        device_iso=$device_sdx
    fi
    if ! checkmedia $device_iso;then
        systemException \
            "ISO check failed, you have been warned" \
        "waitkey"
    else
        Echo "ISO check passed"
        Echo "Press any key to continue (waiting $MEDIACHECK_OK_TIMER sec...)"
        read -s -n 1 -t $MEDIACHECK_OK_TIMER
    fi
}
#======================================
# setupHybridFeatures
#--------------------------------------
function setupHybridPersistent {
    # /.../
    # create a write partition for hybrid images if requested
    # and store the device name in HYBRID_RW
    # ----
    local IFS=$IFS_ORIG
    if [ ! "$kiwi_hybridpersistent" = "true" ];then
        return
    fi
    local diskDevice=$(dn $biosBootDevice)
    #======================================
    # create write partition for hybrid
    #--------------------------------------
    if [ -z "$kiwi_cowdevice" ] && [ -z "$kiwi_cowsystem" ];then
        #======================================
        # try to create a write partition
        #--------------------------------------
        createHybridPersistent $diskDevice
    else
        #======================================
        # use given cow device
        #--------------------------------------
        createCustomHybridPersistent
    fi
    #======================================
    # check hybrid write partition device
    #--------------------------------------
    if [ ! -e "$HYBRID_RW" ]; then
        # /.../
        # failed to create read-write partition
        # disable persistent writing
        # ----
        unset HYBRID_RW
        unset kiwi_hybridpersistent
        export skipSetupBootPartition=1
    fi
}
#======================================
# CDUmount
#--------------------------------------
function CDUmount {
    # /.../
    # umount the CD device
    # ----
    local IFS=$IFS_ORIG
    umount $biosBootDevice
}
#======================================
# CDEject
#--------------------------------------
function CDEject {
    local IFS=$IFS_ORIG
    eject $biosBootDevice
}
#======================================
# searchOFBootDevice
#--------------------------------------
function searchOFBootDevice {
    # /.../
    # search for the device with the OF PROM id
    # this is required for the ppc boot architecture
    # as we don't have a BIOS and a MBR here
    # ----
    local IFS=$IFS_ORIG
    local ofdev=`cat /proc/device-tree/chosen/bootpath|cut -f1 -d:`
    local h=/usr/sbin/ofpathname
    local ddevs=`$h -l $ofdev`
    #======================================
    # Store device with PROM id 
    #--------------------------------------
    for curd in $ddevs;do
        if [ $curd = "sda" -o $curd = "vda" ];then
            export biosBootDevice="/dev/$curd"
            return 0
        fi
    done
    export biosBootDevice="Can't find OF boot device"
    return 1
}
#======================================
# searchBusIDBootDevice
#--------------------------------------
function searchBusIDBootDevice {
    # /.../
    # check for a DASD or ZFCP devices
    # like they exist on the s390 architecture. If found the
    # device is set online and the biosBootDevice variable
    # is set to this device for further processing
    # ----
    local IFS=$IFS_ORIG
    local dpath=/dev/disk/by-path
    local ipl_type=$(cat /sys/firmware/ipl/ipl_type)
    local deviceID=$(cat /sys/firmware/ipl/device)
    local dev_type=$(cat /sys/bus/ccw/devices/$deviceID/devtype)
    local wwpn
    local slun
    #======================================
    # check for custom device init command
    #--------------------------------------
    if [ ! -z "$DEVICE_INIT" ];then
        if ! eval $DEVICE_INIT;then
            export biosBootDevice="Failed to call: $DEVICE_INIT"
            return 1
        fi
        export biosBootDevice=$DISK
        return 0
    fi
    #======================================
    # determine device type: dasd or zfcp
    #--------------------------------------
    if [ -z "$deviceID" ];then
        systemException \
            "Can't find IPL device" \
        "reboot"
    fi
    if [ "$ipl_type" = "fcp" ];then
        # plain FCP device 512b blocksize
        haveZFCP=1
    elif [ "$ipl_type" = "ccw" ];then
        if [[ "$dev_type" =~ "3390" ]];then
            # plain DASD device 4k blocksize
            haveDASD=1
        elif [[ "$dev_type" =~ "9336" ]];then
            # emulated DASD device 512b blocksize, handled as FCP device
            # but don't configure host and disk as required for plain
            # FCP devices
            haveZFCP=1
        else
            systemException \
                "Unknown Device type: $dev_type" \
            "reboot"
        fi
    else
        systemException \
            "Unknown IPL type: $ipl_type" \
        "reboot"
    fi
    #======================================
    # check if we can find the device
    #--------------------------------------
    if [ ! -e /sys/bus/ccw/devices/$deviceID ];then
        systemException \
            "Can't find disk with ID: $deviceID" \
        "reboot"
    fi
    #======================================
    # DASD real in CDL / LDL mode
    #--------------------------------------
    if [ $haveDASD -eq 1 ];then
        dasd_configure $deviceID 1 0
        biosBootDevice="$dpath/ccw-$deviceID"
    fi
    #======================================
    # DASD emulated in FBA mode
    #--------------------------------------
    if [ $haveZFCP -eq 1 ] && [ "$ipl_type" = "ccw" ];then
        dasd_configure $deviceID 1 0
        biosBootDevice="$dpath/ccw-$deviceID"
    fi
    #======================================
    # ZFCP real in SCSI mode
    #--------------------------------------
    if [ $haveZFCP -eq 1 ] && [ "$ipl_type" = "fcp" ];then
        wwpn=$(cat /sys/firmware/ipl/wwpn)
        slun=$(cat /sys/firmware/ipl/lun)
        zfcp_host_configure $deviceID 1
        zfcp_disk_configure $deviceID $wwpn $slun 1
        biosBootDevice="$dpath/ccw-$deviceID-zfcp-$wwpn:$slun"
    fi
    #======================================
    # setup boot device variable
    #--------------------------------------
    waitForStorageDevice $biosBootDevice
    if [ ! -e $biosBootDevice ];then
        export biosBootDevice="Failed to set disk $deviceID online"
        return 1
    fi
    export biosBootDevice=$(getDiskDevice $biosBootDevice)
    return 0
}
#======================================
# lookupDiskDevices
#--------------------------------------
function lookupDiskDevices {
    # /.../
    # use hwinfo to search for disk device nodes
    # ----
    local IFS=$IFS_ORIG
    local h=/usr/sbin/hwinfo
    local c="Device File:|BIOS id"
    udevPending
    diskDevices=$($h --disk | \
        grep -E "$c" | sed -e"s@(.*)@@" | cut -f2 -d: | tr -d " ")
}
#======================================
# lookupBiosBootDevice
#--------------------------------------
function lookupBiosBootDevice {
    # /.../
    # check for devices which have 0x80 bios flag assigned
    # ----
    local IFS=$IFS_ORIG
    local curd
    local pred
    for curd in $diskDevices;do
        if [ $curd = "0x80" ];then
            bios=$pred
            return
        fi
        pred=$curd
    done
}
#======================================
# searchBIOSBootDevice
#--------------------------------------
function searchBIOSBootDevice {
    # /.../
    # search for the boot device. The edd 0x80 information
    # is used here but not trusted. Trusted is the MBR disk
    # disk label which is compared with the kiwi written
    # mbrid file in /boot/grub/ of the system image
    # If we got a root device set via cmdline this value
    # takes precedence over everything else though
    # ----
    local IFS=$IFS_ORIG
    local file=/boot/mbrid
    local ifix
    local match_count
    local matched
    local curd
    local mbrML
    local mbrMB
    local mbrI
    local try_count=0
    #======================================
    # Check root variable
    #--------------------------------------
    if [ ! -z "$root" ];then
        if ! waitForStorageDevice $root;then
            Echo "Specified root device $root not found. Found devices:"
            hwinfo --disk
            systemException \
                "root device not found... fatal !" \
            "reboot"
        fi
        export biosBootDevice=$(dn $root)
        if [ ! -e /config.partids ];then
            echo "kiwi_RootPart=1" > /config.partids
        fi
        return 0
    fi
    #======================================
    # Read mbrid from initrd
    #--------------------------------------
    if [ ! -e $file ];then
        export biosBootDevice="Failed to find MBR identifier !"
        return 1
    fi
    read mbrI < $file
    #======================================
    # Lookup until found
    #--------------------------------------
    while true;do
        #======================================
        # initialize variables
        #--------------------------------------
        ifix=0
        match_count=0
        try_count=$((try_count + 1))
        #======================================
        # stop after a long time of retry
        #--------------------------------------
        if [ $try_count -eq 15 ];then
            export biosBootDevice="Failed to find boot device !"
            return 1
        fi
        #======================================
        # create device list
        #--------------------------------------
        lookupDiskDevices
        lookupBiosBootDevice
        #======================================
        # Compare ID with MBR entry
        #--------------------------------------
        for curd in $diskDevices;do
            if [ ! -b $curd ];then
                continue
            fi
            mbrML=$(dd if=$curd bs=1 count=4 skip=$((0x1b8)) | \
                hexdump -n4 -e '"0x%08x"')
            mbrMB=$(echo $mbrML | \
                sed 's/^0x\(..\)\(..\)\(..\)\(..\)$/0x\4\3\2\1/')
            if [ "$mbrML" = "$mbrI" ] || [ "$mbrMB" = "$mbrI" ];then
                ifix=1
                matched=$curd
                match_count=$(($match_count + 1))
                if [ "$mbrML" = "$mbrI" ];then
                    export masterBootID=$mbrML
                fi
                if [ "$mbrMB" = "$mbrI" ];then
                    export masterBootID=$mbrMB
                fi
                if [ "$curd" = "$bios" ];then
                    export biosBootDevice=$curd
                    return 0
                fi
            fi
        done
        #======================================
        # Multiple matches are bad
        #--------------------------------------
        if [ $match_count -gt 1 ];then
            export biosBootDevice="multiple devices matches same MBR ID: $mbrI"
            return 2
        fi
        #======================================
        # Found it...
        #--------------------------------------
        if [ $ifix -eq 1 ];then
            export biosBootDevice=$matched
            return 0
        fi
        export biosBootDevice="No devices matches MBR ID: $mbrI !"
        sleep 1
    done
}
#======================================
# searchVolumeGroup
#--------------------------------------
function searchVolumeGroup {
    # /.../
    # search for a volume group named $kiwi_lvmgroup and if it can be
    # found activate it while creating appropriate device nodes:
    # /dev/$kiwi_lvmgroup/LVRoot and/or /dev/$kiwi_lvmgroup/LVComp
    # return zero on success
    # ----
    local IFS=$IFS_ORIG
    local vg_count=0
    local vg_found
    if [ ! "$kiwi_lvm" = "true" ];then
        return 1
    fi
    local rootdevice=$(ddn $imageDiskDevice $kiwi_RootPart)
    probeFileSystem $rootdevice
    if [ "$FSTYPE" = "luks" ];then
        luksOpen $rootdevice
        export haveLuks=yes
    fi
    for i in $(vgs --noheadings -o vg_name 2>/dev/null);do
        vg_found=$(echo $i)
        if [ "$vg_found" = "$kiwi_lvmgroup" ];then
            vg_count=$((vg_count + 1))
        fi
    done
    if [ $vg_count -gt 1 ];then
        Echo "Duplicate VolumeGroup name $kiwi_lvmgroup found !"
        Echo "$vg_count versions of this volume group exists"
        Echo "The volume group name must be unique"
        Echo "Please check your disks and rename/remove the duplicates"
        systemException \
            "VolumeGroup $kiwi_lvmgroup not unique !" \
        "reboot"
    fi
    Echo "Activating $kiwi_lvmgroup volume group..."
    vgchange -a y $kiwi_lvmgroup
}
#======================================
# deactivateVolumeGroup
#--------------------------------------
function deactivateVolumeGroup {
    # /.../
    # as signals/ioctls from earlier operations may
    # not have been processed by the kernel or udev
    # we may require a moment before 'vgchange -a n'
    # return zero on success
    # ----
    local IFS=$IFS_ORIG
    if [ ! "$kiwi_lvm" = "true" ];then
        return 1
    fi
    udevPending
    Echo "Deactivating $kiwi_lvmgroup volume group..."
    vgchange -a n $kiwi_lvmgroup
    udevPending
}
#======================================
# activateVolumeGroup
#--------------------------------------
function activateVolumeGroup {
    # /.../
    # activate volume group if LVM is present
    # ----
    local IFS=$IFS_ORIG
    if [ ! "$kiwi_lvm" = "true" ];then
        return 1
    fi
    udevPending
    Echo "Activating $kiwi_lvmgroup volume group..."
    vgchange -a y $kiwi_lvmgroup
    udevPending
}
#======================================
# activateMDRaid
#--------------------------------------
function activateMDRaid {
    local IFS=$IFS_ORIG
    if [ ! -z "$kiwi_RaidDev" ];then
        udevPending
        Echo "Activating $kiwi_RaidDev mdraid array..."
        mdadm --assemble --scan
        waitForStorageDevice $kiwi_RaidDev
    fi
}
#======================================
# resizeMDRaid
#--------------------------------------
function resizeMDRaid {
    local IFS=$IFS_ORIG
    if [ ! -z "$kiwi_RaidDev" ];then
        udevPending
        Echo "Resizing $kiwi_RaidDev mdraid array..."
        mdadm --grow --size=max $kiwi_RaidDev
    fi
}
#======================================
# resizeLVMPVs
#--------------------------------------
function resizeLVMPVs {
    local IFS=$IFS_ORIG
    local extendID=$1
    local device=$(ddn $imageDiskDevice $extendID)
    if [ ! -z "$kiwi_RaidDev" ];then
        device=$kiwi_RaidDev
    fi
    if [ ! -z "$luksDeviceOpened" ];then
        device=$luksDeviceOpened
    fi
    local unixDevice=$(getDiskDevice $device)
    pvresize $unixDevice
}
#======================================
# deactivateMDRaid
#--------------------------------------
function deactivateMDRaid {
    local IFS=$IFS_ORIG
    if [ ! -z "$kiwi_RaidDev" ] && [ -e $kiwi_RaidDev ];then
        udevPending
        Echo "Deactivating $kiwi_RaidDev mdraid array..."
        mdadm --stop $kiwi_RaidDev
    fi
}
#======================================
# zeroMDRaidSuperBlock
#--------------------------------------
function zeroMDRaidSuperBlock {
    local IFS=$IFS_ORIG
    if [ ! -z "$kiwi_RaidDev" ] && [ -e $kiwi_RaidDev ];then
        local diskDevice=$1
        for i in /dev/md*;do
            test -b $i && mdadm --stop $i &>/dev/null
        done
        mdadm --zero-superblock $diskDevice &>/dev/null
    fi
}
#======================================
# searchSwapSpace
#--------------------------------------
function searchSwapSpace {
    # /.../
    # search for a type=82 swap partition
    # ----
    local IFS=$IFS_ORIG
    if [ ! -z $kiwinoswapsearch ];then
        return
    fi
    local hwapp=/usr/sbin/hwinfo
    local diskdevs=`$hwapp --disk | grep "Device File:" | cut -f2 -d:`
    diskdevs=`echo $diskdevs | sed -e "s@(.*)@@"`
    for diskdev in $diskdevs;do
        for disknr in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15;do
            id=$(partitionID $diskdev $disknr)
            if [ "$id" = "82" ];then
                echo $diskdev$disknr
                return
            fi
        done
    done
}
#======================================
# updateMTAB
#--------------------------------------
function updateMTAB {
    local IFS=$IFS_ORIG
    local prefix=$1
    local umount=0
    if [ ! -e /proc/mounts ];then
        mount -t proc proc /proc
        umount=1
    fi
    if [ -e /proc/self/mounts ];then
        pushd $prefix/etc >/dev/null
        rm -f mtab && ln -s /proc/self/mounts mtab
        popd >/dev/null
    fi
    if [ $umount -eq 1 ];then
        umount /proc
    fi
}
#======================================
# getNicNames
#--------------------------------------
function getNicNames {
    local IFS=$IFS_ORIG
    for nic in $(ip -4 -o link | cut -f2 -d:);do
        if [ ! $nic = 'lo' ];then
            echo $nic
        fi
    done
}
#======================================
# getHWAddress
#--------------------------------------
function getHWAddress {
    local IFS=$IFS_ORIG
    local iface=$1
    ip addr show dev $iface |\
        grep 'link\/ether ' | cut -f6 -d ' '
}
#======================================
# setupNic
#--------------------------------------
function setupNic {
    local IFS=$IFS_ORIG
    local iface=$1
    local address=$2
    local netmask=$3
    ip addr flush dev $iface
    ip addr add $address broadcast $netmask dev $iface
    ip link set dev $iface up
}
#======================================
# probeNetworkCard
#--------------------------------------
function probeNetworkCard {
    # /.../
    # use hwinfo to probe for all network devices. The
    # function will check for the driver which is needed
    # to support the card and returns the information in
    # the networkModule variable
    # ----
    local IFS="%"
    local module=""
    local hwicmd="/usr/sbin/hwinfo"
    for i in \
        `$hwicmd --netcard | grep "Driver [IA]" | 
        sed -es"@modprobe\(.*\)\"@\1%@" | tr -d "\n"`
    do
        if echo $i | grep -q "#0";then
            module=`echo $i | cut -f2 -d"\"" | tr -d " "`
            module=`echo $module | sed -es"@modprobe@@g"`
            IFS=";"
            for m in $module;do
                if ! echo $networkModule | grep -q $m;then
                    if [ ! -z "$networkModule" ];then
                        networkModule="$networkModule:$m"
                    else
                        networkModule=$m
                    fi
                fi
            done
        fi
    done
    networkModule=`echo $networkModule`
}
#======================================
# loadNetworkCard
#--------------------------------------
function loadNetworkCard {
    # /.../
    # load network module found by probeNetworkCard()
    # ----
    local IFS=$IFS_ORIG
    local loaded=0
    probeNetworkCard
    IFS=":" ; for i in $networkModule;do
        if [ ! -z "$i" ];then
            modprobe $i 2>/dev/null
            if [ $? = 0 ];then
                loaded=1
            fi
        fi
    done
}
#======================================
# loadNetworkCardS390
#--------------------------------------
function loadNetworkCardS390 {
    # /.../
    # search and include parameters from a parm file
    # provided on the specified dasd id
    # ----
    local IFS=$IFS_ORIG
    local host=$1
    local skip="/etc/deactivate_s390_network_config_from_dasd"
    local hostdev=/dev/disk/by-path/ccw-${host}
    local parmfile_name=PARM-S11
    if [ ! -z "$kiwi_oemvmcp_parmfile" ];then
        parmfile_name=$kiwi_oemvmcp_parmfile
    fi
    Echo "Trying parm file lookup on DASD id: ${host}"
    #======================================
    # check if we got stopped
    #--------------------------------------
    if [ -e $skip ];then
        Echo "Processing skipped by $skip"
        rm -f $skip
        return 1
    fi
    #======================================
    # check for required tools
    #--------------------------------------
    if [ ! lookup cmsfscat &>/dev/null ];then
        Echo "Can't find cmsfscat program required for loading"
        return 1
    fi
    #======================================
    # check for required kernel support
    #--------------------------------------
    # If loading vmcp fails we assume the support for it has been
    # compiled into the kernel. If this is not the case we will run
    # into an exception on 'vmcp query' which is the intended way
    # to handle the error condition
    modprobe vmcp &>/dev/null
    #======================================
    # bring host online
    #--------------------------------------
    if [ ! -b $hostdev ];then
        dasd_configure ${host} 1 0
        udevPending
        if [ ! -b $hostdev ];then
            Echo "Failed to activate DASD id: ${host}"
            return 1
        fi
    fi
    #======================================
    # load parm file using cmsfscat
    #--------------------------------------
    Echo "Loading configuration file <UID>.${parmfile_name} from ${host}..."
    local parmfile="$(vmcp query userid | cut -d ' ' -f 1).$parmfile_name"
    if ! cmsfscat -d $hostdev -a "$parmfile" > /tmp/"$parmfile";then
        Echo "Can't create /tmp/${parmfile} on DASD id: ${host}"
        return 1
    fi
    #======================================
    # import data into environment
    #--------------------------------------
    includeKernelParametersLowerCase "/tmp/$parmfile"
    #======================================
    # unbind host and cleanup
    #--------------------------------------
    rm -f "/tmp/$parmfile"
    dasd_configure ${host} 0 0
    return 0
}
#======================================
# dhclientImportInfo
#-------------------------------------
function dhclientImportInfo {
    # /.../
    # Import and export the information form the
    # dhclient.lease file into the enviroment.
    # ----
    local IFS=$IFS_ORIG
    if [ ! -n $1 ]; then
        Echo "NULL argument passed to dhclientImportInfo"
        return
    fi
    local lease=/var/lib/dhclient/$1.lease
    export IPADDR=$(
        cat $lease | grep 'fixed-address'|\
        awk '{print $2}' | tr -d ';'
    )
    export NETMASK=$(
        cat $lease | grep 'subnet-mask'|\
        awk '{print $3}' | tr -d ';'
    )
    export GATEWAYS=$(
        cat $lease | grep 'routers ' |\
        awk '{print $3}' |tr -d ';'
    )
    export DOMAIN=$(
        cat $lease | grep 'domain-name' | grep -v 'domain-name-server' |\
        awk '{print $3}'| tr -d ';'
    )
    export DNSSERVERS=$(
        cat $lease | grep 'domain-name-servers'|\
        awk '{print $3}'| tr -d ';' | tr ',' ' '
    )
    export DHCPSIADDR=$(
        cat $lease | grep 'dhcp-server-identifier'|\
        awk '{print $3}'| tr -d ';' | tr ',' ' '
    )
    export DNS=$DNSSERVERS
    export DHCPCHADDR=$(
        ip link show $1| grep link | awk '{print $2}'
    )
}
#======================================
# setupNetworkWicked
#--------------------------------------
function setupNetworkWicked {
    # /.../
    # assign DHCP IP address by using the wicked tool
    # ----
    local IFS=$IFS_ORIG
    local nic_config
    local dhcp_info
    local wicked_dhcp4=/usr/lib/wicked/bin/wickedd-dhcp4
    for try_iface in ${prefer_iface[*]}; do
        # try DHCP_DISCOVER on all prefered interfaces
        if ip link set dev $try_iface up;then
            if [ $try_iface = "lo" ];then
                continue
            fi
            waitForLinkUp $try_iface
            dhcp_info=/var/run/wicked/wicked-${try_iface}.info
            $wicked_dhcp4 --debug all \
                --test --test-output $dhcp_info $try_iface
            if [ $? == 0 ] && [ -s $dhcp_info ];then
                importFile < $dhcp_info
                if setupNic $try_iface $IPADDR $NETMASK;then
                    DHCPCD_STARTED="$DHCPCD_STARTED $try_iface"
                fi
            fi
        fi
    done
    if [ -z "$DHCPCD_STARTED" ];then
        if [ -e "$root" ];then
            Echo "Failed to setup DHCP network interface !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Failed to setup DHCP network interface !" \
            "reboot"
        fi
    fi
    #======================================
    # setup routing for first discovered
    #--------------------------------------
    for try_iface in $DHCPCD_STARTED; do
        dhcp_info=/var/run/wicked/wicked-${try_iface}.info
        if [ -s $dhcp_info ]; then
            export PXE_IFACE=$try_iface
            ip route add default dev $PXE_IFACE
            if [ ! -z "$GATEWAYS" ];then
                # Use first entry as primary gateway
                local gw=$(echo $GATEWAYS | cut -f1 -d " ")
                ip route change default via $gw dev $PXE_IFACE
            fi
            break
        fi
    done
    #======================================
    # fallback to local boot if possible
    #--------------------------------------
    if [ -z "$PXE_IFACE" ];then
        if [ -e "$root" ];then
            Echo "Can't get DHCP reply on any interface !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Can't get DHCP reply on any interface !" \
            "reboot"
        fi
    fi
    #======================================
    # setup selected interface
    #--------------------------------------
    dhcp_info=/var/run/wicked/wicked-${PXE_IFACE}.info
    if [ -s $dhcp_info ]; then
        importFile < /var/run/wicked/wicked-${PXE_IFACE}.info
    fi
}
#======================================
# setupNetworkDHCPCD
#--------------------------------------
function setupNetworkDHCPCD {
    # /.../
    # assign DHCP IP address by using the dhcpcd tool
    # ----
    local IFS=$IFS_ORIG
    if [ $DHCPCD_HAVE_PERSIST -eq 0 ];then
        # /.../
        # older version of dhcpd which doesn't have the
        # options we want to pass
        # ----
        unset opts
    fi
    mkdir -p /var/lib/dhcpcd
    for try_iface in ${dev_list[*]}; do
        # try DHCP_DISCOVER on all interfaces
        dhcpcd $opts -T $try_iface > /var/lib/dhcpcd/dhcpcd-$try_iface.info &
        DHCPCD_STARTED="$DHCPCD_STARTED $try_iface"
    done
    if [ -z "$DHCPCD_STARTED" ];then
        if [ -e "$root" ];then
            Echo "Failed to setup DHCP network interface !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Failed to setup DHCP network interface !" \
            "reboot"
        fi
    fi
    #======================================
    # wait for any preferred interface(s)
    #--------------------------------------
    for j in 1 2 ;do
        for i in 1 2 3 4 5 6 7 8 9 10 11;do
            for try_iface in ${prefer_iface[*]} ; do
                if [ -s /var/lib/dhcpcd/dhcpcd-$try_iface.info ] &&
                    grep -q "^IPADDR=" /var/lib/dhcpcd/dhcpcd-$try_iface.info
                then
                    break 3
                fi
            done
            sleep 2
        done
        # /.../
        # we are behind the dhcpcd timeout 20s so the only thing
        # we can do now is to try again
        # ----
        for try_iface in $DHCPCD_STARTED; do
            dhcpcd $opts -T $try_iface \
                > /var/lib/dhcpcd/dhcpcd-$try_iface.info &
        done
        sleep 2
    done
    #======================================
    # select interface from preferred list
    #--------------------------------------
    for try_iface in ${prefer_iface[*]} $DHCPCD_STARTED; do
        if [ -s /var/lib/dhcpcd/dhcpcd-$try_iface.info ] &&
            grep -q "^IPADDR=" /var/lib/dhcpcd/dhcpcd-$try_iface.info
        then
            export PXE_IFACE=$try_iface
            eval `grep "^IPADDR=" /var/lib/dhcpcd/dhcpcd-$try_iface.info`
            rm /var/lib/dhcpcd/dhcpcd-$try_iface.info
            # continue with the DHCP protocol on the selected interface
            if [ -e /var/run/dhcpcd-$PXE_IFACE.pid ];then
                rm -f /var/run/dhcpcd-$PXE_IFACE.pid
            fi
            if [ $DHCPCD_HAVE_PERSIST -eq 0 ];then
                # /.../
                # older version of dhcpd which doesn't provide
                # an option to request a specific IP address
                # ----
                dhcpcd $opts $PXE_IFACE 2>&1
            else
                dhcpcd $opts -r $IPADDR $PXE_IFACE 2>&1
            fi
            break
        fi
    done
    #======================================
    # fallback to local boot if possible
    #--------------------------------------
    if [ -z "$PXE_IFACE" ];then
        if [ -e "$root" ];then
            Echo "Can't get DHCP reply on any interface !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Can't get DHCP reply on any interface !" \
            "reboot"
        fi
    fi
    #======================================
    # wait for iface to finish negotiation
    #--------------------------------------
    for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20;do
        if [ -s /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info ] &&
            grep -q "^IPADDR=" /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info
        then
            break
        fi
        sleep 2
    done
    #======================================
    # setup selected interface
    #--------------------------------------
    setupNic lo 127.0.0.1/8 255.0.0.0
    if [ -s /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info ] &&
        grep -q "^IPADDR=" /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info; then
        importFile < /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info
    fi
}
#======================================
# setupNetworkDHCLIENT
#--------------------------------------
function setupNetworkDHCLIENT {
    # /.../
    # assign DHCP IP address by using the dhclient tool
    # ----
    local IFS=$IFS_ORIG
    local dhclient_opts=" -4 -1 -q"
    mkdir -p /var/lib/dhclient
    mkdir -p /var/run
    for try_iface in ${dev_list[*]}; do
        # try DHCP_DISCOVER on all interfaces
        dhclient $dhclient_opts \
            -lf /var/lib/dhclient/${try_iface}.lease \
            -pf /var/run/dhclient-${try_iface}.pid ${try_iface}
        DHCPCD_STARTED="$DHCPCD_STARTED $try_iface"
    done
    if [ -z "$DHCPCD_STARTED" ];then
        if [ -e "$root" ];then
            Echo "Failed to setup DHCP network interface !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Failed to setup DHCP network interface !" \
            "reboot"
        fi
    fi
    #======================================
    # wait for any preferred interface(s)
    #--------------------------------------
    for j in 1 2 ;do
        for i in 1 2 3 4 5 6 7 8 9 10 11;do
            for try_iface in ${prefer_iface[*]} ; do
                if [ -f /var/lib/dhclient/${try_iface}.lease ] &&
                    grep -q "fixed-address" /var/lib/dhclient/${try_iface}.lease
                then
                    break 3
                fi
            done
            sleep 2
        done
        # /.../
        # we are behind the dhclient timeout 20s so the only thing
        # we can do now is to try again
        # ----
        for try_iface in $DHCPCD_STARTED; do
            dhclient $dhclient_opts \
                -lf /var/lib/dhclient/${try_iface}.lease \
                -pf /var/run/dhclient-${try_iface}.pid ${try_iface}
        done
        sleep 2
    done
    #======================================
    # select interface from preferred list
    #--------------------------------------
    for try_iface in ${prefer_iface[*]} $DHCPCD_STARTED; do
        if [ -f /var/lib/dhclient/${try_iface}.lease ] &&
            grep -q "fixed-address" /var/lib/dhclient/${try_iface}.lease
        then
            export PXE_IFACE=$try_iface
            export IPADDR=$(
                cat /var/lib/dhclient/${try_iface}.lease |\
                    grep 'fixed-address'| awk  '{print $2}' | tr -d ';'
                )
            break
        fi
    done
    #======================================
    # setup selected interface
    #--------------------------------------
    setupNic lo 127.0.0.1/8 255.0.0.0
    if [ -f /var/lib/dhclient/$PXE_IFACE.lease ] &&
        grep -q "fixed-address" /var/lib/dhclient/$PXE_IFACE.lease; then
        dhclientImportInfo "$PXE_IFACE"
    fi
}
#======================================
# setupNetwork
#--------------------------------------
function setupNetwork {
    # /.../
    # probe for the existing network interface names and
    # hardware addresses. Match the BOOTIF address from PXE
    # to the correct linux interface name. Setup the network
    # interface using a dhcp request. On success the dhcp
    # info file is imported into the current shell environment
    # and the nameserver information is written to
    # /etc/resolv.conf
    # ----
    local IFS=$IFS_ORIG
    #======================================
    # local variable setup
    #--------------------------------------
    local MAC=0
    local DEV=0
    local mac_list=0
    local dev_list=0
    local index=0
    local hwicmd=/usr/sbin/hwinfo
    local opts="--noipv4ll -p"
    local try_iface
    export DHCPCD_STARTED=""
    #======================================
    # detect iface and HWaddr
    #--------------------------------------
    for DEV in $(getNicNames);do
        MAC=$(getHWAddress $DEV)
        mac_list[$index]=$MAC
        dev_list[$index]=$DEV
        index=$((index + 1))
    done
    if [ $index = 0 ];then
        systemException \
            "No network interfaces found" \
        "reboot"
    fi
    #======================================
    # preselect first nic as a start
    #--------------------------------------
    export prefer_iface=${dev_list[0]}
    #======================================
    # continue to be smarter in nic check
    #--------------------------------------
    if [ -z "$BOOTIF" ];then
        # /.../
        # there is no PXE boot interface information. We will use
        # the first interface that responds to dhcp
        # ----
        prefer_iface=${dev_list[*]}
    else
        # /.../
        # evaluate the information from the PXE boot interface
        # if we found the MAC in the list the appropriate interface
        # name is assigned.
        # ----
        index=0
        BOOTIF=$(echo $BOOTIF | cut -f2- -d - | tr "-" ":")
        for i in ${mac_list[*]};do
            list_iface=$(echo $i | tr [:upper:] [:lower:])
            if [ $list_iface = $BOOTIF ];then
                prefer_iface=${dev_list[$index]}
            fi
            index=$((index + 1))
        done
    fi
    #======================================
    # ask for an address
    #--------------------------------------
    if lookup wicked &>/dev/null; then
        setupNetworkWicked
    elif lookup dhcpcd &>/dev/null; then
        setupNetworkDHCPCD
    elif lookup dhclient &>/dev/null; then
        setupNetworkDHCLIENT
    else
        Echo "No supported DHCP client tool found (dhcpcd/dhclient)"
        return 1
    fi
    #======================================
    # check if we got an address
    #--------------------------------------
    if [ -z "$IPADDR" ];then
        if [ -e "$root" ];then
            Echo "Can't assign IP addr via dhcp info: dhcpcd-$PXE_IFACE.info !"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Can't assign IP addr via dhcp info: dhcpcd-$PXE_IFACE.info !" \
            "reboot"
        fi
    fi
    if [ -z "$DOMAIN" ] && [ -n "$DNSDOMAIN" ];then
        export DOMAIN=$DNSDOMAIN
    fi
    echo "search $DOMAIN" > /etc/resolv.conf
    if [ -z "$DNS" ] && [ -n "$DNSSERVERS" ];then
        export DNS=$DNSSERVERS
    fi
    IFS="," ; for i in $DNS;do
        echo "nameserver $i" >> /etc/resolv.conf
    done
    export DHCPCHADDR=$(
        ip link show dev $PXE_IFACE | grep link | awk '{print $2}'
    )
}
#======================================
# releaseNetwork
#--------------------------------------
function releaseNetwork {
    # /.../
    # release network setup by dhcpcd and free the lease
    # Do that only for _non_ network root devices
    # ----
    local IFS=$IFS_ORIG
    if [ -z "$NFSROOT" ] && [ -z "$NBDROOT" ] && [ -z "$AOEROOT" ];then
        if lookup dhcpcd &>/dev/null; then
            #======================================
            # unset dhcp info variables
            #--------------------------------------
            unsetFile < /var/lib/dhcpcd/dhcpcd-$PXE_IFACE.info
            #======================================
            # free the lease and the cache
            #--------------------------------------
            dhcpcd -k $PXE_IFACE
        elif lookup dhclient &>/dev/null; then
            #======================================
            # unset dhclient info variables
            #--------------------------------------
            unset IPADDR
            unset GATEWAYS
            unset DNSSERVERS
            unset NETMASK
            unset DOMAIN
            unset DNSSERVERS
            unset DNS
            unset DHCPCHADDR
            #======================================
            # free the lease and the cache
            #--------------------------------------
            kill -9 $(cat /var/run/dhclient-$PXE_IFACE.pid )
            dhclient -r \
                -lf /var/lib/dhclient/$PXE_IFACE.lease $PXE_IFACE
        fi
        #======================================
        # remove sysconfig state information
        #--------------------------------------
        rm -rf /dev/.sysconfig/network
        #======================================
        # unset host information
        #--------------------------------------
        unset HOSTNAME
    fi
}
#======================================
# setupNetworkInterfaceS390
#--------------------------------------
function setupNetworkInterfaceS390 {
    # /.../
    # bring up the network card according to the parm file
    # parameters and create the correspondent udev rules
    # needs includeKernelParametersLowerCase to be run
    # because parm file parameters are case insensitive
    # ----
    local IFS=$IFS_ORIG
    case "$instnetdev" in
        "osa"|"hsi")
            local qeth_cmd="/sbin/qeth_configure"
            if [ "$layer2" = "1" ];then
                qeth_cmd="$qeth_cmd -l"
            fi
            if [ -n "$portname" ];then
                qeth_cmd="$qeth_cmd -p $portname"
            fi
            if [ -n "$portno" ];then
                qeth_cmd="$qeth_cmd -n $portno"
            fi
            qeth_cmd="$qeth_cmd $readchannel $writechannel"
            if [ -n "$datachannel" ];then
                qeth_cmd="$qeth_cmd $datachannel"
            fi
            eval $qeth_cmd 1
            ;;
        "ctc")
            /sbin/ctc_configure $readchannel $writechannel 1 $ctcprotocol
            ;;
        "iucv")
            /sbin/iucv_configure $iucvpeer 1
            ;;
        *)
            if [ -e "$root" ];then
                Echo "Unknown s390 network type: $instnetdev"
                Echo "Try fallback to local boot on: $root"
                LOCAL_BOOT=yes
                return
            else
                systemException \
                    "Unknown s390 network type: $instnetdev" \
                "reboot"
            fi
            ;;
    esac
    if [ ! $? = 0 ];then
        if [ -e "$root" ];then
            Echo "Failed to bring up the network: $instnetdev"
            Echo "Try fallback to local boot on: $root"
            LOCAL_BOOT=yes
            return
        else
            systemException \
                "Failed to bring up the network: $instnetdev" \
            "reboot"
        fi
    fi
    udevPending
}
#======================================
# convertCIDRToNetmask
#--------------------------------------
function convertCIDRToNetmask {
    # /.../
    # convert the CIDR part to a useable netmask
    # ----
    local IFS=$IFS_ORIG
    local cidr=$1
    local count=0
    for count in `seq 1 4`;do
        if [ $((cidr / 8)) -gt 0 ];then
            echo -n 255
        else
            local remainder=$((cidr % 8))
            if [ $remainder -gt 0 ];then
                echo -n $(( value = 256 - (256 >> remainder)))
            else
                echo -n 0
            fi
        fi
        cidr=$((cidr - 8))
        if [ $count -lt 4 ];then
            echo -n .
        fi
    done
    echo
}
#======================================
# setupNetworkStatic
#--------------------------------------
function setupNetworkStatic {
    # /.../
    # configure static network either bring it up manually
    # or save the configuration depending on 'up' parameter
    # ----
    local IFS=$IFS_ORIG
    local up=$1
    if [[ $hostip =~ / ]];then
        #======================================
        # convert CIDR to netmask
        #--------------------------------------
        netmask=$(convertCIDRToNetmask $(echo $hostip | cut -f2 -d/))
    fi
    if [ "$up" = "1" ];then
        #======================================
        # activate network
        #--------------------------------------
        # Please note: It is assumed the last interface in the list is the
        # one which should receive the interface config. While the loopback
        # interface is skipped this could still result in an unexpected
        # behavior.
        local iface=$(
            cat /proc/net/dev|grep -v lo:|tail -n1|cut -d':' -f1|sed 's/ //g'
        )
        if ! setupNic $iface $hostip $netmask;then
            if [ -e "$root" ];then
                Echo "Failed to set up the network: $iface"
                Echo "Try fallback to local boot on: $root"
                LOCAL_BOOT=yes
                return
            else
                systemException \
                    "Failed to set up the network: $iface" \
                "reboot"
            fi
        fi
        export iface_static=$iface
    elif [ ! -z $iface_static ];then
        #======================================
        # write network setup
        #--------------------------------------
        local netFile="/etc/sysconfig/network/ifcfg-$iface_static"
        echo "BOOTPROTO='static'" > $netFile
        echo "STARTMODE='auto'" >> $netFile
        echo "IPADDR='$hostip'" >> $netFile
        echo "NETMASK='$netmask'" >> $netFile
        if [ -n "$broadcast" ];then
            echo "BROADCAST='$broadcast'" >> $netFile
        fi
        if [ -n "$pointopoint" ];then
            echo "REMOTE_IPADDR='$pointopoint'" >> $netFile
        fi
    fi
    setupDefaultGateway $up
    setupDNS
}
#======================================
# setupDefaultGateway
#--------------------------------------
function setupDefaultGateway {
    # /.../
    # setup default gateway. either set the route or save
    # the configuration depending on 'up' parameter
    # ----
    local IFS=$IFS_ORIG
    local up=$1
    if [ "$up" == "1" ];then
        #======================================
        # activate GW route
        #--------------------------------------
        ip route add default via $gateway
    else
        #======================================
        # write GW configuration
        #--------------------------------------
        echo "default  $gateway - -" > "/etc/sysconfig/network/routes"
    fi
}
#======================================
# setupDNS
#--------------------------------------
function setupDNS {
    # /.../
    # setup DNS. write data to resolv.conf
    # ----
    local IFS=$IFS_ORIG
    local file="/etc/resolv.conf"
    if [ -n "$domain" ];then
        export DOMAIN=$domain
        local line="search $domain"
        if ! grep -q $line $file;then
            echo "$line" >> "$file"
        fi
    fi
    if [ -n "$nameserver" ];then
        export DNS=$nameserver
        IFS="," ; for i in $nameserver;do
            local line="nameserver $i"
            if ! grep -q $line $file;then
                echo "$line" >> "$file"
            fi
        done
    fi
}
#======================================
# fetchImageMD5
#--------------------------------------
function fetchImageMD5 {
    # /.../
    # download image.md5 file either from the network
    # or from a local cache directory if specified by
    # KIWI_LOCAL_CACHE_DIR.
    # ----
    local IFS=$IFS_ORIG
    local imageMD5s="image/$1-$2.md5"
    local imageServer=$3
    local imageBlkSize=$4
    local error=0
    [ -z "$imageServer" ]  && imageServer=$SERVER
    [ -z "$imageBlkSize" ] && imageBlkSize=8192
    #======================================
    # Check for MD5 in the local cache
    #--------------------------------------
    if [ -n "$KIWI_LOCAL_CACHE_DIR" ];then
        local cached_md5="$KIWI_LOCAL_CACHE_DIR/$imageMD5s"
        if [ -f "$cached_md5" ];then
            read sum_local blocks blocksize zblocks zblocksize < "$cached_md5"
        fi
    fi
    #======================================
    # Download latest MD5 from the network
    #--------------------------------------
    fetchFile $imageMD5s /etc/image.md5 uncompressed $imageServer
    #======================================
    # Check results if download failed
    #--------------------------------------
    if test $loadCode != 0 || ! loadOK "$loadStatus"; then
        Echo "Download of $imageMD5s failed: $loadStatus"
        if [ -z "$sum_local" ]; then
            Echo "Fatal: No cache copy available"
            error=1
        else
            Echo "Using cache copy: $KIWI_LOCAL_CACHE_DIR/$imageMD5s"
            cp "$KIWI_LOCAL_CACHE_DIR/$imageMD5s" /etc/image.md5
            error=0
        fi
    fi
    #======================================
    # Check error state
    #--------------------------------------
    # failed MD5 download and no cache copy is fatal
    if [ $error -eq 1 ];then
        systemException \
            "Failed to provide image MD5 data" \
        "reboot"
    fi
    #======================================
    # Read in provided MD5 data
    #--------------------------------------
    read sum1 blocks blocksize zblocks zblocksize < /etc/image.md5
}

#======================================
# updateNeeded
#--------------------------------------
function updateNeeded {
    # /.../
    # check the contents of the IMAGE key and compare the
    # image version file as well as the md5 sum of the installed
    # and the available image on the tftp server
    # ----
    #======================================
    # Local variables
    #--------------------------------------
    local IFS=$IFS_ORIG
    local count=0
    local sum2
    local installed
    local field
    local atversion
    local versionFile
    local imageName
    local imageVersion
    local imageServer
    local imageBlkSize
    local imageZipped
    local prefix=/mnt
    #======================================
    # Global variables
    #--------------------------------------
    SYSTEM_INTEGRITY=""
    SYSTEM_MD5STATUS=""
    #======================================
    # Check system update status via md5
    #--------------------------------------
    IFS="," ; for i in $IMAGE;do
        field=0
        IFS=";" ; for n in $i;do
        case $field in
            0) field=1 ;;
            1) imageName=$n   ; field=2 ;;
            2) imageVersion=$n; field=3 ;;
            3) imageServer=$n ; field=4 ;;
            4) imageBlkSize=$n; field=5 ;;
            5) imageZipped=$n ;
        esac
        done
        atversion="$imageName-$imageVersion"
        versionFile="$prefix/etc/ImageVersion-$atversion"
        IFS=" "
        if [ -f "$versionFile" ];then
            read installed sum2 < $versionFile
        fi
        fetchImageMD5 \
            "$imageName" "$imageVersion"   \
            "$imageServer" "$imageBlkSize"
        if [ ! -z "$sum1" ];then
            SYSTEM_MD5STATUS="$SYSTEM_MD5STATUS:$sum1"
        else
            SYSTEM_MD5STATUS="$SYSTEM_MD5STATUS:none"
        fi
        if [ ! -z "$1" ];then
            continue
        fi
        if test "$count" = 1;then
        if test "$SYSTEM_INTEGRITY" = ":clean";then
            Echo "Main OS image update needed"
            Echo -b "Forcing download for multi image session"
            RELOAD_IMAGE="yes"
        fi
        fi
        count=$(($count + 1))
        Echo "Checking update status for image: $imageName"
        if test ! -z $RELOAD_IMAGE;then
            Echo -b "Update forced via RELOAD_IMAGE..."
            Echo -b "Update status: Clean"
            SYSTEM_INTEGRITY="$SYSTEM_INTEGRITY:clean"
            continue
        fi
        if test ! -f $versionFile;then
            Echo -b "Update forced: /etc/ImageVersion-$atversion not found"
            Echo -b "Update status: Clean"
            SYSTEM_INTEGRITY="$SYSTEM_INTEGRITY:clean"
            RELOAD_IMAGE="yes"
            continue
        fi
        Echo -b "Current: $atversion Installed: $installed"
        if test "$atversion" = "$installed";then
            if test "$sum1" = "$sum2";then
                Echo -b "Update status: Fine"
                SYSTEM_INTEGRITY="$SYSTEM_INTEGRITY:fine"
                continue
            fi
            Echo -b "Image Update for image [ $imageName ] needed"
            Echo -b "Image version equals but md5 checksum failed"
            Echo -b "This means the contents of the new image differ"
            RELOAD_IMAGE="yes"
        else
            Echo -b "Image Update for image [ $imageName ] needed"
            Echo -b "Name and/or image version differ"
            RELOAD_IMAGE="yes"
        fi
        Echo -b "Update status: Clean"
        SYSTEM_INTEGRITY="$SYSTEM_INTEGRITY:clean"
    done
    SYSTEM_INTEGRITY=`echo $SYSTEM_INTEGRITY | cut -f2- -d:`
    SYSTEM_MD5STATUS=`echo $SYSTEM_MD5STATUS | cut -f2- -d:`
}
#======================================
# cleanSweep
#--------------------------------------
function cleanSweep {
    # /.../
    # zero out a the given disk device
    # ----
    local IFS=$IFS_ORIG
    local diskDevice=$1
    dd if=/dev/zero of=$diskDevice bs=32M >/dev/null
}
#======================================
# fdasdGetPartitionID
#--------------------------------------
function fdasdGetPartitionID {
    local IFS=$IFS_ORIG
    local device=$1
    local partid=$2
    local count=1
    for i in $(fdasd -s -p $device | grep -E '^[ ]+\/' |\
        awk -v OFS=":" '$1=$1' | cut -f7 -d:)
    do
        if [ $count -eq $partid ];then
            if [ $i = "native" ];then
                echo 83
            elif [ $i = "swap" ];then
                echo 82
            else
                # /.../
                # don't know this partition information
                # assume it's a linux partition
                # ----
                echo 83
            fi
            return
        fi
        count=$((count + 1))
    done
}
#======================================
# partedGetPartitionID
#--------------------------------------
function partedGetPartitionID {
    # /.../
    # prints the partition ID for the given device and number
    # In case of a GPT map to the GUID code from the sgdisk
    # utility. If sgdisk is not available map to the kiwi
    # fdisk compatible hex id's which uses ee for any kind
    # of unknown GPT partition entry
    # ----
    local IFS=$IFS_ORIG
    local parted=$(parted -m -s $1 print | grep -v Warning:)
    local diskhd=$(echo $parted | head -n 3 | tail -n 2 | head -n 1)
    local plabel=$(echo $diskhd | cut -f6 -d:)
    if [ -z "$plabel" ];then
        # can't find a partition label for this disk
        echo xx
        return
    fi
    if [[ $plabel =~ gpt ]];then
        plabel=gpt
    fi
    if [ ! $plabel = "gpt" ];then
        parted -m -s $1 print | grep ^$2: | cut -f2 -d= |\
            sed -e 's@[,; ]@@g' | tr -d 0
    else
        local name=$(parted -m -s $1 print | grep ^$2: | cut -f6 -d:)
        if lookup sgdisk &>/dev/null;then
            # map to short gdisk code
            echo $(sgdisk -p $1 | grep -E "^   $2") | cut -f6 -d ' '
        elif [ "$name" = "lxroot" ];then
            # map lxroot to MBR type 83 (linux)
            echo 83
        elif [ "$name" = "lxswap" ];then
            # map lxswap to MBR type 82 (linux swap)
            echo 82
        elif [ "$name" = "lxlvm" ];then
            # map lxlvm to MBR type 8e (linux LVM)
            echo 8e
        elif [ "$name" = "UEFI" ];then
            # map UEFI to MBR type 6 (fat 16)
            echo 6
        elif [ "$name" = "legacy" ];then
            # map bios grub legacy partition to MBR type ef (EFI)
            echo ef
        else
            # map anything else to ee (GPT)
            echo ee
        fi
    fi
}
#======================================
# partitionID
#--------------------------------------
function partitionID {
    local IFS=$IFS_ORIG
    local diskDevice=$1
    local diskNumber=$2
    if [ $PARTITIONER = "fdasd" ];then
        fdasdGetPartitionID $diskDevice $diskNumber
    else
        partedGetPartitionID $diskDevice $diskNumber
    fi
}
#======================================
# partitionSize
#--------------------------------------
function partitionSize {
    local IFS=$IFS_ORIG
    local diskDevice=$1
    local psizeBytes
    local psizeKBytes
    if [ -z "$diskDevice" ] || [ ! -e "$diskDevice" ];then
        echo 1 ; return 1
    fi
    psizeBytes=$(blockdev --getsize64 $diskDevice)
    psizeKBytes=$((psizeBytes / 1024))
    echo $psizeKBytes
}
#======================================
# kernelList
#--------------------------------------
function kernelList {
    # /.../
    # check for all installed kernels whether there are valid
    # links to the initrd and kernel files. The function will
    # save the valid linknames in the variable KERNEL_LIST
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    local kcount=1
    local kname=""
    local kernel=""
    local initrd=""
    local kpair=""
    local krunning=`uname -r`
    KERNEL_LIST=""
    KERNEL_NAME=""
    KERNEL_PAIR=""
    #======================================
    # search running kernel first
    #--------------------------------------
    if [ -d $prefix/lib/modules/$krunning ];then
        for name in vmlinux vmlinuz image uImage;do
            if [ -f $prefix/boot/$name-$krunning ];then
                kernel=$name-$krunning
                initrd=initrd-$krunning
                break
            fi
        done
        if [ ! -z "$kernel" ];then
            KERNEL_PAIR=$kernel:$initrd
            KERNEL_NAME[$kcount]=$krunning
            KERNEL_LIST=$KERNEL_PAIR
            kcount=$((kcount+1))
        fi
    fi
    #======================================
    # search for other kernels
    #--------------------------------------
    for i in $prefix/lib/modules/*;do
        if [ ! -d $i ];then
            continue
        fi
        unset kernel
        unset initrd
        kname=$(basename "$i")
        if [ "$kname" = $krunning ];then
            continue
        fi
        for name in vmlinux vmlinuz image uImage;do
            for k in $prefix/boot/$name-${i##*/}; do
                if [ -f $k ];then
                    kernel=${k##*/}
                    initrd=initrd-${i##*/}
                    break 2
                fi
            done
        done
        if [ ! -z "$kernel" ];then
            kpair=$kernel:$initrd
            KERNEL_NAME[$kcount]=$kname
            KERNEL_LIST=$KERNEL_LIST,$kpair
            kcount=$((kcount+1))
        fi
    done
    #======================================
    # what if no kernel was found...
    #--------------------------------------
    if [ -z "$KERNEL_LIST" ];then
        # /.../
        # the system image doesn't provide the kernel and initrd but
        # if there is a downloaded kernel and initrd from the KIWI_INITRD
        # setup. the kernelList function won't find initrds that gets
        # downloaded over tftp so make sure the vmlinu[zx]/initrd combo
        # gets added as well as the linux.vmx/initrd.vmx combo
        # ----
        if [ -e $prefix/boot/vmlinuz ];then
            KERNEL_LIST="vmlinuz:initrd"
            KERNEL_NAME[1]=vmlinuz
        fi
        if [ -e $prefix/boot/vmlinux ];then
            KERNEL_LIST="vmlinux:initrd"
            KERNEL_NAME[1]=vmlinux
        fi
        if [ -e $prefix/boot/linux.vmx ];then
            KERNEL_LIST="vmlinux:initrd"
            KERNEL_NAME[1]="vmlinux"
        fi
    fi
    KERNEL_LIST=$(echo $KERNEL_LIST | sed -e s@^,@@)
    export KERNEL_LIST
    export KERNEL_NAME
    export KERNEL_PAIR
}
#======================================
# validateSize
#--------------------------------------
function validateSize {
    # /.../
    # check if the image fits into the requested partition.
    # An information about the sizes is printed out
    # ----
    local IFS=$IFS_ORIG
    haveBytes=$(partitionSize $imageDevice)
    haveBytes=$((haveBytes * 1024))
    haveMByte=$((haveBytes / 1048576))
    needBytes=$((blocks * blocksize))
    needMByte=$((needBytes / 1048576))
    Echo "Have size: $imageDevice -> $haveBytes Bytes [ $haveMByte MB ]"
    Echo "Need size: $needBytes Bytes [ $needMByte MB ]"
    if test $haveBytes -gt $needBytes;then
        return 0
    fi
    return 1
}
#======================================
# validateBlockSize
#--------------------------------------
function validateBlockSize {
    # /.../
    # check the block size value. atftp limits to a maximum of
    # 65535 blocks, so the block size must be checked according
    # to the size of the image. The block size itself is also
    # limited to 65464 bytes
    # ----
    local IFS=$IFS_ORIG
    local blkTest
    local nBlk
    if [ -z "$zblocks" ] && [ -z "$blocks" ];then
        # md5 file not yet read in... skip
        return
    fi
    if [ ! -z "$zblocks" ];then
        isize=$((zblocks * zblocksize))
    else
        isize=$((blocks * blocksize))
    fi
    local IFS=' '
    testBlkSizes="32768 61440 65464"
    if [ "$imageBlkSize" -gt 0 ]; then
        testBlkSizes="$imageBlkSize $testBlkSizes"
    fi
    for blkTest in $testBlkSizes ; do
        nBlk=$((isize / blkTest))
        if [ $nBlk -lt 65535 ] ; then
            imageBlkSize=$blkTest
            return
        fi
    done
    systemException \
        "Maximum blocksize for atftp protocol exceeded" \
    "reboot"
}
#======================================
# loadOK
#--------------------------------------
function loadOK {
    # /.../
    # check the output of the atftp command, unfortunately
    # there is no useful return code to check so we have to
    # check the output of the command
    # ----
    local IFS=$IFS_ORIG
    for i in "File not found" "aborting" "no option named" "unknown host" ; do
        if echo "$1" | grep -q  "$i" ; then
            return 1
        fi
    done
    return 0
}
#======================================
# includeKernelParameters
#--------------------------------------
function includeKernelParameters {
    # /.../
    # include the parameters from /proc/cmdline into
    # the current shell environment
    # ----
    local IFS=$IFS_ORIG
    local file=$1
    local translate=$2
    if [ -z "$file" ];then
        file=/proc/cmdline
    fi
    for i in $(cat $file);do
        if ! echo $i | grep -q "=";then
            continue
        fi
        kernelKey=`echo $i | cut -f1 -d=`
        #======================================
        # convert parameters to lowercase if required
        #--------------------------------------
        if [ "$translate" = "lowercase" ];then
            kernelKey=`echo $kernelKey | tr [:upper:] [:lower:]`
        fi
        kernelVal=`echo $i | cut -f2 -d=`
        eval export $kernelKey=$kernelVal
    done
    if [ ! -z "$kiwikernelmodule" ];then
        kiwikernelmodule=`echo $kiwikernelmodule | tr , " "`
    fi
    if [ ! -z "$kiwibrokenmodule" ];then
        kiwibrokenmodule=`echo $kiwibrokenmodule | tr , " "`
    fi
    if \
        [ ! -z "$kiwisplitroot_size" ]            && \
        [[ $kiwisplitroot_size = *[[:digit:]]* ]] && \
        [ $kiwisplitroot_size -gt $splitroot_size ]
    then
        splitroot_size=$kiwisplitroot_size
    fi
    if [ ! -z "$ramdisk_size" ];then
        local modfile=/etc/modprobe.d/99-local.conf
        if [ ! -f $modfile ];then
            modfile=/etc/modprobe.conf.local
        fi
        if [ -f $modfile ];then
            if grep -q rd_size $modfile;then
                sed -i -e s"@rd_size=.*@rd_size=$ramdisk_size@" $modfile
            else
                echo "options brd rd_size=$ramdisk_size" >> $modfile
            fi
        fi
    fi
    if [ ! -z "$lang" ];then
        # lang set on the commandline, e.g by the boot theme
        export DIALOG_LANG=$lang
    elif [ ! -z "$kiwi_language" ];then
        # lang set from the XML data, first item is the primary language
        export DIALOG_LANG=$(echo $kiwi_language | cut -f1 -d,)
    fi
}
#======================================
# includeKernelParametersLowerCase
#--------------------------------------
function includeKernelParametersLowerCase {
    includeKernelParameters "$1" "lowercase"
}
#======================================
# umountSystem
#--------------------------------------
function umountSystem {
    local IFS=$IFS_ORIG
    local retval=0
    local mountList="/mnt /read-only /read-write"
    #======================================
    # umount boot device
    #--------------------------------------
    if [ ! -z "$imageBootDevice" ];then
        umount $imageBootDevice 1>&2
    fi
    #======================================
    # umount mounted mountList paths
    #--------------------------------------
    for mpath in $(cat /proc/mounts | cut -f2 -d " ");do
        for umount in $mountList;do
            if [ "$mpath" = "$umount" ];then
                if ! umount $mpath >/dev/null;then
                if ! umount -l $mpath >/dev/null;then
                    retval=1
                fi
                fi
            fi
        done
    done
    #======================================
    # remove mount points
    #--------------------------------------
    for dir in "/read-only" "/read-write" "/xino";do
        test -d $dir && rmdir $dir 1>&2
    done
    return $retval
}
#======================================
# isFSTypeReadOnly
#--------------------------------------
function isFSTypeReadOnly {
    local IFS=$IFS_ORIG
    if [ "$FSTYPE" = "squashfs" ];then
        export unionFST=overlay
        return 0
    fi
    if [ "$FSTYPE" = "clicfs" ];then
        export unionFST=clicfs
        return 0
    fi
    return 1
}
#======================================
# kiwiMount
#--------------------------------------
function kiwiMount {
    local IFS=$IFS_ORIG
    local src=$1
    local dst=$2
    local opt=$3
    local lop=$4
    #======================================
    # load not autoloadable fs modules
    #--------------------------------------
    modprobe squashfs &>/dev/null
    #======================================
    # store old FSTYPE value
    #--------------------------------------
    if [ ! -z "$FSTYPE" ];then
        FSTYPE_SAVE=$FSTYPE
    fi
    #======================================
    # decide for a mount method
    #--------------------------------------
    if [ ! -z "$lop" ];then
        src=$(loop_setup $lop)
        if [ ! -e $src ]; then
            return 1
        fi
        # /.../
        # for iso images the root device name is set via
        # config.isoclient. But in case of a filename the
        # root device must be loop mounted and the loop
        # setup creates the root device which is stored
        # in imageDevice for the isoboot code
        # ----
        imageDevice=$src
    fi
    #======================================
    # probe filesystem
    #--------------------------------------
    if [ ! "$FSTYPE" = "nfs" ];then
        probeFileSystem $src
    fi
    if [ -z "$FSTYPE" ] || [ "$FSTYPE" = "unknown" ];then
        FSTYPE="auto"
    fi
    if [ "$FSTYPE" = "zfs" ];then
        if [ -b $src ];then
            if ! zpool import -N kiwipool >/dev/null;then
                return 1
            fi
        else
            local basedir=$(dirname $src)
            if ! zpool import -N -d $basedir kiwipool;then
                return 1
            fi
        fi
        zfs set mountpoint=$dst kiwipool/ROOT/system-1 && zfs mount -a
        if [ ! $? = 0 ];then
            return 1
        fi
    else
        if ! mount -t $FSTYPE $opt $src $dst >/dev/null;then
            return 1
        fi
    fi
    if [ ! -z "$FSTYPE_SAVE" ];then
        FSTYPE=$FSTYPE_SAVE
    fi
    return 0
}
#======================================
# setupReadWrite
#--------------------------------------
function setupReadWrite {
    # /.../
    # check/create read-write filesystem used for
    # overlay data
    # ----
    local IFS=$IFS_ORIG
    local rwDir=/read-write
    local rwDevice=`echo $UNIONFS_CONFIG | cut -d , -f 1`
    mkdir -p $rwDir
    if [ $LOCAL_BOOT = "no" ] && [ $systemIntegrity = "clean" ];then
        if [ "$RELOAD_IMAGE" = "yes" ] || \
            ! mount -o ro $rwDevice $rwDir &>/dev/null
        then
            #======================================
            # store old FSTYPE value
            #--------------------------------------
            if [ ! -z "$FSTYPE" ];then
                FSTYPE_SAVE=$FSTYPE
            fi
            #======================================
            # probe filesystem
            #--------------------------------------
            probeFileSystem $rwDevice
            if [ ! "$FSTYPE" = "unknown" ];then
                Echo "Checking filesystem for RW data on $rwDevice..."
                e2fsck -p $rwDevice
            fi
            #======================================
            # restore FSTYPE
            #--------------------------------------
            if [ ! -z "$FSTYPE_SAVE" ];then
                FSTYPE=$FSTYPE_SAVE
            fi
            if [ "$RELOAD_IMAGE" = "yes" ] || \
                ! mount -o ro $rwDevice $rwDir &>/dev/null
            then
                Echo "Creating filesystem for RW data on $rwDevice..."
                if ! mkfs.ext3 -F $rwDevice >/dev/null;then
                    Echo "Failed to create ext3 filesystem"
                    return 1
                fi
                e2fsck -p $rwDevice >/dev/null
            fi
        else
            umount $rwDevice
        fi
    fi
    return 0
}
#======================================
# mountSystemSeedBtrFS
#--------------------------------------
function mountSystemSeedBtrFS {
    local IFS=$IFS_ORIG
    local loopf=$1
    local rwDevice=`echo $UNIONFS_CONFIG | cut -d , -f 1`
    local roDevice=`echo $UNIONFS_CONFIG | cut -d , -f 2`
    local prefix=/mnt
    #======================================
    # check read/only device location
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        roDevice="$imageRootDevice"
    fi
    #======================================
    # check read/write device location
    #--------------------------------------
    if [ ! -e $rwDevice ];then
        rwDevice=/dev/ram1
    fi
    #======================================
    # mount/check btrfs file
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        #======================================
        # btrfs exported via NFS
        #--------------------------------------
        if ! kiwiMount "$roDevice" "$prefix" "" $loopf;then
            Echo "Failed to mount NFS filesystem"
            return 1
        fi
    else
        #======================================
        # mount btrfs container
        #--------------------------------------
        if [ -z "$loopf" ];then
            loopf=$roDevice
        fi
        if ! mount -o loop,$kiwi_fsmountoptions $loopf $prefix; then
            Echo "Failed to mount btrfs filesystem"
            return 1
        fi
    fi
    #======================================
    # add seed device
    #--------------------------------------
    if ! btrfs device add $rwDevice $prefix; then
        Echo "Failed to attach btrfs seed device"
        return 1
    fi
    if ! mount -o remount,rw $prefix; then
        Echo "Failed to remount read-write"
        return 1
    fi
    return 0
}
#======================================
# mountSystemUnionFS
#--------------------------------------
function mountSystemUnionFS {
    local IFS=$IFS_ORIG
    local loopf=$1
    local roDir=/read-only
    local rwDir=/read-write
    local rwDevice=`echo $UNIONFS_CONFIG | cut -d , -f 1`
    local roDevice=`echo $UNIONFS_CONFIG | cut -d , -f 2`
    local unionFST=`echo $UNIONFS_CONFIG | cut -d , -f 3`
    local prefix=/mnt
    #======================================
    # load fuse module
    #--------------------------------------
    modprobe fuse &>/dev/null
    #======================================
    # create overlay mount points
    #--------------------------------------
    mkdir -p $roDir
    mkdir -p $rwDir
    #======================================
    # check read/only device location
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        roDevice="$imageRootDevice"
    fi
    #======================================
    # mount read only device
    #--------------------------------------
    if ! kiwiMount "$roDevice" "$roDir" "" $loopf;then
        Echo "Failed to mount read only filesystem"
        return 1
    fi
    #======================================
    # check read/write device location
    #--------------------------------------
    if [ ! -z "$kiwi_ramonly" ];then
        rwDevice=tmpfs
    fi
    if [ "$rwDevice" = "tmpfs" ];then
        #======================================
        # write into tmpfs
        #--------------------------------------
        if ! mount -t tmpfs tmpfs $rwDir >/dev/null;then
            Echo "Failed to mount tmpfs read/write filesystem"
            return 1
        fi
    else
        #======================================
        # write to another device
        #--------------------------------------
        if [ "$roDevice" = "nfs" ];then
            rwDevice="-o nolock,rw $nfsRootServer:$rwDevice"
        fi
        if [ ! "$roDevice" = "nfs" ] && ! setupReadWrite; then
            return 1
        fi
        if ! kiwiMount "$rwDevice" "$rwDir";then
            Echo "Failed to mount read/write filesystem"
            return 1
        fi
    fi
    #======================================
    # overlay mount the locations
    #--------------------------------------
    if [ "$unionFST" = "overlay" ];then
        #======================================
        # setup overlayfs mount
        #--------------------------------------
        local opts="rw,lowerdir=$roDir,upperdir=$rwDir"
        if ! mount -t overlayfs -o $opts overlayfs $prefix;then
            # overlayfs in version >= v22 behaves differently
            # + renamed from overlayfs to overlay
            # + requires a workdir to become mounted
            # + requires workdir and upperdir to reside under the same mount
            # + requires workdir and upperdir to be in separate subdirs
            mkdir -p $rwDir/work
            mkdir -p $rwDir/rw
            opts="rw,lowerdir=$roDir,upperdir=$rwDir/rw,workdir=$rwDir/work"
            if ! mount -t overlay -o $opts overlay $prefix;then
                Echo "Failed to mount root via overlayfs"
                return 1
            fi
        fi
    elif [ "$unionFST" = "unionfs" ];then
        #======================================
        # setup fuse union mount
        #--------------------------------------
        local opts="cow,max_files=65000,allow_other,use_ino,suid,dev,nonempty"
        if ! unionfs -o $opts $rwDir=RW:$roDir=RO $prefix;then
            Echo "Failed to mount root via unionfs"
            return 1
        fi
    fi
    export haveUnionFS=yes
    return 0
}
#======================================
# mountSystemClicFS
#--------------------------------------
function mountSystemClicFS {
    local IFS=$IFS_ORIG
    local loopf=$1
    local roDir=/read-only
    local rwDevice=`echo $UNIONFS_CONFIG | cut -d , -f 1`
    local roDevice=`echo $UNIONFS_CONFIG | cut -d , -f 2`
    local clic_cmd=clicfs
    local resetReadWrite=0
    local ramOnly=0
    local haveBytes
    local haveKByte
    local haveMByte
    local wantCowFS
    local size
    local prefix=/mnt
    #======================================
    # load fuse module
    #--------------------------------------
    modprobe fuse &>/dev/null
    #======================================
    # create read only mount point
    #--------------------------------------
    mkdir -p $roDir
    #======================================
    # check read/only device location
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        roDevice="$imageRootDevice"
    fi
    #======================================  
    # check kernel command line for log file  
    #--------------------------------------  
    if [ -n "$cliclog" ]; then  
        clic_cmd="$clic_cmd -l $cliclog"  
    fi  
    #======================================
    # check read/write device location
    #--------------------------------------
    if [ ! -z "$kiwi_ramonly" ];then
        ramOnly=1
    elif [ ! -e $rwDevice ];then
        ramOnly=1
    elif getDiskDevice $rwDevice | grep -q ram;then
        ramOnly=1
    fi
    if [ $ramOnly = 1 ];then
        haveKByte=`cat /proc/meminfo | grep MemFree | cut -f2 -d:| cut -f1 -dk`
        haveMByte=$((haveKByte / 1024))
        haveMByte=$((haveMByte * 7 / 10))
        clic_cmd="$clic_cmd -m $haveMByte"
    else
        haveBytes=$(blockdev --getsize64 $rwDevice)
        haveMByte=$((haveBytes / 1024 / 1024))
        wantCowFS=0
        if \
            [ "$kiwi_hybrid" = "true" ] && \
            [ "$kiwi_hybridpersistent" = "true" ]
        then
            # write into a cow file on a filesystem, for hybrid iso's
            wantCowFS=1
        fi
        if [ $wantCowFS = 1 ];then
            # write into a cow file on a filesystem
            mkdir -p $HYBRID_PERSISTENT_DIR
            if [ $LOCAL_BOOT = "no" ] && [ $systemIntegrity = "clean" ];then
                resetReadWrite=1
            elif ! mount $rwDevice $HYBRID_PERSISTENT_DIR;then
                resetReadWrite=1
            elif [ ! -z "$wipecow" ];then
                resetReadWrite=1
            fi
            if [ $resetReadWrite = 1 ];then
                if ! setupReadWrite; then
                    Echo "Failed to setup read-write filesystem"
                    return 1
                fi
                if ! mount $rwDevice $HYBRID_PERSISTENT_DIR;then
                    Echo "Failed to mount read/write filesystem"
                    return 1
                fi
            fi
            clic_cmd="$clic_cmd -m $haveMByte"
            clic_cmd="$clic_cmd -c $HYBRID_PERSISTENT_DIR/.clicfs_COW"
        else
            # write into a device directly
            clic_cmd="$clic_cmd -m $haveMByte -c $rwDevice --ignore-cow-errors"
        fi
    fi
    #======================================
    # mount/check clic file
    #--------------------------------------
    if [ ! -z "$NFSROOT" ];then
        #======================================
        # clic exported via NFS
        #--------------------------------------
        if ! kiwiMount "$roDevice" "$roDir" "" $loopf;then
            Echo "Failed to mount NFS filesystem"
            return 1
        fi
        if [ ! -e "$roDir/fsdata.ext4" ];then
            Echo "Can't find clic fsdata.ext4 in NFS export"
            return 1
        fi
    else
        #======================================
        # mount clic container
        #--------------------------------------
        if [ -z "$loopf" ];then
            loopf=$roDevice
        fi
        if ! $clic_cmd $loopf $roDir; then  
            Echo "Failed to mount clic filesystem"
            return 1
        fi 
    fi
    #======================================
    # mount root over clic
    #--------------------------------------
    size=$(stat -c %s $roDir/fsdata.ext4)
    size=$((size/512))
    # we don't want reserved blocks...
    tune2fs -m 0 $roDir/fsdata.ext4 >/dev/null
    # we don't want automatic filesystem check...
    tune2fs -i 0 $roDir/fsdata.ext4 >/dev/null
    if [ ! $LOCAL_BOOT = "no" ];then
        e2fsck -p $roDir/fsdata.ext4
    fi
    if [ $LOCAL_BOOT = "no" ] || [ $ramOnly = 1 ];then
        resize2fs $roDir/fsdata.ext4 $size"s"
    fi
    mount -o loop,noatime,nodiratime,errors=remount-ro,barrier=0 \
        $roDir/fsdata.ext4 $prefix
    if [ ! $? = 0 ];then
        Echo "Failed to mount ext4 clic container"
        return 1
    fi
    # Give fuse enough time to settle for I/O in the ext4 container
    # Unconditional waiting is never a good idea however I couldn't
    # find a good solution to this problem because a lookup on read
    # or write could cause an ro remount of the ext4 container
    # Thus we just sleep a while before proceeding
    sleep 5
    export haveClicFS=yes
    return 0
}
#======================================
# mountSystemCombined
#--------------------------------------
function mountSystemCombined {
    local IFS=$IFS_ORIG
    local mountDevice=$1
    local loopf=$2
    local roDevice=$mountDevice
    local rwDevice
    local options
    local rootfs
    local meta
    local inode_nr
    local min_size
    local haveKByte
    local haveMByte
    local needMByte
    local prefix=/mnt
    if [ -e "$HYBRID_RW" ];then
        rwDevice=$HYBRID_RW
    elif [ "$haveLuks" = "yes" ]; then
        rwDevice="/dev/mapper/luksReadWrite"
    elif [ "$haveLVM" = "yes" ]; then
        rwDevice="/dev/$kiwi_lvmgroup/LVRoot"
    else
        rwDevice=$(getNextPartition $mountDevice)
    fi
    mkdir /read-only >/dev/null
    # /.../
    # mount the read-only partition to /read-only and use
    # mount option -o ro for this filesystem
    # ----
    if ! kiwiMount "$roDevice" "/read-only" "" $loopf;then
        Echo "Failed to mount read only filesystem"
        return 1
    fi
    # /.../
    # mount a tmpfs which will become the root fs (/) later on
    # and extract the rootfs tarball with the RAM data and the read-only
    # and read-write links into the tmpfs.
    # ----
    rootfs=/read-only/rootfs.tar
    if [ ! -f $rootfs ];then
        Echo "Can't find rootfs tarball"
        umount "$roDevice" &>/dev/null
        return 1
    fi
    meta=/read-only/rootfs.meta
    if [ ! -f $inodes ];then
        Echo "Can't find rootfs meta data"
        umount "$roDevice" &>/dev/null
        return 1
    fi
    # /.../
    # source rootfs meta data variables:
    # => min_size # minimum required tmpfs size in bytes
    # => inode_nr # number of inodes
    # ----
    source $meta
    # /.../
    # check if rootfs tarball fits into memory
    # ----
    haveKByte=$(cat /proc/meminfo | grep MemFree | cut -f2 -d: | cut -f1 -dk)
    haveMByte=$((haveKByte / 1024))
    needMByte=$((min_size  / 1048576))
    Echo "Have size: proc/meminfo -> $haveMByte MB"
    Echo "Need size: $rootfs -> $needMByte MB"
    if [ "$haveMByte" -lt "$needMByte" ];then
        systemException \
            "Not enough RAM space available for temporary data" \
        "reboot"
    fi
    # /.../
    # mount tmpfs, reserve max $splitroot_size for the rootfs data
    # ----
    options="size=${splitroot_size}M,nr_inodes=$inode_nr"
    if ! mount -t tmpfs tmpfs -o $options $prefix;then
        systemException \
            "Failed to mount root tmpfs" \
        "reboot"
    fi
    cd $prefix && tar xf $rootfs >/dev/null && cd /
    # /.../
    # check for a read-write data file and put it on the read-write
    # device or to the root tmpfs
    # ---
    if [ -e ${loopf}-read-write ];then
        local target=$prefix
        if [ -e "$HYBRID_RW" ];then
            mkdir -p $prefix/read-write
            kiwiMount "$rwDevice" "$prefix/read-write"
            target=$prefix/read-write
        fi
        mkdir -p $prefix-tmp
        if ! mount -o loop ${loopf}-read-write $prefix-tmp;then
            systemException \
                "Failed to mount read-write data file" \
            "reboot"
        fi
        pushd $prefix-tmp &>/dev/null
        for item in *;do
            if [ -L /$target/$item ];then
                rm -f /$target/$item
            fi
            if [ ! -e /$target/$item ];then
                if ! cp -a $prefix-tmp/$item $target;then
                    systemException \
                        "Failed to copy $item to $target" \
                    "reboot"
                fi
            fi
        done
        popd &>/dev/null
        if [ -e "$HYBRID_RW" ];then
            umount $prefix/read-write
        fi
        umount $prefix-tmp
        rmdir $prefix-tmp
    fi
    # /.../
    # create a read-only mount point and move the /read-only
    # mount into the root tree. After that remove the read-only
    # directory and create a link to read-only instead
    # ----
    mkdir $prefix/read-only >/dev/null
    mount --move /read-only $prefix/read-only >/dev/null
    rm -rf /read-only >/dev/null
    ln -s $prefix/read-only /read-only >/dev/null || return 1
    if ! echo $rwDevice | grep -q loop;then
        if partitionSize $rwDevice &>/dev/null;then
            # /.../
            # mount the read-write partition to read-write and create a link
            # ----
            mkdir -p $prefix/read-write >/dev/null
            kiwiMount "$rwDevice" "$prefix/read-write"
            rm -rf /read-write >/dev/null
            ln -s $prefix/read-write /read-write >/dev/null
        fi
    fi
}
#======================================
# mountSystemStandard
#--------------------------------------
function mountSystemStandard {
    local IFS=$IFS_ORIG
    local mountDevice=$1
    local variable
    local volume
    local content
    local volpath
    local mpoint
    local mppath
    local prefix=/mnt
    if [ ! -z $FSTYPE ]          && 
         [ ! $FSTYPE = "unknown" ] && 
         [ ! $FSTYPE = "auto" ]
    then
        kiwiMount "$mountDevice" "$prefix"
    else
        mount $mountDevice $prefix >/dev/null
    fi
    if [ "$haveLVM" = "yes" ];then
        for i in $(cat /.profile | grep -E 'kiwi_LVM_|kiwi_allFreeVolume');do
            variable=$(echo $i|cut -f1 -d=)
            volume=$(echo $i| cut -f3- -d_ | cut -f1 -d=)
            content=$(echo $i|cut -f2 -d= | tr -d \' | tr -d \")
            volpath=$(echo $content | cut -f3 -d:)
            if [ -z "$volpath" ];then
                volpath=$(echo $volume | tr _ /)
            fi
            mpoint=$(echo $volpath | sed -e s@^LV@@)
            if \
                [ ! $volume = "LVRoot" ] && \
                [ ! $volume = "LVComp" ] && \
                [ ! $volume = "LVSwap" ]
            then
                mkdir -p $prefix/$mpoint
                kiwiMount "/dev/$kiwi_lvmgroup/$volume" "$prefix/$mpoint"
            fi
        done
    fi
    return $?
}
#======================================
# mountSystem
#--------------------------------------
function mountSystem {
    local IFS=$IFS_ORIG
    local retval=0
    #======================================
    # set primary mount device
    #--------------------------------------
    local mountDevice="$imageRootDevice"
    if [ ! -z "$1" ];then
        mountDevice="$1"
    fi
    #======================================
    # wait for storage device to appear
    #--------------------------------------
    if ! echo $mountDevice | grep -qE "loop|vers=";then
        waitForStorageDevice $mountDevice
    fi
    #======================================
    # check root tree type
    #--------------------------------------
    if [ ! -z "$COMBINED_IMAGE" ];then
        mountSystemCombined "$mountDevice" $2
        retval=$?
    elif [ ! -z "$UNIONFS_CONFIG" ];then
        local unionFST=`echo $UNIONFS_CONFIG | cut -d , -f 3`
        if [ "$unionFST" = "clicfs" ];then
            mountSystemClicFS $2
        elif [ "$unionFST" = "seed" ];then
            mountSystemSeedBtrFS $2
        elif [ "$unionFST" = "overlay" ];then
            mountSystemUnionFS $2
        elif [ "$unionFST" = "unionfs" ];then
            mountSystemUnionFS $2
        else
            systemException \
                "Unknown overlay mount method: $unionFST" \
            "reboot"
        fi
        retval=$?
    else
        mountSystemStandard "$mountDevice"
        retval=$?
    fi
    #======================================
    # setup boot partition
    #--------------------------------------
    if \
        [ -z "$skipSetupBootPartition" ]  && \
        [ "$LOCAL_BOOT" = "no" ]          && \
        [ ! "$systemIntegrity" = "fine" ] && \
        [ $retval = 0 ]                   && \
        [ -z "$RESTORE" ]
    then
        if [[ $kiwi_iname =~ netboot ]];then
            setupBootPartitionPXE
        else
            setupBootPartition
        fi
    fi
    #======================================
    # reset mount counter
    #--------------------------------------
    resetMountCounter
    return $retval
}
#======================================
# cleanDirectory
#--------------------------------------
function cleanDirectory {
    local IFS=$IFS_ORIG
    local directory=$1
    shift 1
    local save=$@
    local tmpdir=`mktemp -d`
    for saveItem in $save;do
        mv $directory/$saveItem $tmpdir >/dev/null
    done
    rm -rf $directory/*
    mv $tmpdir/* $directory
    rm -rf $tmpdir
}
#======================================
# searchGroupConfig
#--------------------------------------
function searchGroupConfig {
    local IFS=$IFS_ORIG
    local localhwaddr=$DHCPCHADDR
    local GROUPCONFIG=/etc/config.group
    local list_var
    local mac_list
    #======================================
    # Load group file if it exists
    #--------------------------------------
    Echo "Checking for config file: config.group";
    fetchFile KIWI/config.group $GROUPCONFIG
    if [ ! -s $GROUPCONFIG ]; then
        return
    fi
    Echo "Found config.group, determining available groups";
    importFile < $GROUPCONFIG
    Debug "KIWI_GROUP = '$KIWI_GROUP'"
    #======================================
    # Parse group file
    #--------------------------------------
    if [ -z "$KIWI_GROUP" ] ; then
        systemException \
            "No groups defined in $GROUPCONFIG" \
        "reboot"
    fi
    for i in `echo "$KIWI_GROUP" | sed 's/,/ /g' | sed 's/[ \t]+/ /g'`; do
        Echo "Lookup MAC address: $localhwaddr in ${i}_KIWI_MAC_LIST"
        eval list_var="${i}_KIWI_MAC_LIST"
        eval mac_list=\$$list_var
        searchGroupHardwareAddress $i "$mac_list"
        if [ -s $CONFIG ]; then
            break
        fi
        unset list_var
        unset mac_list
    done
}
#======================================
# searchGroupHardwareAddress
#--------------------------------------
function searchGroupHardwareAddress {
    # /.../
    # function to check the existance of the hosts
    # hardware address within the defined "mac_list".
    # If the hardware address is found, load the config file.
    # ----
    local IFS=$IFS_ORIG
    local localhwaddr=$DHCPCHADDR
    local local_group=$1
    local mac_list=$2
    for j in `echo "$mac_list" | sed 's/,/ /g' | sed 's/[ \t]+/ /g'`; do
        if [ "$localhwaddr" = "$j" ] ; then
            Echo "MAC address $localhwaddr found in group $local_group"
            Echo "Checking for config file: config.$local_group"
            fetchFile KIWI/config.$local_group $CONFIG
            if [ ! -s $CONFIG ]; then
                systemException \
                    "No configuration found for $j" \
                "reboot"
            fi
            break
        fi
    done
}
#======================================
# searchAlternativeConfig
#--------------------------------------
function searchAlternativeConfig {
    local IFS=$IFS_ORIG
    # Check config.IP in Hex (pxelinux style)
    localip=$IPADDR
    hexip1=`echo $localip | cut -f1 -d'.'`
    hexip2=`echo $localip | cut -f2 -d'.'`
    hexip3=`echo $localip | cut -f3 -d'.'`
    hexip4=`echo $localip | cut -f4 -d'.'`
    hexip=`printf "%02X" $hexip1 $hexip2 $hexip3 $hexip4`
    STEP=8
    while [ $STEP -gt 0 ]; do
        hexippart=`echo $hexip | cut -b -$STEP`
        Echo "Checking for config file: config.$hexippart"
        fetchFile KIWI/config.$hexippart $CONFIG
        if test -s $CONFIG;then
            break
        fi
        let STEP=STEP-1
    done
    # Check config.default if no hex config was found
    if test ! -s $CONFIG;then
        Echo "Checking for config file: config.default"
        fetchFile KIWI/config.default $CONFIG
    fi
}
#======================================
# searchHardwareMapConfig
#--------------------------------------
function searchHardwareMapConfig {
    local IFS=$IFS_ORIG
    local list_var
    local mac_list
    #======================================
    # return if no map was specified
    #--------------------------------------
    if [ -z "$HARDWARE_MAP" ];then
        return
    fi
    Echo "Found hardware/vendor map configuration variable"
    #===========================================
    # Evaluate the MAP list, and test for hwaddr
    #-------------------------------------------
    for i in `echo "$HARDWARE_MAP" | sed 's/,/ /g' | sed 's/[ \t]+/ /g'`; do
        Echo "Lookup MAC address: $localhwaddr in ${i}_HARDWARE_MAP"
        eval list_var="${i}_HARDWARE_MAP"
        eval mac_list=\$$list_var
        Debug "${i}_HARDWARE_MAP = '$mac_list'"
        searchHardwareMapHardwareAddress $i "$mac_list"
        if [ -s $CONFIG ]; then
            break
        fi
        unset list_var
        unset mac_list
    done
}
#======================================
# searchHardwareMapHardwareAddress
#--------------------------------------
function searchHardwareMapHardwareAddress {
    local IFS=$IFS_ORIG
    local HARDWARE_CONFIG=/etc/config.hardware
    local localhwaddr=$DHCPCHADDR
    local hardware_group=$1
    local mac_list=$2
    Debug "hardware_group = '$hardware_group'"
    Debug "mac_list = '$mac_list'"
    for j in `echo "$mac_list" | sed 's/,/ /g' | sed 's/[ \t]+/ /g'`; do
        if [ "$localhwaddr" = "$j" ] ; then
            Echo "MAC address $localhwaddr found in group $hardware_group"
            Echo "Checking for config file: hardware_config.$hardware_group"
            fetchFile KIWI/hardware_config.$hardware_group $HARDWARE_CONFIG
            if [ ! -s $HARDWARE_CONFIG ]; then
                systemException \
                    "No configuration found for $j" \
                "reboot"
            fi
            importFile < $HARDWARE_CONFIG
            break
        fi
    done
}
#======================================
# runHook
#--------------------------------------
function runHook {
    local IFS=$IFS_ORIG
    #======================================
    # Check for execution permission
    #--------------------------------------
    if [ ! -z "$KIWI_FORBID_HOOKS" ];then
        Echo "Hook script execution is forbidden by KIWI_FORBID_HOOKS"
        return
    fi
    #======================================
    # Init custom post hook commands
    #--------------------------------------
    # a) switch post command execution off, can be activated by hook script
    export eval KIWI_ALLOW_HOOK_CMD_$1=0
    #======================================
    # Search and execute hook script
    #--------------------------------------
    HOOK="/kiwi-hooks/$1.sh"
    if [ ! -e $HOOK ];then
        HOOK="/lib/kiwi/hooks/$1.sh"
    fi
    if [ -e $HOOK ]; then
        . $HOOK "$@"
    fi
    #======================================
    # Run custom post hook commands
    #--------------------------------------
    # b) check permisson and state of command list
    if [ ! -z "$KIWI_FORBID_HOOK_CMDS"  ];then
        Echo "Post-Hook command execution is forbidden by KIWI_FORBID_HOOK_CMDS"
        return
    fi
    eval local call_cmd=\$KIWI_ALLOW_HOOK_CMD_$1
    if [ "$call_cmd" -eq 1 ]; then
        eval local call=\$KIWI_HOOK_CMD_$1
        eval $call
    fi
}
#======================================
# getNextPartition
#--------------------------------------
function getNextPartition {
    local IFS=$IFS_ORIG
    part=$1
    nextPart=`echo $part | sed -e "s/\(.*\)[0-9]/\1/"`
    nextPartNum=`echo $part | sed -e "s/.*\([0-9]\)/\1/"`
    nextPartNum=$((nextPartNum + 1))
    nextPart="${nextPart}${nextPartNum}"
    echo $nextPart
}
#======================================
# startShell
#--------------------------------------
function startShell {
    # /.../
    # start a debugging shell on ELOG_BOOTSHELL
    # ----
    local IFS=$IFS_ORIG
    if [ ! -z $kiwidebug ];then
        if [ ! -e $ELOG_BOOTSHELL ];then
            Echo "No terminal $ELOG_BOOTSHELL available for debug shell"
            return
        fi
        Echo "Starting boot shell on $ELOG_BOOTSHELL"
        setctsid -f $ELOG_BOOTSHELL /bin/bash -i
        ELOGSHELL_PID=$(fuser $ELOG_BOOTSHELL | tr -d " ")
        echo ELOGSHELL_PID=$ELOGSHELL_PID >> /iprocs
    fi
}
#======================================
# killShell
#--------------------------------------
function killShell {
    # /.../
    # kill debugging shell on ELOG_BOOTSHELL
    # ----
    local IFS=$IFS_ORIG
    local umountProc=0
    if [ ! -e /proc/mounts ];then
        mount -t proc proc /proc
        umountProc=1
    fi
    if [ ! -z "$ELOGSHELL_PID" ];then
        Echo "Stopping boot shell"
        kill $ELOGSHELL_PID &>/dev/null
    fi
    if [ $umountProc -eq 1 ];then
        umount /proc
    fi
}
#======================================
# waitForStorageDevice
#--------------------------------------
function waitForStorageDevice {
    # /.../
    # function to check access on a storage device
    # which could be a whole disk or a partition.
    # the function will wait until the size of the
    # storage device could be obtained or the check
    # counter equals 4
    # ----
    local IFS=$IFS_ORIG
    local device=$1
    local check=0
    udevPending
    while true;do
        partitionSize $device &>/dev/null
        if [ $? = 0 ];then
            sleep 1; return 0
        fi
        if [ $check -eq 30 ];then
            return 1
        fi
        Echo "Waiting for device $device to settle..."
        check=$((check + 1))
        sleep 2
    done
}
#======================================
# waitForLinkUp
#--------------------------------------
function waitForLinkUp {
    # /.../
    # wait for the network link to enter UP state
    # ----
    local IFS=$IFS_ORIG
    local dev=$1
    local check=0
    while true;do
        ip link ls $dev | grep -qi "state UP"
        if [ $? = 0 ];then
            sleep 1; return 0
        fi
        if [ $check -eq 30 ];then
            return 1
        fi
        Echo "Waiting for link up on ${dev}..."
        check=$((check + 1))
        sleep 2
    done
}
#======================================
# waitForBlockDevice
#--------------------------------------
function waitForBlockDevice {
    # /.../
    # function to check if the given block device
    # exists. If not the function will wait until the
    # device appears or the check counter equals 4
    # ----
    local IFS=$IFS_ORIG
    local device=$1
    local check=0
    udevPending
    while true;do
        if [ -b $device ] || [ $check -eq 4 ];then
            break
        fi
        Echo "Waiting for device $device to settle..."
        check=$((check + 1))
        sleep 2
    done
}

#======================================
# atftpProgress
#--------------------------------------
function atftpProgress {
    # /.../
    # atftp doesn't use a stream based download and sometimes
    # seek back and forth which makes it hard to use pipes for
    # progress indication. Therefore we watch the trace output
    # ----
    local IFS=$IFS_ORIG
    local imgsize=$1    # image size in MB
    local prefix=$2     # line prefix text
    local file=$3       # file with progress data
    local blocksize=$4  # blocksize use for download
    local bytes=0       # log lines multiplied by blocksize
    local lines=0       # log lines
    local percent=0     # in percent of all
    local all=$((imgsize * 1024 * 1024))
    local line
    local step=0
    # number of cycles for approx. 2% steps
    local max_step=$(($all / $blocksize / 25))
    cat < dev/null > $file.tmp
    #======================================
    # print progress information
    #--------------------------------------
    while read line ;do
        echo "$line" >> $file.tmp
        let step=step+1
        if [ $step -lt $max_step ]; then
            continue
        fi
        step=0
        # /.../
        # the trace logs two lines indicating one download block of
        # blocksize bytes. We assume only full blocks. At the end
        # it might happen that only a part of blocksize bytes is
        # required. The function does not precisely calculate them
        # and assumes blocksize bytes. imho that's ok for the progress
        # bar. In order to be exact the function would have to sum
        # up all bytes from the trace log for each iteration which
        # would cause the download to pause because it has to wait
        # for the progress bar to get ready
        # ----
        # the same block can be transferred multiple times
        lines=$(grep "^sent ACK" $file.tmp | sort -u | wc -l)
        bytes=$((lines * $blocksize))
        percent=$(echo "scale=2; $bytes * 100"  | bc)
        percent=$(echo "scale=0; $percent / $all" | bc)
        echo -en "$prefix ( $percent%)\r"
    done
    grep -v "^\(received \)\|\(sent \)" $file.tmp > $file
    rm $file.tmp
    echo
}

#======================================
# encodeURL
#--------------------------------------
function encodeURL {
    # /.../
    # encode special characters in URL's to correctly
    # serve as input for fetchFile and putFile
    # ----
    local IFS=$IFS_ORIG
    local STR
    local CH
    STR="$@"
    echo -n "$STR" | while read -n1 CH; do
        [[ $CH =~ [-_A-Za-z0-9./] ]] && printf "$CH" || printf "%%%x" \'"$CH"
    done
}

#======================================
# fetchFile
#--------------------------------------
function fetchFile {
    # /.../
    # the generic fetcher which is able to use different protocols
    # tftp,ftp, http, https. fetchFile is used in the netboot linuxrc
    # and uses curl and atftp to download files from the network
    # ----
    local IFS=$IFS_ORIG
    local path=$1
    local dest=$2
    local izip=$3
    local host=$4
    local type=$5
    local chunk=$6
    local encoded_path
    local dump
    local call
    local call_pid
    local unzip
    #======================================
    # source path is required
    #--------------------------------------
    if [ -z "$path" ]; then
        systemException "No source path specified" "reboot"
    fi
    #======================================
    # destination path is required
    #--------------------------------------
    if [ -z "$dest" ];then
        systemException "No destination path specified" "reboot"
    fi
    #======================================
    # source host is required
    #--------------------------------------
    if [ -z "$host" ]; then
        if test -z "$SERVER"; then
            systemException "No source server specified" "reboot"
        fi
        host=$SERVER
    fi
    #======================================
    # set default chunk size
    #--------------------------------------
    if [ -z "$chunk" ];then
        chunk=4k
    fi
    #======================================
    # set default service type
    #--------------------------------------
    if [ -z "$type" ]; then
        if [ -z "$SERVERTYPE" ]; then
            type="tftp"
        else
            type="$SERVERTYPE"
        fi
    fi
    #======================================
    # set source path + tool if compressed
    #--------------------------------------
    if [ ! -z "$izip" ] && [[ ! "$izip" =~ ^uncomp ]];then
        if [ $izip = "compressed" ] || [ "$izip" = "compressed-gzip" ]; then
            unzip="gzip -d"
            path=$(echo "$path" | sed -e s@\\.gz@@)
            path="$path.gz"
        elif [ $izip = "compressed-xz" ];then
            unzip="xz -d"
            path=$(echo "$path" | sed -e s@\\.xz@@)
            path="$path.xz"
        else
            systemException "Unknown compression mode: $izip" "reboot"
        fi
    else
        unset izip
    fi
    #======================================
    # encode special URL characters
    #--------------------------------------
    encoded_path=$(encodeURL "$path")
    #======================================
    # setup progress meta information
    #--------------------------------------
    dump="dd bs=$chunk of=\"$dest\""
    showProgress=0
    if \
        [ -x /usr/bin/dcounter ]      && \
        [ -f /etc/image.md5 ]         && \
        [ -b "$dest" ]                && \
        [ -z "$disableProgressInfo" ]
    then
        showProgress=1
        read sum1 blocks blocksize zblocks zblocksize < /etc/image.md5
        needBytes=$((blocks * blocksize))
        needMByte=$((needBytes / 1048576))
        if [ ! -z "$zblocks" ];then
            needZBytes=$((zblocks * zblocksize))
            needZMByte=$((needZBytes / 1048576))
        fi
        progressBaseName=$(basename "$path")
        TEXT_LOAD=$(getText "Loading %1" "$progressBaseName")
        TEXT_COMP=$(getText "Uncompressing %1" "$progressBaseName")
        dump="dcounter -s $needMByte -l \"$TEXT_LOAD \" 2>/progress | $dump"
    fi
    #======================================
    # build download command
    #--------------------------------------
    case "$type" in
        "local")
            if [ ! -z "$izip" ];then
                call="$unzip < $host/$path \
                    2>$TRANSFER_ERRORS_FILE | $dump"
            else
                call="dd if=$host/$path bs=$chunk |\
                    $dump"
            fi
            ;;
        "http")
            if [ ! -z "$izip" ];then
                call="curl -f http://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $unzip 2>>$TRANSFER_ERRORS_FILE | $dump"
            else
                call="curl -f http://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $dump"
            fi
            ;;
        "https")
            if [ ! -z "$izip" ];then
                call="curl -f -k https://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $unzip 2>>$TRANSFER_ERRORS_FILE | $dump"
            else
                call="curl -f -k https://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $dump"
            fi
            ;;
        "ftp")
            if [ ! -z "$izip" ];then
                call="curl ftp://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $unzip 2>>$TRANSFER_ERRORS_FILE | $dump"
            else
                call="curl ftp://$host/$encoded_path \
                    2>$TRANSFER_ERRORS_FILE |\
                    $dump"
            fi
            ;;
        "tftp")
            validateBlockSize
            # /.../
            # atftp activates multicast by '--option "multicast"'
            # and deactivates it again  by '--option "disable multicast"'
            # ----
            if [ -f /etc/image.md5 ] && [ -b "$dest" ];then
                # enable multicast for system image and transfer to block device
                multicast_atftp="multicast"
            else
                # disable multicast for any other transfer
                multicast_atftp="disable multicast"
            fi
            havetemp_dir=1
            if [ -z "$FETCH_FILE_TEMP_DIR" ];then
                # we don't have a tmp dir available for downloading
                havetemp_dir=0
            elif [ -e "$FETCH_FILE_TEMP_DIR/${path##*/}" ];then
                # temporary download data already exists
                havetemp_dir=0
            else
                # prepare use of temp files for compressed download
                FETCH_FILE_TEMP_FILE="$FETCH_FILE_TEMP_DIR/${path##*/}"
                export FETCH_FILE_TEMP_FILE
            fi
            if [ ! -z "$izip" ];then
                if [ $havetemp_dir -eq 0 ];then
                    # /.../
                    # operate without temp files, standard case
                    # ----
                    call="busybox tftp \
                        -b $imageBlkSize -g -r \"$path\" \
                        -l >($unzip 2>>$TRANSFER_ERRORS_FILE | $dump) \
                        $host 2>>$TRANSFER_ERRORS_FILE"
                else
                    # /.../
                    # operate using temp files
                    # export the path to allow temp file management in a hook
                    # ----
                    if [ $showProgress -eq 1 ];then
                        call="(atftp \
                            --trace \
                            --option \"$multicast_atftp\"  \
                            --option \"blksize $imageBlkSize\" \
                            -g -r \"$path\" -l \"$FETCH_FILE_TEMP_FILE\" \
                            $host 2>&1 | \
                            atftpProgress \
                                $needZMByte \"$TEXT_LOAD\" \
                                $TRANSFER_ERRORS_FILE $imageBlkSize \
                            >&2 ; \
                            $unzip < \"$FETCH_FILE_TEMP_FILE\" | \
                                dcounter -s $needMByte -l \"$TEXT_COMP \" | \
                                dd bs=$chunk of=\"$dest\" ) 2>/progress "
                    else
                        call="atftp \
                            --option \"$multicast_atftp\"  \
                            --option \"blksize $imageBlkSize\" \
                            -g -r \"$path\" -l \"$FETCH_FILE_TEMP_FILE\" $host \
                            &> $TRANSFER_ERRORS_FILE ; \
                            $unzip < \"$FETCH_FILE_TEMP_FILE\" | \
                            dd bs=$chunk of=\"$dest\" "
                    fi
                fi
            else
                if [ $showProgress -eq 1 ];then
                    call="atftp \
                        --trace \
                        --option \"$multicast_atftp\"  \
                        --option \"blksize $imageBlkSize\" \
                        -g -r \"$path\" -l \"$dest\" $host 2>&1 | \
                        atftpProgress \
                            $needMByte \"$TEXT_LOAD\" \
                            $TRANSFER_ERRORS_FILE $imageBlkSize \
                        > /progress"
                else
                    call="atftp \
                        --option \"$multicast_atftp\"  \
                        --option \"blksize $imageBlkSize\" \
                        -g -r \"$path\" -l \"$dest\" $host \
                        &> $TRANSFER_ERRORS_FILE"
                fi
            fi
            ;;
        *)
            systemException "Unknown download type: $type" "reboot"
            ;;
    esac
    #======================================
    # run the download
    #--------------------------------------
    if [ $showProgress -eq 1 ];then
        test -e /progress || mkfifo /progress
        test -e /tmp/load_code && rm -f /tmp/load_code
        errorLogStop
        (
            eval $call \; 'echo ${PIPESTATUS[0]} > /tmp/load_code' &>/dev/null
        )&
        call_pid=$!
        echo "cat /progress | dialog \
            --backtitle \"$TEXT_INSTALLTITLE\" \
            --progressbox 3 65
        " > /tmp/progress.sh
        if FBOK;then
            fbiterm -m $UFONT -- bash -e /tmp/progress.sh
        else
            bash -e /tmp/progress.sh
        fi
        clear
        wait $call_pid
        loadCode=`cat /tmp/load_code`
        if [ -z "$loadCode" ]; then
            systemException \
                "Failed to get the download process return value" \
            "reboot"
        fi
    else
        eval $call \; 'loadCode=${PIPESTATUS[0]}'
    fi
    if [ $showProgress -eq 1 ];then
        errorLogContinue
    fi
    loadStatus=`cat $TRANSFER_ERRORS_FILE`
    return $loadCode
}

#======================================
# fetchFileLocal
#--------------------------------------
function fetchFileLocal {
    # /.../
    # ----
    fetchFile "$1" "$2" "$3" "$KIWI_LOCAL_CACHE_DIR" "local"
}

#======================================
# putFile
#--------------------------------------
function putFile {
    # /.../
    # the generic putFile function is used to upload boot data on
    # a server. Supported protocols are tftp, ftp, http, https
    # ----
    local IFS=$IFS_ORIG
    local path=$1
    local dest=$2
    local host=$3
    local type=$4
    local encoded_dest
    if test -z "$path"; then
        systemException "No path specified" "reboot"
    fi
    if test -z "$host"; then
        if test -z "$SERVER"; then
            systemException "No server specified" "reboot"
        fi
        host=$SERVER
    fi
    if test -z "$type"; then
        if test -z "$SERVERTYPE"; then
            type="tftp"
        else
            type="$SERVERTYPE"
        fi
    fi
    encoded_dest=$(encodeURL "$dest")
    case "$type" in
        "local")
            cp -f "$path" "$host/$dest" > $TRANSFER_ERRORS_FILE 2>&1
            return $?
            ;;
        "http")
            curl -f -T "$path" http://$host/$encoded_dest \
                > $TRANSFER_ERRORS_FILE 2>&1
            return $?
            ;;
        "https")
            curl -f -T "$path" https://$host/$encoded_dest \
                > $TRANSFER_ERRORS_FILE 2>&1
            return $?
            ;;
        "ftp")
            curl -T "$path" ftp://$host/$encoded_dest \
                > $TRANSFER_ERRORS_FILE 2>&1
            return $?
            ;;
        "tftp")
            atftp -p -l "$path" -r "$dest" $host >/dev/null 2>&1
            return $?
            ;;
        *)
            systemException "Unknown download type: $type" "reboot"
            ;;
    esac
}

#======================================
# importBranding
#--------------------------------------
function importBranding {
    # /.../
    # include possible custom boot loader and bootsplash files
    # to the system to allow to use them persistently
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    if [ -f /image/loader/message ];then
        if ! canWrite $prefix/boot;then
            Echo "Can't write to boot, import of boot message skipped"
        else
            mv /image/loader/message $prefix/boot
        fi
    fi
    if [ -f /image/loader/branding/logo.mng ];then
    if [ -d $prefix/etc/bootsplash/themes ];then
        for theme in $prefix/etc/bootsplash/themes/*;do
            if [ -d $theme/images ];then
                if ! canWrite $theme;then
                    Echo "Can't write to $theme, import of boot theme skipped"
                    continue
                fi
                cp /image/loader/branding/logo.mng  $theme/images
                cp /image/loader/branding/logov.mng $theme/images
                cp /image/loader/branding/*.jpg $theme/images
                cp /image/loader/branding/*.cfg $theme/config
            fi
        done  
    fi
    fi
}

#======================================
# validateRootTree
#--------------------------------------
function validateRootTree {
    # /.../
    # after the root of the system image has been mounted we should
    # check whether that mount is a valid system tree or not. Therefore
    # some sanity checks are made here
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    if [ ! -x $prefix/sbin/init -a ! -L $prefix/sbin/init ];then
        systemException "/sbin/init no such file or not executable" "reboot"
    fi
}

#======================================
# getDiskID
#--------------------------------------
function getDiskID {
    # /.../
    # this function is able to turn a given standard device
    # name into the udev ID based representation
    # ----
    local IFS=$IFS_ORIG
    local device=$1
    local swap=$2
    local prefix=by-id
    if [ -z "$device" ];then
        return
    fi
    if [ ! -z "$kiwi_lvmgroup" ] && echo $device | grep -q "$kiwi_lvmgroup";then
        echo $device
        return
    fi
    if [ -z "$swap" ] && [[ $device =~ ^/dev/md ]];then
        echo $device
        return
    fi
    if [ ! -z "$NON_PERSISTENT_DEVICE_NAMES" ]; then
        echo $device
        return
    fi
    if [[ $device =~ ^/dev/dm- ]];then
        for i in /dev/mapper/*;do
            if [ ! -L $i ];then
                continue
            fi
            local dev=$(readlink $i)
            dev=/dev/$(basename "$dev")
            if [ $dev = $device ];then
                echo $i
                return
            fi
        done
    fi
    if [ ! -z "$kiwi_devicepersistency" ];then
        prefix=$kiwi_devicepersistency
    fi
    for i in /dev/disk/$prefix/*;do
        if [ -z "$i" ];then
            continue
        fi
        if echo $i | grep -q edd-;then
            continue
        fi
        local dev=$(readlink $i)
        dev=/dev/$(basename "$dev")
        if [ $dev = $device ];then
            echo $i
            return
        fi
    done
    echo $device
}
#======================================
# getDiskDevice
#--------------------------------------
function getDiskDevice {
    # /.../
    # this function is able to turn the given udev disk
    # ID label into the /dev/ device name
    # ----
    local IFS=$IFS_ORIG
    local device=$(readlink $1)
    if [ -z "$device" ];then
        echo $1
        return
    fi
    device=$(basename $device)
    device=/dev/$device
    echo $device
}
#======================================
# getDiskModel
#--------------------------------------
function getDiskModels {
    # /.../
    # this function returns the disk identifier as
    # registered in the sysfs layer
    # ----
    local IFS=$IFS_ORIG
    local models=`cat /sys/block/*/device/model 2>/dev/null`
    if [ ! -z "$models" ];then
        echo $models; return
    fi
    echo "unknown"
}
#======================================
# setupInittab
#--------------------------------------
function setupInittab {
    # /.../
    # setup default runlevel according to /proc/cmdline
    # information. If textmode is set to 1 we will boot into
    # runlevel 3
    # ----
    local IFS=$IFS_ORIG
    local prefix=$1
    if cat /proc/cmdline | grep -qi "textmode=1";then
        sed -i -e s"@id:.*:initdefault:@id:3:initdefault:@" $prefix/etc/inittab
    fi
}
#======================================
# setupConfigFiles
#--------------------------------------
function setupConfigFiles {
    # /.../
    # all files created below /config inside the initrd are
    # now copied into the system image
    # ----
    local IFS=$IFS_ORIG
    local file
    local dir
    local prefix=/mnt
    cd /config
    find . -type f | while read file;do
        dir=$(dirname $file)
        if [ ! -d $prefix/$dir ];then
            mkdir -p $prefix/$dir
        fi
        if ! canWrite $prefix/$dir;then
            Echo "Can't write to $dir, read-only filesystem... skipped"
            continue
        fi
        cp $file $prefix/$file
    done
    cd /
    rm -rf /config
}
#======================================
# activateImage
#--------------------------------------
function activateImage {
    # /.../
    # move the udev created nodes from the initrd into
    # the system root tree call the pre-init phase which
    # already runs in the new tree and finaly switch the
    # new tree to be the new root (/) 
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    #======================================
    # setup image name
    #--------------------------------------
    local name
    if [ ! -z "$stickSerial" ];then
        name="$stickSerial on -> $stickDevice"
    elif [ ! -z "$imageName" ];then
        name=$imageName
    elif [ ! -z "$imageRootName" ];then
        name=$imageRootName
    elif [ ! -z "$imageRootDevice" ];then
        name=$imageRootDevice
    elif [ ! -z "$imageDiskDevice" ];then
        name=$imageDiskDevice
    else
        name="unknown"
    fi
    #======================================
    # move union mount points to system
    #--------------------------------------
    local roDir=read-only
    local rwDir=read-write
    local xiDir=xino
    if [ -z "$NFSROOT" ];then
        if [ -d $roDir ];then
            mkdir -p $prefix/$roDir && mount --move /$roDir $prefix/$roDir
        fi
        if [ -d $rwDir ];then
            mkdir -p $prefix/$rwDir && mount --move /$rwDir $prefix/$rwDir
        fi
        if [ -d $xiDir ];then
            mkdir -p $prefix/$xiDir && mount --move /$xiDir $prefix/$xiDir
        fi
    fi
    #======================================
    # move live CD mount points to system
    #--------------------------------------
    local cdDir=/livecd
    if [ -d $cdDir ];then
        mkdir -p $prefix/$cdDir && mount --move /$cdDir $prefix/$cdDir
        if [ -d /cow ];then
            mkdir -p $prefix/cow && mount --move /cow $prefix/cow
        fi
        if [ -d /isofrom ];then
            mkdir -p $prefix/isofrom && mount --move /isofrom $prefix/isofrom
        fi
    fi
    #======================================
    # create dbus machine id
    #--------------------------------------
    if lookup dbus-uuidgen &>/dev/null;then
        dbus-uuidgen > $prefix/var/lib/dbus/machine-id
    fi
    #======================================
    # move device nodes
    #--------------------------------------
    Echo "Activating Image: [$name]"
    udevPending
    mkdir -p $prefix/run
    mkdir -p $prefix/dev
    mkdir -p $prefix/var/run
    mount --move /dev $prefix/dev
    if [[ ! $kiwi_iname =~ SLE.11 ]];then
        mount --move /run $prefix/run
        if [ ! -L $prefix/var/run ];then
            mount --move /var/run $prefix/var/run
        fi
    fi
    udevKill
    #======================================
    # run preinit stage
    #--------------------------------------
    Echo "Preparing preinit phase..."
    if ! cp /usr/bin/utimer $prefix;then
        systemException "Failed to copy: utimer" "reboot"
    fi
    if ! cp /iprocs $prefix;then
        systemException "Failed to copy: iprocs" "reboot"
    fi
    if ! cp /preinit $prefix;then
        systemException "Failed to copy: preinit" "reboot"
    fi
    if ! cp /include $prefix;then
        systemException "Failed to copy: include" "reboot"
    fi
    local killall5=$(lookup killall5)
    if [ ! -e $prefix/$killall5 ]; then
        touch $prefix/killall5.from-initrd
    fi
    if ! cp -f -a $killall5 $prefix/$killall5;then
        systemException "Failed to copy: killall5" "reboot"
    fi
    local pidof=$(lookup pidof)
    if [ ! -e $prefix/$pidof ];then
        touch $prefix/pidof.from-initrd
    fi
    if ! cp -f -a $pidof $prefix/$pidof;then
        systemException "Failed to copy: pidof" "reboot"
    fi
}
#======================================
# cleanImage
#--------------------------------------
function cleanImage {
    # /.../
    # remove preinit code from system image before
    # real init is called. this function runs already
    # inside the system root directory via chroot
    # ----
    local IFS=$IFS_ORIG
    local bootdir=boot_bind
    #======================================
    # setup logging in this mode
    #--------------------------------------
    exec 2>>$ELOG_FILE
    set -x
    #======================================
    # kill second utimer and tail
    #--------------------------------------
    . /iprocs
    kill $UTIMER_PID &>/dev/null
    #======================================
    # remove preinit code from system image
    #--------------------------------------
    rm -f /tmp/utimer
    rm -f /dev/utimer
    rm -f /utimer
    rm -f /iprocs
    rm -f /preinit
    rm -f /include
    rm -f /.kconfig
    rm -f /.profile
    rm -rf /image
    if [ -e /pidof.from-initrd ];then
        rm -f /pidof.from-initrd
        rm -f $(lookup pidof)
    fi
    if [ -e /killall5.from-initrd ];then
        rm -f /killall5.from-initrd
        rm -f $(lookup killall5)
    fi
    #======================================
    # return early for special types
    #--------------------------------------
    if \
        [ "$haveClicFS" = "yes" ] || \
        [ ! -z "$NFSROOT" ]       || \
        [ ! -z "$NBDROOT" ]       || \
        [ ! -z "$AOEROOT" ]       || \
        [ ! -z "$COMBINED_IMAGE" ]
    then
        return
    fi
    #======================================
    # return early for systemd
    #--------------------------------------
    if [ $init = "/bin/systemd" ];then
        return
    fi
    #======================================
    # umount LVM root parts
    #--------------------------------------
    local variable
    local volume
    local content
    local volpath
    local mpoint
    for i in $(cat /.profile | grep -E 'kiwi_LVM_|kiwi_allFreeVolume');do
        variable=$(echo $i|cut -f1 -d=)
        volume=$(echo $i| cut -f3- -d_ | cut -f1 -d=)
        content=$(echo $i|cut -f2 -d= | tr -d \' | tr -d \")
        volpath=$(echo $content | cut -f3 -d:)
        if [ -z "$volpath" ];then
            volpath=$(echo $volume | tr _ /)
        fi
        mpoint=$(echo $volpath | sed -e s@^LV@@)
        if \
            [ ! $volume = "LVRoot" ] && \
            [ ! $volume = "LVComp" ] && \
            [ ! $volume = "LVSwap" ]
        then
            umount /$mpoint 1>&2
        fi
    done
    #======================================
    # umount image boot partition if any
    #--------------------------------------
    if [ -e /$bootdir ];then
        umount /$bootdir 1>&2
    fi
    umount /boot 1>&2
    #======================================
    # turn off swap
    #--------------------------------------
    mount -t proc proc /proc
    swapoff -a   1>&2
    umount /proc 1>&2
}
#======================================
# bootImage
#--------------------------------------
function bootImage {
    # /.../
    # call the system image init process and therefore
    # boot into the operating system
    # ----
    local IFS=$IFS_ORIG
    local reboot=no
    local option=${kernel_cmdline[@]}
    local prefix=/mnt
    #======================================
    # Set active console to default font
    #--------------------------------------
    setupConsoleFont
    #======================================
    # check for init kernel option
    #--------------------------------------
    if [ -z "$init" ];then
        if [ -e $prefix/bin/systemd ];then
            export init=/bin/systemd
        else
            export init=/sbin/init
        fi
    fi
    #======================================
    # turn runlevel 4 to 5 if found
    #--------------------------------------
    option=$(echo $@ | sed -e s@4@5@)
    echo && Echo "Booting System: $option"
    #======================================
    # check for reboot request
    #--------------------------------------
    if [ "$LOCAL_BOOT" = "no" ];then
        if [ -z "$KIWI_RECOVERY" ];then
            if [ ! -z "$kiwi_oemreboot" ] || [ ! -z "$REBOOT_IMAGE" ];then
                reboot=yes
            fi
            if [ ! -z "$kiwi_oemrebootinteractive" ];then
                rebootinter=yes
            fi
            if [ ! -z "$kiwi_oemshutdown" ];then
                shutdown=yes
            fi
            if [ ! -z "$kiwi_oemshutdowninteractive" ];then
                shutdowninter=yes
            fi
        fi
    fi
    #======================================
    # run resetBootBind
    #--------------------------------------
    if [ -z "$NETBOOT_ONLY" ];then
        resetBootBind $prefix
    fi
    #======================================
    # setup warpclock for local time setup
    #--------------------------------------
    local warpclock=/lib/mkinitrd/bin/warpclock
    if [ -e $prefix/etc/localtime ] && [ -x $warpclock ];then
        cp $prefix/etc/localtime /etc
        if [ -e $prefix/etc/adjtime ];then
            cp $prefix/etc/adjtime /etc
            while read line;do
                if test "$line" = LOCAL
            then
                $warpclock > $prefix/dev/shm/warpclock
            fi
            done < /etc/adjtime
        elif [ -e $prefix/etc/sysconfig/clock ];then
            cp $prefix/etc/sysconfig/clock /etc
            . /etc/clock
            case "$HWCLOCK" in
                *-l*) $warpclock > $prefix/dev/shm/warpclock
            esac
        fi
    fi
    #======================================
    # kill initial tail and utimer
    #--------------------------------------
    . /iprocs
    kill $UTIMER_PID &>/dev/null
    #======================================
    # copy boot log file into system image
    #--------------------------------------
    mkdir -p $prefix/var/log
    rm -f $prefix/boot/mbrid
    if [ -e $prefix/dev/shm/initrd.msg ];then
        cp -f $prefix/dev/shm/initrd.msg $prefix/var/log/boot.msg
    fi
    if [ -e $ELOG_FILE ];then
        cp -f $ELOG_FILE $prefix/$ELOG_FILE
    fi
    if [ ! -d $prefix/var/log/ConsoleKit ];then
        mkdir -p $prefix/var/log/ConsoleKit
    fi
    #======================================
    # umount proc
    #--------------------------------------
    umount proc &>/dev/null && \
    umount proc &>/dev/null
    #======================================
    # copy initrd to /run/initramfs
    #--------------------------------------
    mkdir -p $prefix/run/initramfs
    match='mnt|lost\+found|dev|boot|tmp|run|proc|sys|read-only|read-write'
    for dir in /*;do
        if [[ $dir =~ $match ]]; then
            mkdir -p $prefix/run/initramfs/$dir
            continue
        fi
        cp -a $dir $prefix/run/initramfs
    done
    if [ "$FSTYPE" = "zfs" ];then
        #======================================
        # setup shutdown script
        #--------------------------------------
        local halt=$prefix/run/initramfs/shutdown
cat > $halt << EOF
#!/bin/sh
# if systemd is used this script is called after all
# services are terminated and mount points unmounted
# ---
ACTION="\$1"
EOF
        #======================================
        # shutdown: zfs -> export pool
        #--------------------------------------
        echo "zpool export kiwipool" >> $halt
        #======================================
        # shutdown: handle requested action
        #--------------------------------------
cat >> $halt << EOF
case "\$ACTION" in
    reboot)
        reboot -f -d
    ;;
    poweroff)
        reboot -f -d -p
    ;;
    halt)
        halt
    ;;
    kexec)
        kexec -e
    ;;
    *)
        reboot -f -d
    ;;
esac
EOF
    fi
    #======================================
    # run preinit and cleanImage
    #--------------------------------------
    chroot $prefix /bin/bash -c \
        "/preinit"
    chroot $prefix /bin/bash -c \
        ". /include ; exec 2>>$ELOG_FILE ; set -x ; cleanImage"
    cd $prefix
    #======================================
    # tell logging the new root fs
    #--------------------------------------
    exec 2>>$prefix/$ELOG_FILE
    set -x
    #======================================
    # tell plymouth the new root fs
    #--------------------------------------
    if lookup plymouthd &>/dev/null;then
        plymouth update-root-fs --new-root-dir=$prefix
        #======================================
        # stop if not installed in system image
        #--------------------------------------
        if [ ! -e $prefix/usr/bin/plymouth ];then
            plymouth quit
        fi
    fi
    #======================================
    # export root block device
    #--------------------------------------
    if [ -b "$imageRootDevice" ];then
        export ROOTFS_BLKDEV=$imageRootDevice
    fi
    #======================================
    # rootfs is clean, skip check
    #--------------------------------------
    export ROOTFS_FSCK="0"
    #======================================
    # stop dropbear ssh server
    #--------------------------------------
    if [ ! -z "$DROPBEAR_PID" ];then
        kill $DROPBEAR_PID
    fi
    #======================================
    # hand over control to init
    #--------------------------------------
    if [ $reboot = "yes" ];then
        Echo "Reboot requested... rebooting after preinit"
        exec chroot . /sbin/reboot -f -i
    fi
    if [ "$rebootinter" = "yes" ];then
        Echo "Reboot requested... rebooting after preinit"
        if [ "$OEMInstallType" = "CD" ];then
            TEXT_DUMP=$TEXT_CDPULL
        else
            TEXT_DUMP=$TEXT_USBPULL
        fi
        Dialog \
            --backtitle \"$TEXT_INSTALLTITLE\" \
            --msgbox "\"$TEXT_DUMP\"" 5 70
        clear
        Echo "Prepare for reboot"
        exec chroot . /sbin/reboot -f -i
    fi
    if [ "$shutdown" = "yes" ];then
        Echo "Shutdown  requested... system shutdown after preinit"
        exec chroot . /sbin/halt -fihp
    fi
    if [ "$shutdowninter" = "yes" ];then
        Echo "Shutdown  requested... system shutdown after preinit"
        if [ "$OEMInstallType" = "CD" ];then
            TEXT_DUMP=$TEXT_CDPULL_SDOWN
        else
            TEXT_DUMP=$TEXT_USBPULL_SDOWN
        fi
        Dialog \
            --backtitle \"$TEXT_INSTALLTITLE\" \
            --msgbox "\"$TEXT_DUMP\"" 5 70
        clear
        Echo "Prepare for shutdown"
        exec chroot . /sbin/halt -fihp
    fi
    if lookup switch_root &>/dev/null;then
        exec switch_root . $init $option
    else
        if lookup pivot_root &>/dev/null;then
            pivot_root . run/initramfs
        fi
        exec chroot . $init $option
    fi
}
#======================================
# setupUnionFS
#--------------------------------------
function setupUnionFS {
    # /.../
    # export the UNIONFS_CONFIG environment variable
    # which contains a three part coma separated list of the
    # following style: rwDevice,roDevice,unionType. The
    # devices are stores by disk ID if possible
    # ----
    local IFS=$IFS_ORIG
    local rwDevice=`getDiskID $1`
    local roDevice=`getDiskID $2`
    local unionFST=$3
    if [[ "$roDevice" =~ aoe|nbd ]]; then
        roDevice=$imageRootDevice
    fi
    if [ -e "$rwDevice" ]; then
        luksOpen $rwDevice luksReadWrite
        rwDeviceLuks=$luksDeviceOpened
    fi
    if [ -e "$roDevice" ]; then
        luksOpen $roDevice luksReadOnly
        roDeviceLuks=$luksDeviceOpened
    fi
    if [ ! -z "$rwDeviceLuks" ] && [ ! "$rwDeviceLuks" = "$rwDevice" ];then
        rwDevice=$rwDeviceLuks
        export haveLuks="yes"
    fi
    if [ ! -z "$roDeviceLuks" ] && [ ! "$roDeviceLuks" = "$roDevice" ];then
        roDevice=$roDeviceLuks
        export haveLuks="yes"
    fi
    if [ ! -z "$rwDevice" ] && [ ! -z "$roDevice" ];then
        export UNIONFS_CONFIG="$rwDevice,$roDevice,$unionFST"
    fi
}
#======================================
# canWrite
#--------------------------------------
function canWrite {
    # /.../
    # check if we can write to the given location
    # returns zero on success.
    # ---
    local IFS=$IFS_ORIG
    local prefix=$1
    if [ -z "$prefix" ];then
        prefix=/mnt
    fi
    if [ ! -d $prefix ];then
        return 1
    fi
    if touch $prefix/can-write &>/dev/null;then
        rm $prefix/can-write
        return 0
    fi
    return 1
}
#======================================
# xenServer
#--------------------------------------
function xenServer {
    # /.../
    # check if the given kernel is a xen kernel and if so
    # check if a dom0 or a domU setup was requested
    # ----
    local IFS=$IFS_ORIG
    local kname=$1
    local mountPrefix=$2
    local sysmap="$mountPrefix/boot/System.map-$kname"
    local isxen
    if [ ! -e $sysmap ]; then
        sysmap="$mountPrefix/boot/System.map"
    fi
    if [ ! -e $sysmap ]; then
        Echo "No system map for kernel $kname found"
        return 1
    fi
    isxen=$(grep -c "xen_base" $sysmap)
    if [ $isxen -eq 0 ]; then
        # not a xen kernel
        return 1
    fi
    if [ -z "$kiwi_xendomain" ];then
        # no xen domain set, assume domU
        return 1
    fi
    if [ $kiwi_xendomain = "dom0" ];then
        # xen dom0 requested
        return 0
    fi
    return 1
}
#======================================
# makeLabel
#--------------------------------------
function makeLabel {
    # /.../
    # create boot label and replace all spaces with
    # underscores. current bootloaders show the
    # underscore sign as as space in the boot menu
    # ---
    local IFS=$IFS_ORIG
    if \
        [ ! $loader = "syslinux" ] && \
        [ ! $loader = "extlinux" ] && \
        [ ! $loader = "grub2" ]
    then
        echo $1 | tr " " "_"
    else
        echo $1
    fi
}
#======================================
# waitForX
#--------------------------------------
function waitForX {
    # /.../
    # wait for the X-Server with PID $xserver_pid to
    # become read for client calls
    # ----
    local IFS=$IFS_ORIG
    local xserver_pid=$1
    local testx=/usr/sbin/testX
    local err=1
    while kill -0 $xserver_pid 2>/dev/null ; do
        sleep 1
        if test -e /tmp/.X11-unix/X0 && test -x $testx ; then
            $testx 16 2>/dev/null
            err=$?
            # exit code 1 -> XOpenDisplay failed...
            if test $err = 1;then
                Echo "TestX: XOpenDisplay failed"
                return 1
            fi
            # exit code 2 -> color or dimensions doesn't fit...
            if test $err = 2;then
                Echo "TestX: color or dimensions doesn't fit"
                kill $xserver_pid
                return 1
            fi
            # server is running, detach oom-killer from it
            echo -n '-17' > /proc/$xserver_pid/oom_adj
            return 0
        fi
    done
    return 1
}
#======================================
# startX
#--------------------------------------
function startX {
    # /.../
    # start X-Server and wait for it to become ready
    # ----
    local IFS=$IFS_ORIG
    export DISPLAY=:0
    local XServer=/usr/bin/Xorg
    if [ -x /usr/X11R6/bin/Xorg ];then
        XServer=/usr/X11R6/bin/Xorg
    fi
    $XServer -deferglyphs 16 vt07 &
    export XServerPID=$!
    if ! waitForX $XServerPID;then
        Echo "Failed to start X-Server"
        return 1
    fi
    return 0
}
#======================================
# stoppX
#--------------------------------------
function stoppX {
    local IFS=$IFS_ORIG
    if [ -z "$XServerPID" ];then
        return
    fi
    if kill -0 $XServerPID 2>/dev/null; then
        sleep 1 && kill $XServerPID
        while kill -0 $XServerPID 2>/dev/null; do
            sleep 1
        done
    fi
}
#======================================
# luksOpen
#--------------------------------------
function luksOpen {
    # /.../
    # check given device if it uses the LUKS extension
    # if yes open the device and return the new
    # /dev/mapper/ device name
    # ----
    local IFS=$IFS_ORIG
    local ldev=$1
    local name=$2
    local retry=1
    local info
    if [ -z "$ldev" ];then
        ldev=$(ddn $imageDiskDevice $kiwi_RootPart)
    fi
    #======================================
    # check device for luks extension
    #--------------------------------------
    if ! cryptsetup isLuks $ldev &>/dev/null;then
        return
    fi
    #======================================
    # no map name set, build it from device
    #--------------------------------------
    if [ -z "$name" ];then
        name=luks_$(basename "$ldev")
    fi
    #======================================
    # luks map already exists, return
    #--------------------------------------
    if [ -e /dev/mapper/$name ];then
        export luksDeviceOpened=/dev/mapper/$name
        return
    fi
    #======================================
    # ask for passphrase if not cached
    #--------------------------------------
    while true;do
        if [ -z "$luks_pass" ];then
            Echo "Try: $retry"
            errorLogStop
            luks_pass=$(runInteractive \
                "--insecure --passwordbox "\"$TEXT_LUKS\"" 10 60"
            )
            errorLogContinue
        fi
        if echo "$luks_pass" | cryptsetup luksOpen $ldev $name;then
            break
        fi
        unset luks_pass
        if [ -n "$luks_open_can_fail" ]; then
            unset luksDeviceOpened
            return 1
        fi
        if [ $retry -eq 3 ];then
            systemException \
                "Max retries reached... reboot" \
            "reboot"
        fi
        retry=$(($retry + 1))
    done
    #======================================
    # wait for the luks map to appear
    #--------------------------------------
    if ! waitForStorageDevice /dev/mapper/$name &>/dev/null;then
        systemException \
            "LUKS map /dev/mapper/$name doesn't appear... fatal !" \
        "reboot"
    fi
    #======================================
    # store luks device and return
    #--------------------------------------
    export luksDeviceOpened=/dev/mapper/$name
    return 0
}
#======================================
# luksResize
#--------------------------------------
function luksResize {
    # /.../
    # check if luksDeviceOpened is defined and
    # run cryptsetup resize on the mapper name
    # ----
    local IFS=$IFS_ORIG
    if [ ! -z "$luksDeviceOpened" ] && [ -e $luksDeviceOpened ];then
        cryptsetup resize $luksDeviceOpened
        udevPending
    fi
}
#======================================
# luksClose
#--------------------------------------
function luksClose {
    # /.../
    # close all open LUKS mappings
    # ----
    local IFS=$IFS_ORIG
    local name=$1
    #======================================
    # close specified name if set
    #--------------------------------------
    if [ -n "$1" ]; then
        name=$(basename $1)
        cryptsetup luksClose $name
        return
    fi
    #======================================
    # close all luks* map names
    #--------------------------------------
    for i in /dev/mapper/luks*;do
        name=$(basename "$i")
        cryptsetup luksClose $name
    done
}
#======================================
# importText
#--------------------------------------
function importText {
    # /.../
    # read in all texts from the catalog
    # ----
    local IFS=$IFS_ORIG
    export TEXT_TIMEOUT=$(
        getText "Boot continues in 10 sec...")
    export TEXT_OK=$(
        getText "OK")
    export TEXT_CANCEL=$(
        getText "Cancel")
    export TEXT_YES=$(
        getText "Yes")
    export TEXT_NO=$(
        getText "No")
    export TEXT_EXIT=$(
        getText "Exit")
    export TEXT_LUKS=$(
        getText "Enter LUKS passphrase")
    export TEXT_LICENSE=$(
        getText "Do you accept the license agreement ?")
    export TEXT_RESTORE=$(
        getText "Do you want to start the System-Restore ?")
    export TEXT_REPAIR=$(
        getText "Do you want to start the System-Recovery ?")
    export TEXT_RECOVERYTITLE=$(
        getText "Restoring base operating system...")
    export TEXT_INSTALLTITLE=$(
        getText "Installation...")
    export TEXT_CDPULL=$(
        getText "Please remove the CD/DVD before reboot")
    export TEXT_USBPULL=$(
        getText "Please unplug the USB stick before reboot")
    export TEXT_CDPULL_SDOWN=$(
        getText "Please remove the CD/DVD before shutdown")
    export TEXT_USBPULL_SDOWN=$(
        getText "System will be shutdown. Remove USB stick before power on")
    export TEXT_SELECT=$(
        getText "Select disk for installation:")
    export TEXT_BOOT_SETUP_FAILED=$(
        getText "Bootloader installation has failed")
    export TEXT_BOOT_SETUP_FAILED_INFO=$(
        getText "The system will not be able to reboot. Please make sure to fixup and install the bootloader before next reboot. Check $ELOG_FILE for details")
}
#======================================
# selectLanguage
#--------------------------------------
function selectLanguage {
    # /.../
    # select language if not yet done. The value is
    # used for all dialog windows with i18n support
    # ----
    local IFS=$IFS_ORIG
    local title="\"Select Language\""
    local list="en_US \"[ English ]\" on"
    local list_orig=$list
    local zh_CN=Chinese
    local zh_TW=Taiwanese
    local ru_RU=Russian
    local de_DE=German
    local ar_AR=Arabic
    local cs_CZ=Czech
    local el_GR=Greek
    local es_ES=Spanish
    local fi_FI=Finnish
    local fr_FR=French
    local hu_HU=Hungarian
    local it_IT=Italian
    local ja_JP=Japanese
    local ko_KR=Korean
    local nl_NL=Dutch
    local pl_PL=Polish
    local pt_BR=Portuguese
    local sv_SE=Swedish
    local tr_TR=Turkish
    local nb_NO=Norwegian
    local da_DK=Danish
    local pt_PT=Portuguese
    local en_GB=English
    local code
    local lang
    #======================================
    # Exports (Texts), default language
    #--------------------------------------
    importText
    #======================================
    # Check language environment
    #--------------------------------------
    if [ ! -z "$kiwi_oemunattended" ] && [ "$DIALOG_LANG" = "ask" ];then
        # answer the language question in unatteneded mode
        DIALOG_LANG=en_US
    fi
    if [ "$DIALOG_LANG" = "ask" ];then
        for code in $(echo $kiwi_language | tr "," " ");do
            if [ $code = "en_US" ];then
                continue
            fi
            eval lang=\$$code
            list="$list $code \"[ $lang ]\" off"
        done
        if [ "$list" = "$list_orig" ];then
            DIALOG_LANG=en_US
        else
            DIALOG_LANG=$(runInteractive \
                "--timeout 10 --no-cancel \
                 --backtitle \"$TEXT_TIMEOUT\" \
                 --radiolist $title 20 40 10 $list"
            )
        fi
    fi
    export LANG=$DIALOG_LANG.utf8
    #======================================
    # Exports (Texts), selected language
    #--------------------------------------
    importText
}
#======================================
# getText
#--------------------------------------
function getText {
    # /.../
    # return translated text
    # ----
    local IFS=$IFS_ORIG
    local text=$(gettext kiwi "$1")
    if [ ! -z "$2" ];then
        text=$(echo $text | sed -e s"@%1@$2@")
    fi
    if [ ! -z "$3" ];then
        text=$(echo $text | sed -e s"@%2@$3@")
    fi
    echo "$text"
}
#======================================
# displayEULA
#--------------------------------------
function displayEULA {
    # /.../
    # display in a dialog window the text part of the
    # selected language file(s). The files are searched
    # by the names in kiwi_showlicense
    # ----
    local IFS=$IFS_ORIG
    local code=$(echo $DIALOG_LANG | cut -f1 -d_)
    if [ -z "$kiwi_showlicense" ];then
        Echo "No license name(s) configured"
        return
    fi
    for name in $kiwi_showlicense;do
        #======================================
        # select license file by name
        #--------------------------------------
        code=/$name.$code.txt
        if [ ! -f $code ];then
            code=/$name.txt
        fi
        if [ ! -f $code ];then
            code=/etc/YaST2/licenses/base/$name.$code.txt
        fi
        if [ ! -f $code ];then
            code=/etc/YaST2/licenses/base/$name.txt
        fi
        if [ ! -f $code ];then
            code=/etc/YaST2/licenses/base/$name
        fi
        if [ ! -f $code ];then
            Echo "License with basename $name not found... skipped"
            continue
        fi
        #======================================
        # show license until accepted
        #--------------------------------------
        while true;do
            Dialog --textbox $code 20 70 \
                --and-widget --extra-button \
                --extra-label "$TEXT_NO" \
                --ok-label "$TEXT_YES" \
                --cancel-label "$TEXT_CANCEL" \
                --yesno "\"$TEXT_LICENSE\"" \
                5 45
            case $? in
                0 ) break
                    ;;
                1 ) continue
                    ;;
                * ) systemException \
                        "License not accepted... reboot" \
                    "reboot"
                    ;;
            esac
        done
    done
}
#======================================
# ddn
#--------------------------------------
function ddn {
    # /.../
    # print disk device name (node name) according to the
    # linux device node specs: If the last character of the
    # device is a letter, attach the partition number. If the
    # last character is a number, attach a 'p' and then the
    # partition number. Exceptions:
    # a) If the device name starts with /dev/disk
    #    the /dev/disk/<name>[-_]partN schema is used exclusively
    # b) If the device name starts with /dev/ram
    #    the /dev/mapper/<name>pN schema is used exclusively
    # c) If the device name starts with /dev/mapper
    #    the /dev/mapper/<name>_partN schema is checked optionally
    #    if it does not exist the default device node specs applies
    # ----
    local IFS=$IFS_ORIG
    if echo $1 | grep -q "^\/dev\/disk\/" ; then
        if [ -e $1"_part"$2 ]; then
            echo $1"_part"$2
            return
        fi
        echo $1"-part"$2
        return
    elif echo $1 | grep -q "^\/dev\/mapper\/" ; then
        if [ -e $1"_part"$2 ]; then
            echo $1"_part"$2
            return
        fi
    elif echo $1 | grep -q "^\/dev\/ram";then
        name=$(echo $1 | tr -d /dev)
        echo /dev/mapper/${name}p$2
        return
    fi
    local lastc=$(echo $1 | sed -e 's@\(^.*\)\(.$\)@\2@')
    if echo $lastc | grep -qP "^\d+$";then
        echo $1"p"$2
        return
    fi
    echo $1$2
}
#======================================
# dn
#--------------------------------------
function dn {
    # /.../
    # print disk name (device name) according to the
    # linux device node specs: If the device matches "p"
    # followed by a number remove pX else remove 
    # the last number. Exceptions:
    # loop devices
    # ----
    local IFS=$IFS_ORIG
    local part=$(getDiskDevice $1)
    if [[ $part =~ dev/loop[0-9] ]];then
        echo $part
        return
    fi
    if [[ $part =~ mapper/loop ]];then
        part=$(echo $part | sed -e s@/mapper@@)
    fi
    local part_new=$(echo $part | sed -e 's@\(^.*\)\(p[0-9].*$\)@\1@')
    if [ $part = $part_new ];then
        part_new=$(echo $part | sed -e 's@\(^.*\)\([0-9].*$\)@\1@')
    fi
    echo $part_new
}
#======================================
# nd
#--------------------------------------
function nd {
    # /.../
    # print the number of the disk device according to the
    # device node name. 
    # ----
    local IFS=$IFS_ORIG
    local part=$(getDiskDevice $1)
    local part_new=$(echo $part | sed -e 's@\(^.*\)p\([0-9].*$\)@\2@')
    if [ $part = $part_new ];then
        part_new=$(echo $part | sed -e 's@\(^.*\)\([0-9].*$\)@\2@')
    fi
    echo $part_new
}
#======================================
# runInteractive
#--------------------------------------
function runInteractive {
    # /.../
    # run dialog in a bash inside an fbiterm or directly
    # on the running terminal. Make the terminal the controlling
    # tty first. The output of the dialog call is stored in
    # a file and printed as result to this function
    # ----
    local IFS=$IFS_ORIG
    hideSplash
    local r=/tmp/rid
    local code
    echo "dialog $@ 2> /tmp/out" > $r
    echo "echo -n \$? > /tmp/out.exit" >> $r
    if FBOK;then
        setctsid $ELOG_EXCEPTION fbiterm -m $UFONT -- bash -i $r
    else
        setctsid $ELOG_EXCEPTION bash -i $r
    fi
    code=$(cat /tmp/out.exit)
    if [ ! $code = 0 ];then
        return $code
    fi
    cat /tmp/out && rm -f /tmp/out* $r
    return 0
}
#======================================
# createCustomHybridPersistent
#--------------------------------------
function createCustomHybridPersistent {
    # /.../
    # import the write space for the hybrid according to
    # the information given by kiwi_cowdevice and kiwi_cowsystem
    # ----
    local IFS=$IFS_ORIG
    #======================================
    # check for custom cow location
    #--------------------------------------
    if [ -z "$kiwi_cowdevice" ];then
        return
    fi
    if [ -z "$kiwi_cowsystem" ];then
        return
    fi
    Echo "Using custom cow file: $kiwi_cowdevice:$kiwi_cowsystem"
    #======================================
    # got custom cow location
    #--------------------------------------
    waitForStorageDevice $kiwi_cowdevice
    #======================================
    # mount cow device
    #--------------------------------------
    mkdir /cow
    if ! mount $kiwi_cowdevice /cow;then
        systemException \
            "Failed to mount cow device !" \
        "reboot"
    fi
    #======================================
    # does the cow file exist
    #--------------------------------------
    if [ ! -f /cow/$kiwi_cowsystem ];then
        Echo "Can't find cow file on write partition... deactivated"
        unset kiwi_hybridpersistent
        umount /cow
        rmdir  /cow
        return
    fi
    #======================================
    # loop setup cow space
    #--------------------------------------
    kiwi_cowdevice=$(loop_setup /cow/$kiwi_cowsystem)
    if [ ! -e $kiwi_cowdevice ];then
        systemException \
            "Failed to loop setup cow file !" \
        "reboot"
    fi
    #======================================
    # export read-write device name
    #--------------------------------------
    export skipSetupBootPartition=1
    export HYBRID_RW=$kiwi_cowdevice
}
#======================================
# createHybridPersistent
#--------------------------------------
function createHybridPersistent {
    # /.../
    # create a new partition to handle the copy-on-write actions
    # by the clicfs live mount. A new partition with a filesystem
    # inside labeled as 'hybrid' is created for this purpose
    # ----
    local IFS=$IFS_ORIG
    local device=$1
    local input=/part.input
    local pID
    rm -f $input
    #======================================
    # check for custom cow location
    #--------------------------------------
    if [ ! -z "$kiwi_cowdevice" ] || [ ! -z "$kiwi_cowsystem" ];then
        return
    fi
    #======================================
    # check persistent write partition
    #--------------------------------------
    local hybrid_fs=$HYBRID_PERSISTENT_FS
    if [ ! -z "$kiwi_hybridpersistent_filesystem" ];then
        hybrid_fs=$kiwi_hybridpersistent_filesystem
    fi
    for pID in 4 3 2 1;do
        local partd=$(ddn $device $pID)
        local label=$(blkid $partd -s LABEL -o value)
        if [ "$label" = "hybrid" ];then
            Echo "Existing persistent hybrid partition found"
            if [ $hybrid_fs = "fat" ];then
                if ! setupHybridCowDevice;then
                    Echo "Failed to setup hybrid cow device"
                    Echo "Persistent writing deactivated"
                    unset kiwi_hybridpersistent
                    return
                fi
            else
                export HYBRID_RW=$partd
            fi
            export skipSetupBootPartition=1
            return
        fi
    done
    #======================================
    # create persistent write partition
    #--------------------------------------
    Echo "Creating hybrid persistent partition for COW data"
    export imageDiskDevice=$device
    if [ ! -e "$imageDiskDevice" ];then
        Echo "Disk device $device does not exist, most likely not a disk"
        Echo "Persistent writing deactivated"
        unset kiwi_hybridpersistent
        return
    fi
    # Find partition ID we could use to create a new write partition
    for pID in 1 2 3 4;do
        local partd=$(ddn $device $pID)
        if [ ! -e "$partd" ];then
            Echo "Creating write partition at ID: $pID"
            break
        fi
    done
    if [ "$kiwi_firmware" = "bios" ];then
        # we support creation of partitions which are not in ascending order
        # in bios mode. The partition table created via isohybrid starts at
        # the second partition to allow the creation of the write partition
        # as first partition. Reason for this is to support Windows systems
        # with a fat partition as write space which has to be the first
        # partition otherwise Windows can't cope with it.
        #
        # Such a write partition can be created using fdisk, however for
        # EFI capable hybrid ISO images the GPT table is used which fdisk
        # can't handle.
        #
        # Therefore we use fdisk for bios firmware images and parted for
        # efi|uefi firmware images.
        #
        # This also means we don't support fat
        # based persistent write partitions to be created as first partition
        # on efi|uefi ISO hybrid images
        echo -e "n\np\n$pID\n\n\nw\nq" | fdisk $imageDiskDevice
    else
        createPartitionerInput \
            n p:lxrw $pID . . t $pID $HYBRID_PERSISTENT_ID
        callPartitioner $input
    fi
    #======================================
    # check partition device node
    #--------------------------------------
    if [ $partitionerWriteStatus != 0 ];then
        Echo "Partition creation failed for device $device"
        Echo "Persistent writing deactivated"
        unset kiwi_hybridpersistent
        return
    fi
    if ! waitForStorageDevice $(ddn $device $pID);then
        Echo "Partition $pID on $device doesn't appear... fatal !"
        Echo "Persistent writing deactivated"
        unset kiwi_hybridpersistent
        return
    fi
    #======================================
    # create filesystem on write partition
    #--------------------------------------
    local hybrid_device=$(ddn $device $pID)
    local exception_handling="false"
    if ! createFilesystem \
        $hybrid_device "" "" "hybrid" $exception_handling $hybrid_fs
    then
        Echo "Failed to create hybrid persistent filesystem"
        Echo "Persistent writing deactivated"
        unset kiwi_hybridpersistent
        return
    fi
    #======================================
    # export read-write device name
    #--------------------------------------
    if [ $hybrid_fs = "fat" ];then
        # The fat filesystem is not really suitable to be used as rootfs
        # for linux. Therefore we create a btrfs based file which we store
        # on the fat filesystem and loop setup it. The size of the file
        # is set to half the size of the fat device
        if ! setupHybridCowDevice $hybrid_device;then
            Echo "Failed to setup hybrid cow device"
            Echo "Persistent writing deactivated"
            unset kiwi_hybridpersistent
            return
        fi
    else
        export HYBRID_RW=$(ddn $device $pID)
    fi
    #======================================
    # skip boot partition setup on overlay
    #--------------------------------------
    export skipSetupBootPartition=1
}
#======================================
# setupHybridCowDevice
#--------------------------------------
function setupHybridCowDevice {
    local IFS=$IFS_ORIG
    local hybrid_device=$1
    mkdir -p /cow
    for i in 1 2 3;do
        mount -L hybrid /cow && break || sleep 2
    done
    if [ ! $? = 0 ];then
        Echo "Failed to mount hybrid persistent filesystem !"
        return 1
    fi
    if [ ! -e "/cow/cowfile" ];then
        local cowsize=$(($(blockdev --getsize64 $hybrid_device) / 2))
        local exception_handling="false"
        qemu-img create /cow/cowfile $cowsize
        if ! createFilesystem \
            "/cow/cowfile" "" "" "" $exception_handling "btrfs"
        then
            Echo "Failed to create hybrid persistent cow filesystem"
            return 1
        fi
    fi
    export HYBRID_RW=$(loop_setup /cow/cowfile)
    if [ ! -e "$cowdevice" ];then
        Echo "Failed to loop setup hybrid cow file !"
        return 1
    fi
    return 0
}
#======================================
# callPartitioner
#--------------------------------------
function callPartitioner {
    local IFS=$IFS_ORIG
    local input=$1
    if [ $PARTITIONER = "fdasd" ];then
        Echo "Partition the disk according to real geometry [ fdasd ]"
        echo "w" >> $input
        echo "q" >> $input
        fdasd $imageDiskDevice < $input 1>&2
        export partitionerWriteStatus=$?
        if test $partitionerWriteStatus != 0; then
            systemException "Failed to create partition table" "reboot"
        fi
        udevPending
        blockdev --rereadpt $imageDiskDevice
    else
        # /.../
        # nothing to do for parted here as we write
        # imediately with parted and don't create a
        # command input file as for fdasd but we re-read
        # the disk so that the new table will be used
        # ----
        udevPending
        blockdev --rereadpt $imageDiskDevice
    fi
}
#======================================
# createPartitionerInput
#--------------------------------------
function createPartitionerInput {
    local IFS=$IFS_ORIG
    if isDASDDevice; then
        PARTITIONER=fdasd
    fi
    if [ $PARTITIONER = "fdasd" ];then
        createFDasdInput $@
    else
        updatePartitionTable $imageDiskDevice
        Echo "Partition the disk according to real geometry [ parted ]"
        partedInit $imageDiskDevice
        partedSectorInit $imageDiskDevice
        createPartedInput $imageDiskDevice $@
    fi
}
#======================================
# createFDasdInput
#--------------------------------------
function createFDasdInput {
    local IFS=$IFS_ORIG
    local input=/part.input
    local ignore_once=0
    local ignore=0
    normalizeRepartInput $*
    for cmd in ${pcmds[*]};do
        if [ $ignore = 1 ] && echo $cmd | grep -qE '[dntwq]';then
            ignore=0
        elif [ $ignore = 1 ];then
            continue
        fi
        if [ $ignore_once = "1" ];then
            ignore_once=0
            continue
        fi
        if [ $cmd = "a" ];then
            ignore=1
            continue
        fi
        if [[ $cmd =~ ^p: ]];then
            ignore_once=1
            continue
        fi
        if [ $cmd = "83" ] || [ $cmd = "8e" ];then
            cmd=1
        fi
        if [ $cmd = "82" ];then
            cmd=2
        fi
        if [ $cmd = "." ];then
            echo >> $input
            continue
        fi
        echo $cmd >> $input
    done
}
#======================================
# partedInit
#--------------------------------------
function partedInit {
    # /.../
    # initialize current partition table output
    # as well as the number of cylinders and the
    # cyliner size in kB for this disk
    # ----
    local IFS=$IFS_ORIG
    local devname=$1
    local device=$(getDiskDevice $devname)
    IFS=""
    local parted=$(parted -m -s $device unit cyl print | grep -v Warning:)
    local header=$(echo $parted | head -n 3 | tail -n 1)
    local ccount=$(echo $parted | grep ^$device | cut -f 2 -d: | tr -d cyl)
    local cksize=$(echo $header | cut -f4 -d: | cut -f1 -dk)
    local diskhd=$(echo $parted | head -n 3 | tail -n 2 | head -n 1)
    local plabel=$(echo $diskhd | cut -f6 -d:)
    if [[ $plabel =~ gpt ]];then
        plabel=gpt
    fi
    export partedTableType=$plabel
    export partedOutput=$parted
    export partedCylCount=$ccount
    export partedCylKSize=$cksize
}
#======================================
# partedWrite
#--------------------------------------
function partedWrite {
    # /.../
    # call parted with current command queue.
    # This will immediately change the partition table
    # ----
    local IFS=$IFS_ORIG
    local device=$1
    local cmds=$2
    local opts
    if [ $PARTED_HAVE_ALIGN -eq 1 ];then
        opts="-a cyl"
    fi
    parted $opts -m -s $device unit cyl $cmds
    export partitionerWriteStatus=$?
    if [ $partitionerWriteStatus != 0 ];then
        if [ ! -z "$kiwi_hybridpersistent" ];then
            # /.../
            # in case of a iso hybrid table don't stop with a fatal reboot
            # exception on error. In this case we want to proceed with the
            # boot process but deactivate the persistent write feature
            # ----
            return 1
        fi
        systemException "Failed to create partition table" "reboot"
    fi
    partedInit $device
}
#======================================
# partedSectorInit
#--------------------------------------
function partedSectorInit {
    # /.../
    # return aligned start/end sectors of current table.
    # ----
    local IFS=$IFS_ORIG
    local disk=$1
    local s_start
    local s_stopp
    unset startSectors
    unset endSectors
    local align=$((kiwi_align / kiwi_sectorsize))
    for i in $(
        parted -m -s $disk unit s print |\
        grep -E ^[1-9]+:| cut -f2-3 -d: | tr -d s
    );do
        s_start=$(echo $i | cut -f1 -d:)
        s_stopp=$(echo $i | cut -f2 -d:)
        if [ -z "$startSectors" ];then
            startSectors=${s_start}s
        else
            startSectors=${startSectors}:${s_start}s
        fi
        if [ -z "$endSectors" ];then
            endSectors=$((s_stopp/align*align+align))s
        else
            endSectors=$endSectors:$((s_stopp/align*align+align))s
        fi
    done
    # /.../
    # in case of an empty disk we use the default start sector
    # ----
    if [ -z "$startSectors" ];then
        startSectors=${kiwi_startsector}s
    fi
}
#======================================
# partedEndCylinder
#--------------------------------------
function partedEndCylinder {
    # /.../
    # return end cylinder of given partition, next
    # partition must start at return value plus 1
    # ----
    local IFS=$IFS_ORIG
    local part=$(($1 + 3))
    IFS=""
    local header=$(echo $partedOutput | head -n $part | tail -n 1)
    local ccount=$(echo $header | cut -f3 -d: | tr -d cyl)
    echo $ccount
}
#======================================
# partedMBToCylinder
#--------------------------------------
function partedMBToCylinder {
    # /.../
    # convert size given in MB to cylinder count
    # ----
    local IFS=$IFS_ORIG
    local sizeBytes=$(($1 * 1048576))
    local cylreq=$(echo "scale=0; $sizeBytes / ($partedCylKSize * 1000)" | bc)
    echo $cylreq
}
#======================================
# createPartedInput
#--------------------------------------
function createPartedInput {
    # /.../
    # evaluate partition instructions and turn them
    # into a parted command line queue. As soon as the
    # geometry data would be changed according to the
    # last partedInit() call the command queue is processed
    # and the partedInit() will be called afterwards
    # ----
    local IFS=$IFS_ORIG
    local disk=$1
    shift
    local index=0
    local partid
    local partnm
    local pstart
    local pstopp
    local value
    local cmdq
    #======================================
    # normalize commands
    #--------------------------------------
    normalizeRepartInput $*
    for cmd in ${pcmds[*]};do
        case $cmd in
            #======================================
            # delete partition
            #--------------------------------------
            "d")
                partid=${pcmds[$index + 1]}
                partid=$(($partid / 1))
                cmdq="$cmdq rm $partid"
                partedWrite "$disk" "$cmdq"
                cmdq=""
                ;;
            #======================================
            # create new partition
            #--------------------------------------
            "n")
                partnm=${pcmds[$index + 1]}
                partid=${pcmds[$index + 2]}
                partid=$(($partid / 1))
                pstart=${pcmds[$index + 3]}
                if [ ! "$partedTableType" = "gpt" ];then
                    partnm=primary
                else
                    partnm=$(echo $partnm | cut -f2 -d:)
                fi
                if [ "$pstart" = "1" ];then
                    pstart=$(echo $startSectors | cut -f $partid -d:)
                fi
                if [ $pstart = "." ];then
                    # start is next sector according to previous partition
                    pstart=$(($partid - 1))
                    if [ $pstart -gt 0 ];then
                        pstart=$(echo $endSectors | cut -f $pstart -d:)
                    else
                        pstart=$(echo $startSectors | cut -f $partid -d:)
                    fi
                fi
                pstopp=${pcmds[$index + 4]}
                if [ $pstopp = "." ];then
                    # use rest of the disk for partition end
                    pstopp=$partedCylCount
                elif echo $pstopp | grep -qi M;then
                    # calculate stopp cylinder from size
                    pstopp=$(($partid - 1))
                    if [ $pstopp -gt 0 ];then
                        pstopp=$(partedEndCylinder $pstopp)
                    fi
                    value=$(echo ${pcmds[$index + 4]} | cut -f1 -dM | tr -d +)
                    value=$(partedMBToCylinder $value)
                    pstopp=$((1 + $pstopp + $value))
                    if [ $pstopp -gt $partedCylCount ];then
                        # given size is out of bounds, reduce to end of disk
                        pstopp=$partedCylCount
                    fi
                fi
                cmdq="$cmdq mkpart $partnm $pstart $pstopp"
                partedWrite "$disk" "$cmdq"
                partedSectorInit $imageDiskDevice
                cmdq=""
                ;;
            #======================================
            # change partition ID
            #--------------------------------------
            "t")
                ptypex=${pcmds[$index + 2]}
                partid=${pcmds[$index + 1]}
                flagok=1
                if [ "$ptypex" = "82" ];then
                    if [[ $kiwi_iname =~ boot-suse ]];then
                        # /.../
                        # suse parted is not able to set swap flag. I consider
                        # this as a bug in the suse parted tool. In order to
                        # proceed here kiwi uses suse parted 'type' command
                        # extension.
                        #
                        cmdq="$cmdq set $partid type 0x$ptypex"
                    elif [[ $kiwi_iname =~ boot-rhel ]];then
                        # /.../
                        # parted on RHEL is not able to set swap flag. I don't
                        # have a good solution for this thus we skip the flag
                        # setup in this case
                        #
                        flagok=0
                    else
                        cmdq="$cmdq set $partid swap on"
                    fi
                elif [ "$ptypex" = "fd" ];then
                    cmdq="$cmdq set $partid raid on"
                elif [ "$ptypex" = "8e" ];then
                    cmdq="$cmdq set $partid lvm on"
                elif [ "$ptypex" = "83" ];then
                    # default partition type set by parted is linux(83)
                    flagok=0
                else
                    # be careful, this is a suse parted extension
                    cmdq="$cmdq set $partid type 0x$ptypex"
                fi
                if [ ! "$partedTableType" = "gpt" ] && [ $flagok = 1 ];then
                    partedWrite "$disk" "$cmdq"
                fi
                cmdq=""
                ;;
        esac
        index=$(($index + 1))
    done
}
#======================================
# normalizeRepartInput
#--------------------------------------
function normalizeRepartInput {
    local IFS=$IFS_ORIG
    local pcmds_fix
    local index=0
    local index_fix=0
    local partid
    local cmd
    #======================================
    # create list of commands
    #--------------------------------------
    unset pcmds
    for cmd in $*;do
        pcmds[$index]=$cmd
        index=$(($index + 1))
    done
    index=0
    #======================================
    # fix list of commands
    #--------------------------------------
    while [ ! -z "${pcmds[$index]}" ];do
        cmd=${pcmds[$index]}
        pcmds_fix[$index_fix]=$cmd
        case $cmd in
            "d")
                partid=${pcmds[$index + 1]}
                if ! echo $partid | grep -q -E "^[0-9]+$";then
                    # make sure there is a ID set for the deletion
                    index_fix=$(($index_fix + 1))
                    pcmds_fix[$index_fix]=1
                fi
            ;;
            "n")
                partid=${pcmds[$index + 2]}
                if [ ! "$PARTITIONER" = "fdasd" ];then
                    if ! echo $partid | grep -q -E "^[0-9]+$";then
                        # make sure there is a ID set for the creation
                        index_fix=$(($index_fix + 1))
                        pcmds_fix[$index_fix]=${pcmds[$index + 1]}
                        index_fix=$(($index_fix + 1))
                        pcmds_fix[$index_fix]=4
                        index=$(($index + 1))
                    fi
                fi
            ;;
            "t")
                partid=${pcmds[$index + 1]}
                if ! echo $partid | grep -q -E "^[0-9]+$";then
                    # make sure there is a ID set for the type
                    index_fix=$(($index_fix + 1))
                    pcmds_fix[$index_fix]=1
                fi
            ;;
        esac
        index=$(($index + 1))
        index_fix=$(($index_fix + 1))
    done
    #======================================
    # use fixed list and print log info
    #--------------------------------------
    unset pcmds
    pcmds=(${pcmds_fix[*]})
    unset pcmds_fix
    echo "Normalized Repartition input: ${pcmds[*]}" 1>&2
}
#======================================
# reloadKernel
#--------------------------------------
function reloadKernel {
    # /.../
    # reload the given kernel and initrd. This function
    # checks USB stick devices for a kernel and initrd
    # and shows them in a dialog window. The selected kernel
    # and initrd is loaded via kexec.
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    #======================================
    # check proc/cmdline
    #--------------------------------------
    ldconfig
    mountSystemFilesystems &>/dev/null
    if ! cat /proc/cmdline | grep -qi "hotfix=1";then
        umountSystemFilesystems
        return
    fi
    #======================================
    # check for kexec
    #--------------------------------------
    if [ ! -x /sbin/kexec ];then
        systemException "Can't find kexec" "reboot"
    fi
    #======================================
    # start udev
    #--------------------------------------
    touch /etc/modules.conf
    touch /lib/modules/*/modules.dep
    udevStart
    errorLogStart
    probeDevices
    #======================================
    # search hotfix stick
    #--------------------------------------
    USBStickDevice kexec
    if [ $stickFound = 0 ];then
        systemException "No hotfix USB stick found" "reboot"
    fi
    #======================================
    # mount stick
    #--------------------------------------
    if ! mount -o ro $stickDevice $prefix;then
        systemException "Failed to mount hotfix stick" "reboot"
    fi
    #======================================
    # load kernel
    #--------------------------------------
    kexec -l $prefix/linux.kexec --initrd=$prefix/initrd.kexec \
        --append="$(cat /proc/cmdline | sed -e s"@hotfix=1@@")"
    if [ ! $? = 0 ];then
        systemException "Failed to load hotfix kernel" "reboot"
    fi
    #======================================
    # go for gold
    #--------------------------------------
    exec kexec -e
}
#======================================
# resizeFilesystem
#--------------------------------------
function resizeFilesystem {
    local IFS=$IFS_ORIG
    local deviceResize=$1
    local callme=$2
    local ramdisk=0
    local resize_fs
    local check
    local mpoint=/fs-resize
    udevPending
    mkdir -p $mpoint
    if echo $deviceResize | grep -qi "/dev/ram";then
        ramdisk=1
    fi
    if [ -z "$FSTYPE" ];then
        probeFileSystem $deviceResize
    fi
    if [ "$FSTYPE" = "reiserfs" ];then
        resize_fs="resize_reiserfs -q $deviceResize"
        check="reiserfsck -y $deviceResize"
    elif [ "$FSTYPE" = "ext2" ];then
        resize_fs="resize2fs -f -F -p $deviceResize"
        check="e2fsck -p $deviceResize"
        if [ $ramdisk -eq 1 ];then
            resize_fs="resize2fs -f $deviceResize"
        fi
    elif [ "$FSTYPE" = "ext3" ];then
        resize_fs="resize2fs -f -F -p $deviceResize"
        check="e2fsck -p $deviceResize"
        if [ $ramdisk -eq 1 ];then
            resize_fs="resize2fs -f $deviceResize"
        fi
    elif [ "$FSTYPE" = "ext4" ];then
        resize_fs="resize2fs -f -F -p $deviceResize"
        check="e2fsck -p $deviceResize"
        if [ $ramdisk -eq 1 ];then
            resize_fs="resize2fs -f $deviceResize"
        fi
    elif [ "$FSTYPE" = "btrfs" ];then
        resize_fs="mount $deviceResize $mpoint &&"
        if lookup btrfs &>/dev/null;then
            resize_fs="$resize_fs btrfs filesystem resize max $mpoint"
            resize_fs="$resize_fs;umount $mpoint"
        else
            resize_fs="$resize_fs btrfsctl -r max $mpoint;umount $mpoint"
        fi
        check="btrfsck $deviceResize"
    elif [ "$FSTYPE" = "xfs" ];then
        resize_fs="mount $deviceResize $mpoint &&"
        resize_fs="$resize_fs xfs_growfs $mpoint;umount $mpoint"
        check="xfs_repair -n $deviceResize"
    elif [ "$FSTYPE" = "zfs" ];then
        local device=$(getDiskID $deviceResize)
        resize_fs="zpool import kiwipool && udevPending &&"
        resize_fs="$resize_fs zpool online -e kiwipool $device;"
        resize_fs="$resize_fs zpool export kiwipool"
    else
        # don't know how to resize this filesystem
        Echo "Don't know how to resize ${FSTYPE}... skip it"
        return
    fi
    if [ -z "$callme" ];then
        if [ $ramdisk -eq 0 ] && [ ! -z "$check" ];then
            Echo "Checking $FSTYPE filesystem on ${deviceResize}..."
            eval $check
        fi
        Echo "Resizing $FSTYPE filesystem on ${deviceResize}..."
        eval $resize_fs
        if [ ! $? = 0 ];then
            systemException \
                "Failed to resize/check filesystem" \
            "reboot"
        fi
    else
        echo $resize_fs
    fi
}
#======================================
# resetMountCounter
#--------------------------------------
function resetMountCounter {
    local IFS=$IFS_ORIG
    local curtype=$FSTYPE
    local command
    for device in \
        $imageRootDevice $imageBootDevice \
        $imageRecoveryDevice
    do
        if [ ! -e $device ];then
            continue
        fi
        probeFileSystem $device
        if [ "$FSTYPE" = "ext2" ];then
            command="tune2fs -c -1 -i 0"
        elif [ "$FSTYPE" = "ext3" ];then
            command="tune2fs -c -1 -i 0"
        elif [ "$FSTYPE" = "ext4" ];then
            command="tune2fs -c -1 -i 0"
        else
            # nothing to do here...
            continue
        fi
        eval $command $device 1>&2
    done
    FSTYPE=$curtype
}
#======================================
# createFilesystem
#--------------------------------------
function createFilesystem {
    local IFS=$IFS_ORIG
    local deviceCreate=$1
    local blocks=$2
    local uuid=$3
    local label=$4
    local exception_handling=$5
    local filesystem=$6
    local opts=$7
    if [ -z "$filesystem" ];then
        filesystem=$FSTYPE
    fi
    if [ -z "$exception_handling" ];then
        exception_handling="true"
    else
        exception_handling="false"
    fi
    if [[ "$filesystem" =~ ext ]];then
        opts="$opts -F"
        if [ ! -z "$uuid" ];then
            opts="$opts -U $uuid"
        fi
        if [ ! -z "$label" ];then
            opts="$opts -L $label"
        fi
    elif [ "$filesystem" = "reiserfs" ];then
        opts="$opts -f"
        if [ ! -z "$uuid" ];then
            opts="$opts -d $uuid"
        fi
        if [ ! -z "$label" ];then
            opts="$opts -l $label"
        fi
    elif [ "$filesystem" = "btrfs" ];then
        opts="$opts -f"
        if [ ! -z "$uuid" ];then
            opts="$opts -U $uuid"
        fi
        if [ ! -z "$label" ];then
            opts="$opts -L $label"
        fi
        if [ ! -z "$blocks" ];then
            local bytes=$((blocks * 4096))
            opts="$opts -b $bytes"
        fi
    elif [ "$filesystem" = "fat" ];then
        if [ ! -z "$label" ];then
            opts="$opts -n $label"
        fi
    elif [ "$filesystem" = "ntfs" ];then
        if [ ! -z "$label" ];then
            opts="$opts -L $label"
        fi
    fi
    if [ "$filesystem" = "reiserfs" ];then
        mkreiserfs $opts $deviceCreate $blocks 1>&2
    elif [ "$filesystem" = "ext2" ];then
        mkfs.ext2 $opts $deviceCreate $blocks 1>&2
    elif [ "$filesystem" = "ext3" ];then
        mkfs.ext3 $opts $deviceCreate $blocks 1>&2
    elif [ "$filesystem" = "ext4" ];then
        mkfs.ext4 $opts $deviceCreate $blocks 1>&2
    elif [ "$filesystem" = "btrfs" ];then
        # delete potentially existing btrfs on the device because even
        # with the force option enabled mkfs.btrfs refuses to create a
        # filesystem if the existing metadata contains the same UUID
        dd if=/dev/zero of=$deviceCreate bs=1M count=1 conv=notrunc
        mkfs.btrfs $opts $deviceCreate
    elif [ "$filesystem" = "xfs" ];then
        mkfs.xfs -f $deviceCreate
        xfs_admin -U $uuid $deviceCreate
    elif [ "$filesystem" = "fat" ];then
        mkfs.fat $opts $deviceCreate $blocks 1>&2
    elif [ "$filesystem" = "ntfs" ];then
        mkfs.ntfs $opts $deviceCreate $blocks 1>&2
    else
        # use ext3 by default
        mkfs.ext3 $opts $deviceCreate $blocks 1>&2
    fi
    if [ $exception_handling = "false" ];then
        return $?
    fi
    if [ ! $? = 0 ];then
        systemException \
            "Failed to create filesystem" \
        "reboot"
    fi
}
#======================================
# restoreBtrfsSubVolumes
#--------------------------------------
function restoreBtrfsSubVolumes {
    local IFS=$IFS_ORIG
    local root=$1
    local variable
    local volume
    local content
    local volpath
    local mpoint
    local mppath
    local volbase
    btrfs subvolume create $root/@ || return
    local rootid=$(btrfs subvolume list $root | cut -f2 -d ' ')
    btrfs subvolume set-default $rootid $root || return
    for i in $(cat /.profile | grep -E 'kiwi_LVM_|kiwi_allFreeVolume');do
        variable=$(echo $i|cut -f1 -d=)
        volume=$(echo $i| cut -f3- -d_ | cut -f1 -d=)
        content=$(echo $i|cut -f2 -d= | tr -d \' | tr -d \")
        volpath=$(echo $content | cut -f3 -d:)
        if [ -z "$volpath" ];then
            volpath=$(echo $volume | tr _ /)
        fi
        mpoint=$(echo $volpath | sed -e s@^LV@@)
        volbase="$root/@/$(dirname $mpoint)"
        if [ ! -d $volbase ];then
            mkdir -p $volbase
        fi
        btrfs subvolume create $root/@/$mpoint || return
    done
    umount $root && mount $imageRootDevice $root
}
#======================================
# restoreLVMMetadata
#--------------------------------------
function restoreLVMPhysicalVolumes {
    # /.../
    # restore the pysical volumes by the given restore file
    # created from vgcfgbackup. It's important to create them
    # with the same uuid's compared to the restore file
    # ----
    local IFS=$IFS_ORIG
    local restorefile=$1
    cat $restorefile | grep -A2 -E 'pv[0-9] {' | while read line;do
        if [ -z "$uuid" ];then
            uuid=$(echo $line | grep 'id =' |\
                cut -f2 -d= | tr -d \")
        fi
        if [ -z "$pdev" ];then
            pdev=$(echo $line|grep 'device =' |\
                cut -f2 -d\" | cut -f1 -d\")
        fi
        if [ ! -z "$pdev" ];then
            pvcreate -u $uuid $pdev
            unset uuid
            unset pdev
        fi
    done
}
#======================================
# pxeCheckServer
#--------------------------------------
function pxeCheckServer {
    # /.../
    # check the kernel commandline parameter kiwiserver.
    # If it exists its contents will be used as
    # server address stored in the SERVER variabe
    # ----
    local IFS=$IFS_ORIG
    if [ ! -z $kiwiserver ];then
        Echo "Found server in kernel cmdline"
        SERVER=$kiwiserver
    fi
    if [ ! -z $kiwiservertype ]; then
        Echo "Found server type in kernel cmdline"
        SERVERTYPE=$kiwiservertype
    else
        SERVERTYPE=tftp
    fi
}
#======================================
# pxeSetupDownloadServer
#--------------------------------------
function pxeSetupDownloadServer {
    # /.../
    # the pxe image system requires a server which stores
    # the image files. This function setup the SERVER variable
    # pointing to that server using the following heuristic:
    # ----
    # 1) check for $kiwiserver from cmdline
    # 2) try tftp.$DOMAIN whereas $DOMAIN is from dhcpcd-info
    # 3) try address of DHCP server if no servertype or tftp is used
    # 4) fail if no location was found
    # ----
    local IFS=$IFS_ORIG
    pxeCheckServer
    if [ -z "$SERVER" ];then
        if [ ! -z "$ip" ];then
            Echo "Found PXE download server IP in kernel cmdline"
            SERVER=$(echo $ip | awk -F ':' '{ print $2 }')
        else
            Echo "No PXE download server configured, trying: tftp.$DOMAIN"
            SERVER=tftp.$DOMAIN
        fi
    fi
    Echo "Checking connectivity of PXE download server: $SERVER"
    if ! ping -c 1 -w 30 $SERVER >/dev/null 2>&1;then
        Echo "PXE download server: $SERVER not found"
        if [ -z "$SERVERTYPE" ] || [ "$SERVERTYPE" = "tftp" ]; then
            if [ ! -z "$DHCPSIADDR" ];then
                Echo "Using: $DHCPSIADDR from DHCP info"
                SERVER=$DHCPSIADDR
            elif [ ! -z "$DHCPSID" ];then
                Echo "Using: $DHCPSID from DHCP info"
                SERVER=$DHCPSID
            elif [ ! -z "$SERVERID" ];then
                Echo "Using: $SERVERID from DHCP info"
                SERVER=$SERVERID
            else
                systemException \
                    "Can't find responding PXE download server... fatal !" \
                "reboot"
            fi
        fi
    fi
}
#======================================
# pxeSetupSystemAliasName
#--------------------------------------
function pxeSetupSystemAliasName {
    # /.../
    # Ask for an alias name if NAME from config.<MAC>
    # contains a number. If the number is -1 the system will
    # ask for ever for this name otherwhise the number sets
    # a timeout how long to wait for input of this data
    # ----
    local IFS=$IFS_ORIG
    if test $NAME -ne 0;then
        if test $NAME -eq -1;then
            Echo -n "Enter Alias Name for this system: " && \
            read SYSALIAS
        else
            Echo -n "Enter Alias Name [timeout in $NAME sec]: " && \
            read -t $NAME SYSALIAS
        fi
    fi
}
#======================================
# pxeSetupSystemHWInfoFile
#--------------------------------------
function pxeSetupSystemHWInfoFile {
    # /.../
    # calls hwinfo and stores the information into a file
    # suffixed by the hardware address of the network card
    # NOTE: it's required to have the dhcp info file sourced
    # before this function is called
    # ----
    local IFS=$IFS_ORIG
    hwinfo --all --log=hwinfo.$DHCPCHADDR >/dev/null
}
#======================================
# pxeSetupSystemHWTypeFile
#--------------------------------------
function pxeSetupSystemHWTypeFile {
    # /.../
    # collects information about the alias name the
    # architecture and more and stores that into a
    # file suffixed by the hardware address of the
    # network card.
    # ----
    local IFS=$IFS_ORIG
    echo "NCNAME=$SYSALIAS"   >> hwtype.$DHCPCHADDR
    echo "CRNAME=$SYSALIAS"   >> hwtype.$DHCPCHADDR
    echo "IPADDR=$IPADDR"     >> hwtype.$DHCPCHADDR
    echo "ARCHITECTURE=$ARCH" >> hwtype.$DHCPCHADDR
}
#======================================
# pxeSizeToMB
#--------------------------------------
function pxeSizeToMB {
    local IFS=$IFS_ORIG
    local size=$1
    if [ "$size" = "x" ];then
        echo . ; return
    fi
    local lastc=$(echo $size | sed -e 's@\(^.*\)\(.$\)@\2@')
    local value=$(echo $size | sed -e 's@\(^.*\)\(.$\)@\1@')
    if [ "$lastc" = "m" ] || [ "$lastc" = "M" ];then
        size=$value
    elif [ "$lastc" = "g" ] || [ "$lastc" = "G" ];then
        size=$(($value * 1024))
    fi
    echo +"$size"M
}
#======================================
# pxePartitionInput
#--------------------------------------
function pxePartitionInput {
    local IFS=$IFS_ORIG
    if [ $PARTITIONER = "fdasd" ];then
        pxePartitionInputFDASD
    else
        pxePartitionInputGeneric
    fi
}
#======================================
# pxeRaidPartitionInput
#--------------------------------------
function pxeRaidPartitionInput {
    local IFS=$IFS_ORIG
    if [ $PARTITIONER = "fdasd" ];then
        pxeRaidPartitionInputFDASD
    else
        pxeRaidPartitionInputGeneric
    fi
}
#======================================
# pxePartitionInputFDASD
#--------------------------------------
function pxePartitionInputFDASD {
    local IFS=$IFS_ORIG
    local field=0
    local count=0
    local IFS=","
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        partSize=$(pxeSizeToMB $partSize)
        if [ "$partID" = '82' ] || [ "$partID" = 'S' ];then
            partID=2
        elif [ "$partID" = '83' ] || [ "$partID" = 'L' ];then
            partID=1
        elif [ "$partID" = '8e' ] || [ "$partID" = 'V' ];then
            partID=4
        else
            partID=1
        fi
        echo -n "n . $partSize "
        if [ $partID = "2" ] || [ $partID = "4" ];then
            echo -n "t $count $partID "
        fi
    done
    echo "w"
}
#======================================
# pxeRaidPartitionInputFDASD
#--------------------------------------
function pxeRaidPartitionInputFDASD {
    pxePartitionInputFDASD
}
#======================================
# pxePartitionInputGeneric
#--------------------------------------
function pxePartitionInputGeneric {
    local IFS=","
    local field=0
    local count=0
    local pname
       for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        partSize=$(pxeSizeToMB $partSize)
        pname=lxrw
        if [ $partID = "S" ] || [ $partID = "82" ];then
            partID=82
            pname=lxswap
        fi
        if [ $partID = "L" ] || [ $partID = "83" ];then
            partID=83
            if [ "$partMount" = "/boot" ];then
                pname=lxboot
            else
                pname=lxroot
            fi
        fi
        if [ $partID = "V" ] || [ $partID = "8e" ];then
            partID=8e
            pname=lxlvm
        fi
        if [ $partID = "fd" ] || [ ! -z "$RAID" ];then
            partID=fd
            pname=lxroot
        fi
        if [ $count -eq 1 ];then
            echo -n "n p:$pname $count 1 $partSize "
            if  [ $partID = "82" ] || \
                [ $partID = "8e" ] || \
                [ $partID = "41" ] || \
                [ $partID = "fd" ]
            then
                echo -n "t $count $partID "
            fi
        else
            echo -n "n p:$pname $count . $partSize "
            if  [ $partID = "82" ] || \
                [ $partID = "8e" ] || \
                [ $partID = "41" ] || \
                [ $partID = "fd" ]
            then
                echo -n "t $count $partID "
            fi
        fi
        done
    echo "w q"
}
#======================================
# pxeRaidPartitionInputGeneric
#--------------------------------------
function pxeRaidPartitionInputGeneric {
    pxePartitionInputGeneric
}
#======================================
# pxeRaidCreate
#--------------------------------------
function pxeRaidCreate {
    local IFS=","
    local count=0
    local mdcount=0
    local raidFirst
    local raidSecond
    local conf=/mdadm.conf
    echo -n > $conf
    for i in $PART;do
        count=$((count + 1))
        raidFirst=$(ddn $raidDiskFirst $count)
        raidSecond=$(ddn $raidDiskSecond $count)
        if ! waitForStorageDevice $raidFirst;then
            return
        fi
        if ! waitForStorageDevice $raidSecond;then
            return
        fi
        mdadm --zero-superblock $raidFirst
        mdadm --zero-superblock $raidSecond
        mdadm --create --metadata=0.9 --run /dev/md$mdcount \
            --level=$raidLevel --raid-disks=2 $raidFirst $raidSecond
        if [ ! $? = 0 ];then
            systemException \
                "Failed to create raid array... fatal !" \
            "reboot"
        fi
        mdadm -Db /dev/md$mdcount >> $conf
        mdcount=$((mdcount + 1))
    done
}
#======================================
# pxeRaidAssemble
#--------------------------------------
function pxeRaidAssemble {
    local IFS=";"
    local count=0
    local mdcount=0
    local field=0
    local devices
    local raidFirst
    local raidSecond
    local conf=/mdadm.conf
    echo -n > $conf
    for n in $RAID;do
        case $field in
            0) raidLevel=$n     ; field=1 ;;
            1) raidDiskFirst=$n ; field=2 ;;
            2) raidDiskSecond=$n; field=3
        esac
    done
    IFS=","
    for i in $PART;do
        count=$((count + 1))
        raidFirst=$(ddn $raidDiskFirst $count)
        raidSecond=$(ddn $raidDiskSecond $count)
        if ! waitForStorageDevice $raidFirst;then
            echo "Warning: device $raidFirst did not appear"
        else
            devices=$raidFirst
        fi
        if ! waitForStorageDevice $raidSecond;then
            echo "Warning: device $raidSecond did not appear"
        else
            devices="$devices $raidSecond"
        fi
        IFS=$IFS_ORIG
        mdadm --assemble --run /dev/md$mdcount $devices
        mdadm -Db /dev/md$mdcount >> $conf
        mdcount=$((mdcount + 1))
    done
}
#======================================
# pxeRaidZeroSuperBlock
#--------------------------------------
function pxeRaidZeroSuperBlock {
    # /.../
    # if we switch from a raid setup back to a non-raid
    # setup and use the same partition table setup as before
    # it might happen that the raid superblock survives.
    # This function removes all raid super blocks from
    # all partitions in the PART setup. If the partition
    # layout is different compared to the former raid layout
    # the superblock is not valid anymore
    # ----
    local IFS=","
    local count=1
    local device
    for i in $PART;do
        device=$(ddn $imageDiskDevice $count)
        if ! waitForStorageDevice $device;then
            continue
        fi
        mdadm --zero-superblock $device
        count=$((count + 1))
    done
}
#======================================
# pxeRaidStop
#--------------------------------------
function pxeRaidStop {
    local IFS=","
    local count=0
    for i in $PART;do
        mdadm --stop /dev/md$count
        count=$((count + 1))
    done
}
#======================================
# pxeSwapDevice
#--------------------------------------
function pxeSwapDevice {
    local IFS=","
    local field=0
    local count=0
    local device
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        if test $partID = "82" -o $partID = "S";then
            device=$(ddn $DISK $count)
            waitForStorageDevice $device
            echo $device
            return
        fi
    done
}
#======================================
# pxeRaidSwapDevice
#--------------------------------------
function pxeRaidSwapDevice {
    local IFS=","
    local field=0
    local count=0
    local mdcount=0
    local device
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        if test $partID = "82" -o $partID = "S";then
            device=/dev/md$mdcount
            waitForStorageDevice $device
            echo $device
            return
        fi
        mdcount=$((mdcount + 1))
    done
}
#======================================
# pxeRaidPartCheck
#--------------------------------------
function pxeRaidPartCheck {
    local IFS=";"
    local count=0
    local field=0
    local n
    local raidLevel
    local raidDiskFirst
    local raidDiskSecond
    local device
    local partSize
    local partID
    local partMount
    local IdFirst
    local IdSecond
    local raidFirst
    local raidSecond
    local size
    local maxDiffPlus=10240  # max 10MB bigger
    local maxDiffMinus=10240 # max 10MB smaller
    for n in $RAID;do
        case $field in
            0) raidLevel=$n     ; field=1 ;;
            1) raidDiskFirst=$n ; field=2 ;;
            2) raidDiskSecond=$n; field=3
        esac
    done
    IFS=","
    for i in $PART;do
        count=$((count + 1))
        field=0
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        IdFirst="$(partitionID $raidDiskFirst $count)"
        IdSecond="$(partitionID $raidDiskSecond $count)"
        raidFirst=$(ddn $raidDiskFirst $count)
        raidSecond=$(ddn $raidDiskSecond $count)
        if [ "$IdFirst" != "fd" ] || ! waitForStorageDevice $raidFirst;then
            raidFirst=
        fi
        if [ "$IdSecond" != "fd" ] || ! waitForStorageDevice $raidSecond;then
            raidSecond=
        fi
        # /.../
        # RAID should be able to work in degraded mode when
        # one of the disks is missing
        # ----
        if [ -z "$raidFirst" -a -z "$raidSecond" ]; then
            return 1
        fi
        if [ "$partSize" == "x" ] ; then
            # partition use all available space
            continue
        fi
        for device in $raidFirst $raidSecond ; do
            size=$(partitionSize $device)
            if [ "$(( partSize * 1024 - size ))" -gt "$maxDiffMinus" -o \
                "$(( size - partSize * 1024 ))" -gt "$maxDiffPlus" ]
            then
                return 1
            fi
        done
    done
    return 0
}
#======================================
# pxePartitionSetupCheck
#--------------------------------------
function pxePartitionSetupCheck {
    # /.../
    # validation check for the PART line. So far this
    # function counts the given partition sizes and
    # checks if it's possible to setup those partitions
    # with respect to the available disk size
    # ----
    local IFS=","
    local field=0
    local count=0
    local reqsizeMB=0
    if [ -z "$DISK" ];then
        # no disk device available, might be a ram only
        # or diskless client
        return
    fi
    local haveKBytes=$(partitionSize $DISK)
    local haveMBytes=$((haveKBytes / 1024))
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n; field=1 ;;
        esac
        done
        if [ "$partSize" == "x" ] ; then
            # partition requests all available space
            # use a fake value of 10 MB as minimum
            reqsizeMB=$((reqsizeMB + 10))
        else
            # some size was requested, use value as MB size
            reqsizeMB=$((reqsizeMB + partSize))
        fi
    done
    if [ $reqsizeMB -gt $haveMBytes ];then
        systemException \
            "Requested partition sizes exceeds disk size" \
        "reboot"
    fi
}
#======================================
# pxePartCheck
#--------------------------------------
function pxePartCheck {
    # /.../
    # check the current partition table according to the
    # current setup of the PART line. Thus this function
    # checks if a new partition table setup compared to
    # the existing one was requested. Additionally the check
    # is clever enough to find out if the new partition
    # table setup would destroy data on the existing one
    # or if it only increases the partitions so that no
    # data loss is expected.
    # ----
    local IFS=$IFS_ORIG
    local count=0
    local field=0
    local n
    local partSize
    local partID
    local partMount
    local device
    local size
    local maxDiffPlus=10240  # max 10MB bigger
    local maxDiffMinus=10240 # max 10MB smaller
    IFS=","
    for i in $PART;do
        count=$((count + 1))
        field=0
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        device=$(ddn $DISK $count)
        if [ "$(partitionID $DISK $count)" != "$partID" ]; then
            return 1
        fi
        if ! waitForStorageDevice $device;then
            return 1
        fi
        if [ "$partSize" == "x" ] ; then
            # partition use all available space
            continue
        fi
        size=$(partitionSize $device)
        if [ "$(( partSize * 1024 - size ))" -gt "$maxDiffMinus" -o \
            "$(( size - partSize * 1024 ))" -gt "$maxDiffPlus" ]
        then
            return 1
        fi
    done
    return 0
}
#======================================
# pxeBootDevice
#--------------------------------------
function pxeBootDevice {
    local IFS=","
    local field=0
    local count=0
    local device
    for i in $PART;do
        field=0
        count=$((count + 1))
        IFS=";" ; for n in $i;do
        case $field in
            0) partSize=$n   ; field=1 ;;
            1) partID=$n     ; field=2 ;;
            2) partMount=$n;
        esac
        done
        if [ $partMount = "/boot" ];then
            device=$(ddn $DISK $count)
            waitForStorageDevice $device
            echo $device
            return
        fi
    done
}
#======================================
# startUtimer
#--------------------------------------
function startUtimer {
    local IFS=$IFS_ORIG
    local utimer=/usr/bin/utimer
    if [ ! -x $utimer ];then
        utimer=/utimer
    fi
    if [ -x $utimer ];then
        if [ ! -e /tmp/utimer ];then
            ln -s $UTIMER_INFO /tmp/utimer
        fi
        $utimer
        export UTIMER=$(cat /var/run/utimer.pid)
        if [ -f /iprocs ];then
            cat /iprocs | grep -v UTIMER_PID > /iprocs
        fi
        echo UTIMER_PID=$UTIMER >> /iprocs
    fi
}
#======================================
# setupBootPartitionPXE
#--------------------------------------
function setupBootPartitionPXE {
    #======================================
    # Variable setup
    #--------------------------------------
    local IFS=$IFS_ORIG
    local fs_type
    local FSTYPE_SAVE=$FSTYPE
    local mpoint=boot_bind
    unset NETBOOT_ONLY
    local prefix=/mnt
    #======================================
    # Don't operate with unknown root part
    #--------------------------------------
    if [ -z "$imageRootDevice" ];then
        # /.../
        # this case should only be reached when the netboot
        # code checks if the image needs an update. The update
        # check happens as early as possible and at that time
        # the root device variable is not set, so we use this
        # as the trigger to return
        #
        return
    fi
    if [ ! -e "$imageRootDevice" ];then
        # /.../
        # the device does not exist case happens if NFSROOT is used.
        # In this situation the variable holds the nfs root path
        # and options and not a local device. For this setup we
        # also don't need a boot partition because the client will
        # always boot from the network, so we use this as return
        # trigger too
        # ----
        export NETBOOT_ONLY=yes
        return
    fi
    #======================================
    # Check for boot partition in PART
    #--------------------------------------
    local bootdev=$(pxeBootDevice)
    if [ -e "$bootdev" ];then
        export imageBootDevice=$bootdev
    fi
    #======================================
    # Initial bootid setup
    #--------------------------------------
    if [ ! -z "$imageBootDevice" ];then
        # bootid is boot partition
        export bootid=$(nd $imageBootDevice)
    else
        # bootid is root partition
        export bootid=$(nd $imageRootDevice)
        export imageBootDevice=$imageRootDevice
    fi
    if [ ! -z "$RAID" ] && [ ! -z "$bootid" ];then
        # raid md devices start with 0 but partition id's start with 1
        export bootid=$((bootid + 1))
    fi
    #======================================
    # Probe boot/root filesystem
    #--------------------------------------
    probeFileSystem $imageRootDevice
    fs_type=$FSTYPE ; FSTYPE=$FSTYPE_SAVE
    #======================================
    # return if no extra boot partition
    #--------------------------------------
    if [ $imageBootDevice = $imageRootDevice ];then
        if [ $fs_type = "unknown" ] || [ "$haveLuks" = "yes" ];then
            # /.../
            # there is no extra boot device and the root device has an
            # unsupported boot filesystem or layer, mark as netboot only
            # ----
            export NETBOOT_ONLY=yes
        fi
        # no boot partition setup required
        return
    fi
    #======================================
    # Check boot partition filesystem
    #--------------------------------------
    if [ $fs_type = "unknown" ];then
        # /.../
        # there is a boot device with an unknown filesystem
        # create boot filesystem
        # ----
        createFilesystem $imageBootDevice
    fi
    #======================================
    # export bootpart relevant variables
    #--------------------------------------
    export bootPartitionFSType=$fs_type
    export kiwi_BootPart=$bootid
    #======================================
    # copy boot data from image to bootpart
    #--------------------------------------
    mkdir -p /$mpoint
    mount $imageBootDevice /$mpoint
    cp -a $prefix/boot /$mpoint
    if [ -e /boot.tgz ];then
        tar -xf /boot.tgz -C /$mpoint
    fi
    umount /$mpoint
    rmdir  /$mpoint
    #======================================
    # bind mount boot partition
    #--------------------------------------
    # the resetBootBind() function will resolve this to a
    # standard /boot mount when the bootloader will be
    # installed in preinit.
    # ---
    if ! isFSTypeReadOnly;then
        rm -rf $prefix/boot
        mkdir $prefix/boot
    fi
    mkdir $prefix/$mpoint
    mount $imageBootDevice $prefix/$mpoint
    mount --bind \
        $prefix/$mpoint/boot $prefix/boot
}
#======================================
# setupBootPartition
#--------------------------------------
function setupBootPartition {
    #======================================
    # Variable setup
    #--------------------------------------
    local IFS=$IFS_ORIG
    local label=undef
    local mpoint=boot_bind
    local FSTYPE_SAVE=$FSTYPE
    local fs_type=undef
    local BID=1
    local prefix=/mnt
    #======================================
    # Check for partition IDs meta data
    #--------------------------------------
    if [ ! -z "$kiwi_BootPart" ];then
        BID=$kiwi_BootPart
    fi
    #======================================
    # Check for boot partition
    #--------------------------------------
    if [ -z "$imageDiskDevice" ];then
        # no disk device like for live ISO based on clicfs
        return
    fi
    label=$(blkid $(ddn $imageDiskDevice $BID) -s LABEL -o value)
    if [ "$label" = "BOOT" ];then
        export imageBootDevice=$(ddn $imageDiskDevice $BID)
    fi
    #======================================
    # Probe boot partition filesystem
    #--------------------------------------
    probeFileSystem $(ddn $imageDiskDevice $BID)
    fs_type=$FSTYPE ; FSTYPE=$FSTYPE_SAVE
    export bootPartitionFSType=$fs_type
    #======================================
    # Export bootid if not yet done
    #--------------------------------------
    if [ -z "$bootid" ];then
        export bootid=$BID
    fi
    #======================================
    # Return if no boot setup required
    #--------------------------------------
    if [ ! "$label" = "BOOT" ] || [ ! -e "$imageBootDevice" ];then
        return
    fi
    #======================================
    # copy boot data from image to bootpart
    #--------------------------------------
    mkdir -p /$mpoint
    mount $imageBootDevice /$mpoint
    cp -a $prefix/boot /$mpoint
    if [ -e /boot.tgz ];then
        tar -xf /boot.tgz -C /$mpoint
    fi
    umount /$mpoint
    rmdir  /$mpoint
    #======================================
    # bind mount boot partition
    #--------------------------------------
    # the resetBootBind() function will resolve this to a
    # standard /boot mount when the bootloader will be
    # installed in preinit.
    # ---
    if ! isFSTypeReadOnly;then
        rm -rf $prefix/boot
        mkdir $prefix/boot
    fi
    mkdir $prefix/$mpoint
    mount $imageBootDevice $prefix/$mpoint
    mount --bind \
        $prefix/$mpoint/boot $prefix/boot
}
#======================================
# isVirtioDevice
#--------------------------------------
function isVirtioDevice {
    local IFS=$IFS_ORIG
    if [ $haveDASD -eq 0 ] && [ $haveZFCP -eq 0 ];then
        return 0
    fi
    return 1
}
#======================================
# isDASDDevice
#--------------------------------------
function isDASDDevice {
    local IFS=$IFS_ORIG
    if [ $haveDASD -eq 1 ];then
        return 0
    fi
    return 1
}
#======================================
# isZFCPDevice
#--------------------------------------
function isZFCPDevice {
    local IFS=$IFS_ORIG
    if [ $haveZFCP -eq 1 ];then
        return 0
    fi
    return 1
}
#======================================
# runPreinitServices
#--------------------------------------
function runPreinitServices {
    # /.../
    # run the .sh scripts in /etc/init.d/kiwi while
    # inside the preinit stage of the kiwi boot process
    # ----
    local IFS=$IFS_ORIG
    local service=/etc/init.d/kiwi/$1
    if [ ! -d $service ];then
        Echo "kiwi service $service not found... skipped"
        return
    fi
    for script in $service/*.sh;do
        test -e $script && bash -x $script
    done
}
#======================================
# setupTTY
#--------------------------------------
function setupTTY {
    # /.../
    # create tty device nodes in case we don't have devtmpfs
    # ----
    local IFS=$IFS_ORIG
    local tty_driver
    local major
    local minor
    local tty
    if $have_devtmpfs;then
        return
    fi
    if [ "$console" ]; then
        tty_driver="${tty_driver:+$tty_driver }${console%%,*}"
    fi
    for o in $tty_driver; do
        case "$o" in
            ttyS*) test -e /dev/$o || mknod -m 0660 /dev/$o c 4 64 ;;
            tty*)  test -e /dev/$o || mknod -m 0660 /dev/$o c 4  1 ;;
        esac
    done
    tty_driver=$(showconsole -n 2>/dev/null)
    if test -n "$tty_driver" ; then
        major=${tty_driver%% *}
        minor=${tty_driver##* }
        if test $major -eq 4 -a $minor -lt 64 ; then
            tty=/dev/tty$minor
            test -e $tty || mknod -m 0660 $tty c 4 $minor
        fi
        if test $major -eq 4 -a $minor -ge 64 ; then
            tty=/dev/ttyS$((64-$minor))
            test -e $tty || mknod -m 0660 $tty c 4 $minor
        fi
    fi
}
#======================================
# setupConsoleFont
#--------------------------------------
function setupConsoleFont {
    setfont $CONSOLE_FONT
}
#======================================
# setupConsole
#--------------------------------------
function setupConsole {
    # /.../
    # setup the xvc and/or hvc console if the device is present
    # also remove the ttyS0 console if no ttyS0 device exists
    # ----
    local IFS=$IFS_ORIG
    local itab=/etc/inittab
    local stty=/etc/securetty
    local init=/bin/systemd
    local xvc="X0:12345:respawn:/sbin/mingetty --noclear xvc0 linux"
    local hvc="H0:12345:respawn:/sbin/mingetty --noclear hvc0 linux"
    #======================================
    # return early in case of systemd
    #--------------------------------------
    if [ -e $init ];then
        return
    fi
    #======================================
    # create tty nodes if not done
    #--------------------------------------
    setupTTY
    #======================================
    # setup xvc console (xen)
    #--------------------------------------
    if [ -e /sys/class/tty/xvc0 ];then
        if ! cat $itab | grep -v '^#' | grep -q xvc0;then
            echo "$xvc" >> $itab
            echo "xvc0" >> $stty
        fi
    fi
    #======================================
    # setup hvc console (kvm)
    #--------------------------------------
    if [ -e /sys/class/tty/hvc0 ];then
        if ! cat $itab | grep -v '^#' | grep -q hvc0;then
            echo "$hvc" >> $itab
            echo "hvc0" >> $stty
        fi
    fi
    #======================================
    # remove ttyS0 if not present
    #--------------------------------------
    if [ ! -e /sys/class/tty/ttyS0 ];then
        cat $itab | grep -vi 'ttyS0' > $itab.new && mv $itab.new $itab
    fi
}
#======================================
# cleanPartitionTable
#--------------------------------------
function cleanPartitionTable {
    # /.../
    # remove partition table and create a new msdos
    # table label if parted is in use
    # ----
    local IFS=$IFS_ORIG
    dd if=/dev/zero of=$imageDiskDevice bs=512 count=1 >/dev/null
    if [ $PARTITIONER = "parted" ];then
        parted -s $imageDiskDevice mklabel msdos
    fi
}
#======================================
# updatePartitionTable
#--------------------------------------
function updatePartitionTable {
    # /.../
    # fix gpt geometry and backup gpt by using parted. parted asks
    # for fixing the table when e.g the print command is called.
    # We tell parted to fix the table
    # ----
    local IFS=$IFS_ORIG
    local device=$(getDiskDevice $1)
    local diskhd
    local plabel
    local line
    local partn
    local begin
    local stopp
    local label
    local pflag
    #======================================
    # check for hybrid iso
    #--------------------------------------
    if [ "$kiwi_hybridpersistent" = "true" ];then
        # /.../
        # The partition table written into an iso doesn't
        # like the resync, so we return early here
        # ----
        return
    fi
    #======================================
    # fix and store current table
    #--------------------------------------
    # the strange parted creates a gpt_sync_mbr if the disk
    # geometry has changed. If this happened we have to rewrite
    # the entire table with a new GPT label, thanks parted :(
    # ----
    if ! parted -m -s $device unit s print > /tmp/table;then
        systemException \
            "Failed to store current partition table" \
        "reboot"
    fi
    #======================================
    # check table type
    #--------------------------------------
    plabel=$(cat /tmp/table | grep ^$device: | cut -f6 -d:)
    if [ ! "$plabel" = "gpt_sync_mbr" ];then
        return 0
    fi
    #======================================
    # clone GPT table
    #--------------------------------------
    Echo "Updating GPT metadata..."
    if ! parted -s $device mklabel gpt;then
        systemException \
            "Failed to create GPT label" \
        "reboot"
    fi
    while read line;do
        if [[ ! $line =~ ^[0-9]+: ]];then
            continue
        fi
        line=$(echo "${line%?}")
        partn=$(echo $line | cut -f1 -d:)
        begin=$(echo $line | cut -f2 -d:)
        stopp=$(echo $line | cut -f3 -d:)
        label=$(echo $line | cut -f6 -d:)
        pflag=$(echo $line | cut -f7 -d:)
        if [ -z "$label" ];then
            label=primary
        fi
        if ! parted -s $device mkpart $label $begin $stopp 1>&2;then
            systemException \
                "Failed to clone GPT table" \
            "reboot"
        fi
        if [ ! -z "$pflag" ];then
            # set flag, but ignore errors here
            parted -s $device set $partn $pflag on &>/dev/null
            if [ $pflag = "bios_grub" ];then
                export needProtectiveMBR=1
            fi
        fi
    done < /tmp/table
    return 0
}
#======================================
# resetBootBind
#--------------------------------------
function resetBootBind {
    # /.../
    # remove the bind mount boot setup and replace with a
    # symbolic link to make the suse kernel update process
    # to work correctly
    # ----
    local IFS=$IFS_ORIG
    local bprefix=$1
    local bootdir=$bprefix/boot_bind
    if [ ! -e /proc/mounts ];then
        mount -t proc proc /proc
    fi
    #======================================
    # find bind boot dir
    #--------------------------------------
    if [ ! -e "/$bootdir" ];then
        return
    fi
    #======================================
    # reset bind mount to standard boot dir
    #--------------------------------------
    umount $bprefix/boot
    mv /$bootdir/boot /$bootdir/tmp
    mv /$bootdir/tmp/* /$bootdir
    rm -rf /$bootdir/tmp
    umount /$bootdir
    rmdir /$bootdir
    #======================================
    # update fstab entry
    #--------------------------------------
    grep -v ^/boot_bind $bprefix/etc/fstab > $bprefix/etc/fstab.new
    mv $bprefix/etc/fstab.new $bprefix/etc/fstab
    sed -i -e s@/boot_bind@/boot@ $bprefix/etc/fstab
    #======================================
    # mount boot again
    #--------------------------------------
    chroot $bprefix mount $imageBootDevice /boot
    #======================================
    # check for syslinux requirements
    #-------------------------------------- 
    if [ "$loader" = "syslinux" ];then
        # /.../
        # if syslinux is used we need to make sure to copy
        # the kernel and initrd to /boot on the boot partition.
        # This is normally done by the boot -> . link but we
        # can't create links on fat
        # ----
        IFS="," ; for i in $KERNEL_LIST;do
            if test -z "$i";then
                continue
            fi
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            break
        done
        IFS=$IFS_ORIG
        mkdir -p $bprefix/boot/boot
        cp $bprefix/boot/$kernel $bprefix/boot/boot/
        cp $bprefix/boot/$initrd $bprefix/boot/boot/
    fi
}
#======================================
# setupKernelLinks
#--------------------------------------
function setupKernelLinks {
    # /.../
    # check kernel names and links to kernel and initrd
    # according to the different boot-up situations
    # ----
    local IFS=$IFS_ORIG
    local prefix=/mnt
    #======================================
    # mount boot partition if required
    #--------------------------------------
    local mountCalled=no
    if [ -e "$imageBootDevice" ] && blkid $imageBootDevice;then
        if kiwiMount $imageBootDevice "$prefix";then
            mountCalled=yes
        fi
    fi
    #======================================
    # Change to boot directory
    #--------------------------------------
    pushd $prefix/boot >/dev/null
    #======================================
    # remove garbage if possible 
    #--------------------------------------
    if [ "$loader" = "syslinux" ] || [ "$loader" = "extlinux" ];then
        rm -rf grub
    fi
    #======================================
    # setup if overlay filesystem is used
    #--------------------------------------
    if  [ "$kiwi_oemkboot" = "true" ] || \
        [ "$PXE_KIWI_INITRD" = "yes" ] || \
        isFSTypeReadOnly
    then
        # /.../
        # we are using a special root setup based on an overlay
        # filesystem. In this case we can't use the SuSE Linux
        # initrd but must stick to the kiwi boot system.
        # ----
        IFS="," ; for i in $KERNEL_LIST;do
            if test -z "$i";then
                continue
            fi
            kernel=`echo $i | cut -f1 -d:`
            initrd=`echo $i | cut -f2 -d:`
            break
        done
        IFS=$IFS_ORIG
        if [ "$loader" = "syslinux" ];then
            rm -f $initrd && mv initrd.vmx $initrd
            rm -f $kernel && mv linux.vmx  $kernel
        elif [ "$PXE_KIWI_INITRD" = "yes" ];then
            if [ ! -f initrd.kiwi ] && [ ! -f linux.kiwi ];then
                Echo "WARNING: can't find kiwi initrd/linux !"
                Echo -b "local boot will not work, maybe you forgot"
                Echo -b "to add KIWI_INITRD and KIWI_KERNEL in config.<MAC> ?"
            else
                if [ "$loader" = "syslinux" ];then
                    rm -f $initrd && mv initrd.kiwi $initrd
                    rm -f $kernel && mv linux.kiwi  $kernel
                else
                    rm -f $initrd && ln -s initrd.kiwi $initrd
                    rm -f $kernel && ln -s linux.kiwi  $kernel
                fi
            fi
        else
            rm -f $initrd && ln -s initrd.vmx $initrd
            rm -f $kernel && ln -s linux.vmx  $kernel
        fi
    fi  
    #======================================
    # make sure boot => . link exists
    #--------------------------------------
    if [ ! "$bootPartitionFSType" = "vfat" ] && [ ! -e boot ];then
        ln -s . boot
    fi
    #======================================
    # umount boot partition if required
    #--------------------------------------
    popd >/dev/null
    if [ "$mountCalled" = "yes" ];then
        umount $prefix
    fi
}
#======================================
# activateBootPartition
#--------------------------------------
function activateBootPartition {
    if [[ ! $arch =~ i.86|x86_64 ]];then
        # activation of a partition is only needed on
        # x86 legacy BIOS implementations
        return
    fi
    local IFS=$IFS_ORIG
    local device=$imageBootDevice
    if [ ! -e $device ];then
        device=$imageRootDevice
    fi
    if [ ! -e $device ];then
        echo "Can't find boot partition, activation skipped"
        return
    fi
    local bootID=$(nd $device)
    local diskID=$(dn $device)
    sfdisk $diskID --force -A $bootID
}
#======================================
# refreshProtectiveMBR
#--------------------------------------
function updateProtectiveMBR {
    local IFS=$IFS_ORIG
    local device=$1
    local input=/part.input
    if ! lookup gdisk &>/dev/null;then
        Echo "Warning, gdisk tool not found"
        Echo "This could prevent the system to boot via EFI"
    fi
    rm -f $input
    if [ ! -e "$device" ];then
        device=$imageDiskDevice
    fi
    for cmd in x n w y; do
        echo $cmd >> $input
    done
    gdisk $device < $input 1>&2
    if [ ! $? = 0 ]; then
        Echo "Failed to create protective MBR !"
        Echo "This could prevent the system to boot via EFI"
    fi
}
#======================================
# FBOK
#--------------------------------------
function FBOK {
    local IFS=$IFS_ORIG
    if [ ! -e /dev/fb0 ];then
        # no framebuffer device found
        return 1
    fi
    if ! lookup fbiterm &>/dev/null;then
        # no framebuffer terminal program found
        return 1
    fi
    if lookup isconsole &>/dev/null;then
        if ! isconsole;then
            # inappropriate ioctl (not a linux console)
            return 1
        fi
    elif ! fbiterm echo &>/dev/null;then
        # fbiterm can't be called with echo test cmd
        return 1
    fi
    return 0
}
#======================================
# backupDiskLayout
#--------------------------------------
function backupDiskLayout {
    local IFS=$IFS_ORIG
    local devname=$1
    local device=$(getDiskDevice $devname)
    IFS=""
    local parted=$(parted -m -s $device unit cyl print | grep -v Warning:)
    local pcount=$(echo $parted | tail -n 1 | cut -f1 -d:)
    local diskhd=$(echo $parted | head -n 3 | tail -n 2 | head -n 1)
    local plabel=$(echo $diskhd | cut -f6 -d:)
    IFS=$IFS_ORIG
    if [[ $plabel =~ gpt ]];then
        backupGPT $device $pcount
    else
        backupMBR $device
    fi
}
#======================================
# backupMBR
#--------------------------------------
function backupMBR {
    local IFS=$IFS_ORIG
    local device=$1
    dd if=$device bs=1 count=512
}
#======================================
# backupGPT
#--------------------------------------
function backupGPT {
    local IFS=$IFS_ORIG
    local device=$1
    local pcount=$2
    dd if=$device bs=1 count=$(((128 * pcount) + 1024))
}
#======================================
# loop_setup
#--------------------------------------
function loop_setup {
    local IFS=$IFS_ORIG
    local target=$1
    local logical_sector_size
    if [ ! -z "$kiwi_target_blocksize" ];then
        logical_sector_size="-L $kiwi_target_blocksize"
    fi
    local loop=$(losetup $logical_sector_size -f --show $target)
    if [ ! -e "$loop" ];then
        return 1
    fi
    echo $loop
}
#======================================
# loop_delete
#--------------------------------------
function loop_delete {
    local IFS=$IFS_ORIG
    local target=$1
    losetup -d $target
}
#======================================
# initialize
#--------------------------------------
function initialize {
    local IFS=$IFS_ORIG
    #======================================
    # Exports boot image .profile
    #--------------------------------------
    if [ -f /.profile ];then
        importFile < /.profile
        if [ ! -z "$kiwi_bootloader" ];then
            export loader=$kiwi_bootloader
        fi
    fi
    #======================================
    # Check partitioner capabilities
    #--------------------------------------
    if echo $kiwi_iname | grep -qE '(oem|net)boot';then
        if [ $PARTITIONER = "unsupported" ];then
            systemException \
                "Installed parted version is too old" \
            "reboot"
        fi
    fi
    #======================================
    # Check for hotfix kernel
    #--------------------------------------
    reloadKernel
    #======================================
    # Prevent blank screen
    #--------------------------------------
    if [ -x /usr/bin/setterm ];then
        setterm -powersave off -blank 0
    fi
    #======================================
    # Start boot timer (first stage)
    #--------------------------------------
    startUtimer
}

# vim: set noexpandtab:
