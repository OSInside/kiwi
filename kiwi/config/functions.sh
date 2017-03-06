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
#               : for the config.sh and image.sh scripts
#               : 
#               :
# STATUS        : Development
#----------------
#======================================
# work in POSIX environment
#--------------------------------------
export LANG=C
export LC_ALL=C
#======================================
# check base tools
#--------------------------------------
for tool in basename dirname;do
    if [ -x /bin/$tool ] && [ ! -e /usr/bin/$tool ];then
        ln -s /bin/$tool /usr/bin/$tool
    fi
done
for tool in setctsid klogconsole;do
    if [ -x /usr/bin/$tool ] && [ ! -e /usr/sbin/$tool ];then
        ln -s /usr/bin/$tool /usr/sbin/$tool
    fi
done

#======================================
# baseSystemdServiceInstalled
#--------------------------------------
function baseSystemdServiceInstalled {
    local service=$1
    local sd_dirs="
        /usr/lib/systemd/system
        /etc/systemd/system
        /run/systemd/system
    "
    local dir
    for dir in ${sd_dirs} ; do
        if [ -f "${dir}/${service}.service" ];then
            echo ${dir}/${service}.service
            return
        fi
        if [ -f "${dir}/${service}.mount" ];then
            echo ${dir}/${service}.mount
            return
        fi
    done
}

#======================================
# baseSysVServiceInstalled
#--------------------------------------
function baseSysVServiceInstalled {
    local service=$1
    if [ -x "/etc/init.d/${service}" ];then
        echo "${service}"
    fi
}

#======================================
# baseSystemctlCall
#--------------------------------------
function baseSystemdCall {
    local service_name=$1; shift
    local service=$(baseSystemdServiceInstalled "$service_name")
    if [ ! -z "$service" ];then
        systemctl "$@" "$service"
    else
        local legacy_service=$(baseSysVServiceInstalled "$service_name")
        if [ ! -z "$legacy_service" ];then
            # systemd is sysV init compatible and still allows
            # to enable those type of services
            systemctl "$@" "$legacy_service"
        fi
    fi
}

#======================================
# baseInsertService
#--------------------------------------
function baseInsertService {
    # /.../
    # Enable a system service using systemctl
    # Examples:
    #
    # baseInsertService sshd
    #   --> enable sshd service
    #
    # ----
    local service=$1
    baseSystemdCall "$service" "enable"
}

#======================================
# baseRemoveService
#--------------------------------------
function baseRemoveService {
    # /.../
    # Disable a system service using systemctl
    # Example:
    #
    # baseRemoveService sshd
    #   --> disable sshd service
    # ----
    local service=$1
    baseSystemdCall "$service" "disable"
}

#======================================
# baseService
#--------------------------------------
function baseService {
    # /.../
    # Enable or Disable a service
    # Examples:
    #
    # baseService sshd on
    #   --> enable sshd service
    #
    # baseService sshd off
    #   --> disable sshd service
    #
    # ----
    local service=$1
    local target=$2
    if [ -z "$target" ];then
        echo "baseService: no target specified"
        return
    fi
    if [ -z "$service" ];then
        echo "baseService: no service name specified"
        return
    fi
    if [ $target = off ];then
        baseRemoveService $service
    else
        baseInsertService $service
    fi
}

#======================================
# suseRemoveService
#--------------------------------------
function suseRemoveService {
    # function kept for compatibility
    baseRemoveService "$@"
}

#======================================
# suseInsertService
#--------------------------------------
function suseInsertService {
    # function kept for compatibility
    baseInsertService "$@"
}

#======================================
# suseService
#--------------------------------------
function suseService {
    # function kept for compatibility
    service_name=$1
    service_state=$2
    if [ "$service_state" = "off" ];then
        baseRemoveService "$service_name"
    else
        baseInsertService "$service_name"
    fi
}

#======================================
# suseActivateDefaultServices
#--------------------------------------
function suseActivateDefaultServices {
    # /.../
    # Some basic services that needs to be on.
    # ----
    local services=(
        network
        cron
    )
    for i in "${services[@]}";do
        echo "Activating service: $i"
        baseInsertService $i
    done
}

#======================================
# suseImportBuildKey
#--------------------------------------
function suseImportBuildKey {
    # /.../
    # Add missing gpg keys to rpm database
    # ----
    local KEY
    local TDIR=$(mktemp -d)
    local dumpsigs=/usr/lib/rpm/gnupg/dumpsigs
    if [ ! -d "$TDIR" ]; then
        echo "suseImportBuildKey: Failed to create temp dir"
        return
    fi
    if [ -d "/usr/lib/rpm/gnupg/keys" ];then
        pushd "/usr/lib/rpm/gnupg/keys"
    else
        pushd "$TDIR"
        if [ -x $dumpsigs ];then
            $dumpsigs /usr/lib/rpm/gnupg/suse-build-key.gpg
        fi
    fi
    for KFN in gpg-pubkey-*.asc; do
        if [ ! -e "$KFN" ];then
            #
            # check if file exists because if the glob match did
            # not find files bash will use the glob string as
            # result and we just continue in this case
            #
            continue
        fi
        KEY=$(basename "$KFN" .asc)
        rpm -q "$KEY" >/dev/null
        [ $? -eq 0 ] && continue
        echo "Importing $KEY to rpm database"
        rpm --import "$KFN"
    done
    popd
    rm -rf "$TDIR"
}

#======================================
# baseSetupUserPermissions
#--------------------------------------
function baseSetupUserPermissions {
    while read line;do
        dir=$(echo $line | cut -f6 -d:)
        uid=$(echo $line | cut -f3 -d:)
        usern=$(echo $line | cut -f1 -d:)
        group=$(echo $line | cut -f4 -d:)
        shell=$(echo $line | cut -f7 -d:)
        if [ ! -d "$dir" ];then
            continue
        fi
        if [ $uid -lt 1000 ];then
            continue
        fi
        if [[ ! $shell =~ nologin|true|false ]];then
            group=$(cat /etc/group | grep "$group" | cut -f1 -d:)
            chown -c -R $usern:$group $dir/*
        fi
    done < /etc/passwd
}

#======================================
# baseSetupBoot
#--------------------------------------
function baseSetupBoot {
    if [ -f /linuxrc ];then
        cp linuxrc init
        exit 0
    fi
}

#======================================
# suseConfig
#--------------------------------------
function suseConfig {
    # /.../
    # Setup very basic SUSE system configuration
    # ----
    #======================================
    # keytable
    #--------------------------------------
    if [ ! -z "$kiwi_keytable" ];then
        keytable_config=/etc/sysconfig/keyboard
        baseUpdateSysConfig $keytable_config KEYTABLE $kiwi_keytable
    fi
    #======================================
    # locale
    #--------------------------------------
    if [ ! -z "$kiwi_language" ];then
        language=$(echo $kiwi_language | cut -f1 -d,).UTF-8
        lang_config=/etc/sysconfig/language
        baseUpdateSysConfig $lang_config RC_LANG $language
    fi
    #======================================
    # timezone
    #--------------------------------------
    if [ ! -z "$kiwi_timezone" ];then
        if [ -f /usr/share/zoneinfo/$kiwi_timezone ];then
            ln -sf /usr/share/zoneinfo/$kiwi_timezone /etc/localtime
            time_config=/etc/sysconfig/clock
            baseUpdateSysConfig $time_config TIMEZONE $kiwi_timezone
        else
            echo "timezone: $kiwi_timezone not found"
        fi
    fi
    #======================================
    # hwclock
    #--------------------------------------
    if [ ! -z "$kiwi_hwclock" ];then
        time_config=/etc/sysconfig/clock
        baseUpdateSysConfig $time_config HWCLOCK "--$kiwi_hwclock"
    fi
}

#======================================
# baseGetPackagesForDeletion
#--------------------------------------
function baseGetPackagesForDeletion {
    echo $kiwi_delete
}

#======================================
# baseGetProfilesUsed
#--------------------------------------
function baseGetProfilesUsed {
    echo $kiwi_profiles
}

#======================================
# baseCleanMount
#--------------------------------------
function baseCleanMount {
    umount /proc/sys/fs/binfmt_misc &>/dev/null
    umount /proc    &>/dev/null
    umount /dev/pts &>/dev/null
    umount /sys     &>/dev/null
}

#======================================
# baseMount
#--------------------------------------
function baseMount {
    if [ ! -e /proc/cmdline ];then
        mount -t proc proc /proc
    fi
    if [ ! -e /sys/kernel ];then
        mount -t sysfs sysfs /sys
    fi
    if [ ! -e /proc/sys/fs/binfmt_misc/register ];then
        mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc
    fi
    if [ ! -e /dev/pts/0 ];then
        mount -t devpts -o mode=0620,gid=5 devpts /dev/pts
    fi
}

#======================================
# baseStripMans 
#--------------------------------------
function baseStripMans {
    # /..,/
    # remove all manual pages, except 
    # one given as parametr
    #
    # params - name of keep man pages
    # example baseStripMans less
    # ----
    local keepMans="$@"
    local directories="
        /opt/gnome/share/man
        /usr/local/man
        /usr/share/man
        /opt/kde3/share/man/packages
    "
    find $directories -mindepth 1 -maxdepth 2 -type f 2>/dev/null |\
        baseStripAndKeep ${keepMans}
}

#======================================
# baseStripDocs 
#--------------------------------------
function baseStripDocs {
    # /.../
    # remove all documentation, except 
    # copying license copyright
    # ----
    local docfiles
    local directories="
        /opt/gnome/share/doc/packages
        /usr/share/doc/packages
        /opt/kde3/share/doc/packages
    "
    for dir in $directories; do
        docfiles=$(find $dir -type f |grep -iv "copying\|license\|copyright")
        rm -f $docfiles
    done
    rm -rf /usr/share/info
    rm -rf /usr/share/man
}
#======================================
# baseStripLocales
#--------------------------------------
function baseStripLocales {
    local keepLocales="$@"
    local directories="
        /usr/lib/locale
    "
    find $directories -mindepth 1 -maxdepth 1 -type d 2>/dev/null |\
        baseStripAndKeep ${keepLocales}
}

#======================================
# baseStripTranslations
#--------------------------------------
function baseStripTranslations {
    local keepMatching="$@"
    find /usr/share/locale -name "*.mo" | grep -v $keepMatching | xargs rm -f
}

#======================================
# baseStripInfos 
#--------------------------------------
function baseStripInfos {
    # /.../
    # remove all info files, 
    # except one given as parametr
    #
    # params - name of keep info files
    # ----
    local keepInfos="$@"
    local directories="
        /usr/share/info
    "
    find $directories -mindepth 1 -maxdepth 1 -type f 2>/dev/null |\
        baseStripAndKeep "${keepInfos}"
}
#======================================
# baseStripAndKeep
#--------------------------------------
function baseStripAndKeep {
    # /.../
    # helper function for strip* functions
    # read stdin lines of files to check 
    # for removing
    # - params - files which should be keep
    # ----
    local keepFiles="$@"
    local found
    while read file; do
        local baseFile=$(/usr/bin/basename $file)
        found=0
        for keep in $keepFiles;do
            if echo $baseFile | grep -q $keep; then
                found=1
                break
            fi
        done
        if [ "$found" = 0 ]; then
             Rm -rf "$file"
        fi
    done
}
#======================================
# baseStripTools
#--------------------------------------
function baseStripTools {
    local tpath=$1
    local tools=$2
    local found
    for file in `find $tpath`;do
        found=0
        base=$(/usr/bin/basename $file)
        for need in $tools;do
            if [ "$base" = "$need" ];then
                found=1
                break
            fi
        done
        if [ "$found" = 0 ] && [ ! -d "$file" ];then
            Rm -fv "$file"
        fi
    done
}
#======================================
# baseStripRPM
#--------------------------------------
function baseStripRPM {
    # /.../
    # remove rpms defined in config.xml 
    # under image=delete section
    #
    # Method is a noop and only exists for compatibility
    # kiwi handles this now in the core python code
    # ----
    return
}
#======================================
# baseSetupInPlaceSVNRepository
#--------------------------------------
function baseSetupInPlaceSVNRepository {
    # /.../
    # create an in place subversion repository for the
    # specified directories. A standard call could look like this
    # baseSetupInPlaceSVNRepository /etc /srv /var/log
    # ----
    local paths=$1
    local repo=/var/adm/sys-repo
    if [ ! -x /usr/bin/svn ];then
        echo "subversion not installed... skipped"
        return
    fi
    svnadmin create $repo
    chmod 700 $repo
    svn mkdir -m created file:///$repo/trunk
    local subp=""
    for dir in $paths;do
        subp=""
        for n in $(echo $dir | tr '/' ' ');do
            if [ -z $n ];then
                continue
            fi
            subp="$subp/$n"
            svn mkdir -m created file:///$repo/trunk/$subp
        done
    done
    for dir in $paths;do
        chmod 700 $dir/.svn
        svn add $dir/*
        find $dir -name .svn | xargs chmod 700
        svn ci -m initial $dir
    done
}

#======================================
# baseSetupPlainTextGITRepository
#--------------------------------------
function baseSetupPlainTextGITRepository {
    # /.../
    # create an in place git repository of the root
    # directory containing all plain/text files.
    # ----
    if [ ! -x /usr/bin/git ];then
        echo "git not installed... skipped"
        return
    fi
    pushd /
    local ignore=""
    #======================================
    # directories to ignore
    #--------------------------------------
    local dirs="
        /sys /dev /var/log /home /media /var/run /var/tmp /tmp /var/lock
        /image /var/spool /var/cache /var/lib /boot /root /var/adm
        /usr/share/doc /base-system /usr/lib /usr/lib64 /usr/bin /usr/sbin
        /usr/share/man /proc /bin /sbin /lib /lib64 /opt
        /usr/share/X11 /.git
    "
    #======================================
    # files to ignore
    #--------------------------------------
    local files="
        ./etc/Image* *.lock ./etc/resolv.conf *.gif *.png
        *.jpg *.eps *.ps *.la *.so */lib */lib64 */doc */zoneinfo
    "
    #======================================
    # creae .gitignore and find list
    #--------------------------------------
    for entry in $files;do
        echo $entry >> .gitignore
        if [ -z "$ignore" ];then
            ignore="-wholename $entry"
        else
            ignore="$ignore -or -wholename $entry"
        fi
    done
    for entry in $dirs;do
        echo $entry >> .gitignore
        if [ -z "$ignore" ];then
            ignore="-path .$entry"
        else
            ignore="$ignore -or -path .$entry"
        fi
    done
    #======================================
    # init git base
    #--------------------------------------
    git init
    #======================================
    # find all text/plain files except ign
    #--------------------------------------
    for i in `find . \( $ignore \) -prune -o -print`;do
        file=`echo $i | cut -f2 -d.`
        if file -i $i | grep -q "text/*";then
            git add $i
        fi
        if file -i $i | grep -q "application/x-shellscript";then
            git add $i
        fi
        if file -i $i | grep -q "application/x-awk";then
            git add $i
        fi
        if file -i $i | grep -q "application/x-c";then
            git add $i
        fi
        if file -i $i | grep -q "application/x-c++";then
            git add $i
        fi
        if file -i $i | grep -q "application/x-not-regular-file";then
            echo $file >> .gitignore
        fi
        if file -i $i | grep -q "application/x-gzip";then
            echo $file >> .gitignore
        fi
        if file -i $i | grep -q "application/x-empty";then
            echo $file >> .gitignore
        fi
    done
    #======================================
    # commit the git
    #--------------------------------------
    git commit -m "deployed"
    popd
}

#======================================
# baseSetupInPlaceGITRepository
#--------------------------------------
function baseSetupInPlaceGITRepository {
    # /.../
    # create an in place git repository of the root
    # directory. This process may take some time and you
    # may expect problems with binary data handling
    # ----
    if [ ! -x /usr/bin/git ];then
        echo "git not installed... skipped"
        return
    fi
    pushd /
    rm -rf .git
    cat > .gitignore < /dev/null
    local files="
        /bin/ /boot/ /dev/ /image/ /lib/ /lib64/ /lost+found/ /media/ /mnt/
        /opt/ /proc/ /sbin/ /sys/ /tmp/ /var/ /usr/ *.lock /etc/Image*
        /base-system/ /.broken /.buildenv .bash_history /.kconfig /.profile
        /etc/mtab
    "
    # disable globbing
    set -o noglob
    for entry in $files;do
        echo $entry >> .gitignore
    done
    # enable globbing
    set +o noglob
    git init && git add -A && \
    git commit -m "deployed"
    popd
}
#======================================
# Rm  
#--------------------------------------
function Rm {
    # /.../
    # delete files & anounce it to log
    # ----
    Debug "rm $@"
    rm $@
}

#======================================
# Rpm  
#--------------------------------------
function Rpm {
    # /.../
    # all rpm function & anounce it to log
    # ----
    Debug "rpm $@"
    rpm $@
}
#======================================
# Echo
#--------------------------------------
function Echo {
    # /.../
    # print a message to the controling terminal
    # ----
    local option=""
    local prefix="----->"
    local optn=""
    local opte=""
    while getopts "bne" option;do
        case $option in
            b) prefix="      " ;;
            n) optn="-n" ;;
            e) opte="-e" ;;
            *) echo "Invalid argument: $option" ;;
        esac
    done
    shift $(($OPTIND - 1))
    echo $optn $opte "$prefix $1"
    OPTIND=1
}
#======================================
# Debug
#--------------------------------------
function Debug {
    # /.../
    # print message if variable DEBUG is set to 1
    # -----
    if test "$DEBUG" = 1;then
        echo "+++++> (caller:${FUNCNAME[1]}:${FUNCNAME[2]} )  $@"
    fi
}
#======================================
# baseSetupBusyBox
#--------------------------------------
function baseSetupBusyBox {
    # /.../
    # activates busybox if installed for all links from
    # the busybox/busybox.links file - you can choose custom apps to
    # be forced into busybox with the "-f" option as first parameter
    # ---
    # example: baseSetupBusyBox -f /bin/zcat /bin/vi
    # ---
    local applets=""
    local force=no
    local busyboxlinks=/usr/share/busybox/busybox.links
    if ! rpm -q --quiet busybox; then
        echo "Busybox not installed... skipped"
        return 0
    fi
    if [ $# -gt 0 ] && [ "$1" = "-f" ]; then
        force=yes
        shift
    fi
    if [ $# -gt 0 ]; then
        for i in "$@"; do
            if grep -q "^$i$" "$busyboxlinks"; then 
                applets="${applets} $i"
            fi
        done
    else
        applets=`cat "$busyboxlinks"`
    fi
    for applet in $applets; do
        if [ ! -f "$applet" ] || [ "$force" = "yes" ]; then
            echo "Busybox Link: ln -sf /usr/bin/busybox $applet"
            ln -sf /usr/bin/busybox "$applet"
        fi
    done
}

#======================================
# stripUnusedLibs
#--------------------------------------
function baseStripUnusedLibs {
    # /.../
    # Remove libraries which are not directly linked
    # against applications in the bin directories
    # ----
    local needlibs
    local found
    local dir
    local lnk
    local new
    local lib
    local lddref
    # /.../
    # Find directly used libraries, by calling ldd
    # on files in *bin*
    # ---
    ldconfig
    rm -f /tmp/needlibs
    for i in /usr/bin/* /bin/* /sbin/* /usr/sbin/* /lib/systemd/systemd-*;do
        for n in $(ldd $i 2>/dev/null | cut -f2- -d\/ | cut -f1 -d " ");do
            if [ ! -e /$n ];then
                continue
            fi
            lddref=/$n
            while true;do
                lib=$(readlink $lddref)
                if [ $? -eq 0 ];then
                    lddref=$lib
                    continue
                fi
                break
            done
            lddref=$(basename $lddref)
            echo $lddref >> /tmp/needlibs
        done
    done
    count=0
    for i in $(cat /tmp/needlibs | sort | uniq);do
        for d in \
            /lib /lib64 /usr/lib /usr/lib64 \
            /usr/X11R6/lib /usr/X11R6/lib64 \
            /lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
        do
            if [ -e "$d/$i" ];then
                needlibs[$count]=$d/$i
                count=$((count + 1))
            fi
        done
    done
    # /.../
    # add exceptions
    # ----
    while [ ! -z $1 ];do
        for i in \
            /lib*/$1* /usr/lib*/$1* \
            /lib/x86_64-linux-gnu/$1* /usr/lib/x86_64-linux-gnu/$1* \
            /usr/X11R6/lib*/$1*
        do
            if [ -e $i ];then
                needlibs[$count]=$i
                count=`expr $count + 1`
            fi
        done
        shift
    done
    # /.../
    # find unused libs and remove it, dl loaded libs
    # seems not to be that important within the initrd
    # ----
    rm -f /tmp/needlibs
    for i in \
        /lib/lib* /lib64/lib* /usr/lib/lib* \
        /usr/lib64/lib* /usr/X11R6/lib*/lib* \
        /lib/x86_64-linux-gnu/lib* /usr/lib/x86_64-linux-gnu/lib*
    do
        found=0
        if [ ! -e $i ];then
            continue
        fi
        if [ -d $i ];then
            continue
        fi
        if [ -L $i ];then
            continue
        fi
        for n in ${needlibs[*]};do
            if [ $i = $n ];then
                found=1; break
            fi
        done
        if [ $found -eq 0 ];then
            echo "Removing library: $i"
            rm $i
        fi
    done
}

#======================================
# baseUpdateSysConfig
#--------------------------------------
function baseUpdateSysConfig {
    # /.../
    # Update sysconfig variable contents
    # ----
    local FILE=$1
    if [ -f "$FILE" ];then
        local VAR=$2
        local VAL=$3
        local args=$(echo "s'@^\($VAR=\).*\$@\1\\\"$VAL\\\"@'")
        eval sed -i $args $FILE
    else
        echo "warning: config file $FILE not found"
    fi
}

#======================================
# baseStripInitrd
#--------------------------------------
function baseStripInitrd {
    #==========================================
    # Check for initrd system
    #------------------------------------------
    if [ "$kiwi_initrd_system" = "dracut" ]; then
        echo "dracut initrd system requested, initrd strip skipped"
        return
    fi
    #==========================================
    # Remove unneeded files
    #------------------------------------------
    for delete in $kiwi_strip_delete;do
        echo "Removing file/directory: $delete"
        rm -rf $delete
    done
    #==========================================
    # remove unneeded tools
    #------------------------------------------
    local tools="$kiwi_strip_tools"
    tools="$tools $@"
    for path in /sbin /usr/sbin /usr/bin /bin;do
        baseStripTools "$path" "$tools"
    done
    #==========================================
    # remove unused libs
    #------------------------------------------
    baseStripUnusedLibs $kiwi_strip_libs
    #==========================================
    # remove package manager meta data
    #------------------------------------------
    for p in dpkg rpm yum;do
        rm -rf /var/lib/$p
    done
}

#======================================
# suseStripInitrd
#--------------------------------------
function suseStripInitrd {
    baseStripInitrd $@
}

#======================================
# rhelStripInitrd
#--------------------------------------
function rhelStripInitrd {
    baseStripInitrd $@
}

#======================================
# debianStripInitrd
#--------------------------------------
function debianStripInitrd {
    baseStripInitrd $@
}

#======================================
# rhelGFXBoot
#--------------------------------------
function rhelGFXBoot {
    suseGFXBoot $@
}

#======================================
# debianGFXBoot
#--------------------------------------
function debianGFXBoot {
    local theme=$1
    local loader=$2
    local loader_theme=$theme
    local splash_theme=$theme
    export PATH=$PATH:/usr/sbin
    if [ ! -z "$kiwi_splash_theme" ];then
        splash_theme=$kiwi_splash_theme
    fi
    if [ ! -z "$kiwi_loader_theme"  ];then
        loader_theme=$kiwi_loader_theme
    fi
    if [ ! -z "$kiwi_bootloader" ];then
        loader=$kiwi_bootloader
    fi
    test -d /image/loader || mkdir /image/loader
    #======================================
    # setup grub2 bootloader data
    #--------------------------------------
    if [ -d /boot/grub/themes/$loader_theme ];then
        #======================================
        # use boot theme from grub2
        #--------------------------------------
        echo "using grub2 branding data"
        mkdir -p /usr/share/grub2/themes/$loader_theme
        mv /boot/grub/themes/$loader_theme/* \
            /usr/share/grub2/themes/$loader_theme
        mv /boot/grub/unicode.pf2 /usr/share/grub2
    else
        #======================================
        # no grub2 based graphics boot data
        #--------------------------------------
        echo "grub2 branding not installed"
        echo "grub2 graphics boot skipped !"
    fi
    #======================================
    # copy isolinux loader data
    #--------------------------------------
    if [ -f /usr/lib/ISOLINUX/isolinux.bin ];then
        mv /usr/lib/ISOLINUX/isolinux.bin /image/loader
        mv /usr/lib/syslinux/modules/bios/* /image/loader
    fi
    if [ -f /boot/memtest* ];then
        mv /boot/memtest* /image/loader/memtest
    fi
    #======================================
    # setup splash screen
    #--------------------------------------
    if [ -d /usr/share/plymouth/themes/$splash_theme ];then
        echo "plymouth splash system is used"
        touch "/plymouth.splash.active"
    fi
    #======================================
    # setup isolinux boot screen
    #--------------------------------------
    if [ ! -f /etc/bootsplash/themes/$loader_theme/bootloader/message ];then
        # Fallback to upstream gfxboot theme if the distribution
        # does not provide a common theme for all loaders
        loader_theme=upstream
    fi
    if [ -f /etc/bootsplash/themes/$loader_theme/bootloader/message ];then
        #======================================
        # use boot theme from gfxboot-themes
        #--------------------------------------
        echo "using $loader_theme gfxboot theme data"
        if [ -e "/etc/bootsplash/themes/$loader_theme/cdrom/gfxboot.cfg" ];then
            # isolinux boot graphics file (bootlogo)...
            mv /etc/bootsplash/themes/$loader_theme/cdrom/* /image/loader
            local gfxcfg=/image/loader/gfxboot.cfg
            # tell the bootloader about live CD setup
            gfxboot --config-file $gfxcfg \
                --change-config install::livecd=1
            # tell the bootloader to hand over keytable to cmdline
            gfxboot --config-file $gfxcfg \
                --change-config live::addopt.keytable=1
            # tell the bootloader to hand over lang to cmdline
            gfxboot --config-file $gfxcfg \
                --change-config live::addopt.lang=1
        fi
        if [ -e /etc/bootsplash/themes/$loader_theme/bootloader/message ];then
            # boot loader graphics image file (message)...
            mv /etc/bootsplash/themes/$loader_theme/bootloader/message \
                /image/loader
            local archive=/image/loader/message
            # tell the bootloader to hand over keytable to cmdline
            gfxboot --archive $archive \
                --change-config boot::addopt.keytable=1
            # tell the bootloader to hand over lang to cmdline
            gfxboot --archive $archive \
                --change-config boot::addopt.lang=1
            # add selected languages to the bootloader menu
            if [ ! -z "$kiwi_language" ];then
                gfxboot --archive $archive --add-language \
                    $(echo $kiwi_language | tr "," " ") --default-language en_US
            fi
        fi
    else
        #======================================
        # no gfxboot based graphics boot data
        #--------------------------------------
        echo "gfxboot branding not found for $loader_theme theme"
        echo "gfxboot graphics boot skipped !"
    fi
}

#======================================
# rhelSplashToGrub
#--------------------------------------
function rhelSplashToGrub {
    local grub_stage=/usr/lib/grub
    local rhel_logos=/boot/grub/splash.xpm.gz
    if [ ! -e $rhel_logos ];then
        return
    fi
    if [ ! -d $grub_stage ];then
        mkdir -p $grub_stage
    fi
    mv $rhel_logos $grub_stage
}

#======================================
# suseGFXBoot
#--------------------------------------
function suseGFXBoot {
    local theme=$1
    local loader=$2
    local loader_theme=$theme
    local splash_theme=$theme
    export PATH=$PATH:/usr/sbin
    if [ ! -z "$kiwi_splash_theme" ];then
        splash_theme=$kiwi_splash_theme
    fi
    if [ ! -z "$kiwi_loader_theme"  ];then
        loader_theme=$kiwi_loader_theme
    fi
    if [ ! -z "$kiwi_bootloader" ];then
        loader=$kiwi_bootloader
    fi
    if [ "$loader" = "extlinux" ] || [ "$loader" = "syslinux" ];then
        # need the same data for sys|extlinux and for isolinux
        loader="isolinux"
    fi
    if [ "$loader" = "zipl" ];then
        # thanks god, no graphics on s390 :-)
        return
    fi
    #======================================
    # setup gfxboot bootloader data
    #--------------------------------------
    if [ -d /usr/share/gfxboot ];then
        #======================================
        # create boot theme with gfxboot-devel
        #--------------------------------------
        cd /usr/share/gfxboot
        # check for new source layout
        local newlayout=
        [ -f themes/$loader_theme/config ] && newlayout=1
        # create the archive [1]
        [ "$newlayout" ] || make -C themes/$loader_theme prep
        make -C themes/$loader_theme
        # find gfxboot.cfg file
        local gfxcfg=
        if [ "$newlayout" ];then
            if [ $loader = "isolinux" ];then
                gfxcfg=themes/$loader_theme/data-install/gfxboot.cfg
            else
                gfxcfg=themes/$loader_theme/data-boot/gfxboot.cfg
            fi
            if [ ! -f $gfxcfg ];then
                gfxcfg=themes/$loader_theme/src/gfxboot.cfg
            fi
            if [ ! -f $gfxcfg ];then
                echo "gfxboot.cfg not found !"
                echo "install::livecd will be skipped"
                echo "live || boot:addopt.keytable will be skipped"
                echo "live || boot:addopt.lang will be skipped"
                unset gfxcfg
            fi
        fi
        # update configuration for new layout only
        if [ "$newlayout" ] && [ ! -z "$gfxcfg" ];then
            if [ $loader = "isolinux" ];then
                # tell the bootloader about live CD setup
                gfxboot --config-file $gfxcfg \
                    --change-config install::livecd=1
                # tell the bootloader to hand over keytable to cmdline 
                gfxboot --config-file $gfxcfg \
                    --change-config live::addopt.keytable=1
                # tell the bootloader to hand over lang to cmdline
                gfxboot --config-file $gfxcfg \
                    --change-config live::addopt.lang=1
            else
                # tell the bootloader to hand over keytable to cmdline 
                gfxboot --config-file $gfxcfg \
                    --change-config boot::addopt.keytable=1
                # tell the bootloader to hand over lang to cmdline
                gfxboot --config-file $gfxcfg \
                    --change-config boot::addopt.lang=1
                # add selected languages to the bootloader menu
                if [ ! -z "$kiwi_language" ];then
                    for l in `echo $kiwi_language | tr "," " "`;do
                        echo "Adding language: $l"
                        echo $l >> themes/$loader_theme/data-boot/languages
                    done
                fi
            fi
        fi
        # create the archive [2]
        [ "$newlayout" ] || make -C themes/$loader_theme prep
        make -C themes/$loader_theme
        # copy result files
        test -d /image/loader || mkdir /image/loader
        local gfximage=themes/$loader_theme/install/bootlogo
        local bootimage=themes/$loader_theme/boot/message
        if [ "$newlayout" ] ; then
            gfximage=themes/$loader_theme/bootlogo
            bootimage=themes/$loader_theme/message
        fi
        cp $gfximage /image/loader
        bin/unpack_bootlogo /image/loader
        if [ ! -z "$kiwi_language" ];then
            msgdir=/image/loader/message.dir
            mkdir $msgdir && mv $bootimage $msgdir
            (cd $msgdir && cat message | cpio -i && rm -f message)
            if [ "$newlayout" ];then
                for l in `echo $kiwi_language | tr "," " "`;do
                    l=$(echo $l | cut -f1 -d_)
                    cp themes/$loader_theme/po/$l*.tr $msgdir
                    cp themes/$loader_theme/help-boot/$l*.hlp $msgdir
                done
            else
                for l in `echo $kiwi_language | tr "," " "`;do
                    l=$(echo $l | cut -f1 -d_)
                    cp themes/$loader_theme/boot/$l*.tr  $msgdir
                    cp themes/$loader_theme/boot/$l*.hlp $msgdir
                    echo $l >> $msgdir/languages
                done
            fi
            (cd $msgdir && find | cpio --quiet -o > ../message)
            rm -rf $msgdir
        else
            mv $bootimage /image/loader
        fi
        make -C themes/$loader_theme clean
    elif [ -f /etc/bootsplash/themes/$loader_theme/bootloader/message ];then
        #======================================
        # use boot theme from gfxboot-branding
        #--------------------------------------
        echo "gfxboot devel not installed, custom branding skipped !"
        echo "using gfxboot branding package"
        test -d /image/loader || mkdir /image/loader
        if [ -e "/etc/bootsplash/themes/$loader_theme/cdrom/gfxboot.cfg" ];then
            # isolinux boot graphics file (bootlogo)...
            mv /etc/bootsplash/themes/$loader_theme/cdrom/* /image/loader
            local gfxcfg=/image/loader/gfxboot.cfg
            # tell the bootloader about live CD setup
            gfxboot --config-file $gfxcfg \
                --change-config install::livecd=1
            # tell the bootloader to hand over keytable to cmdline 
            gfxboot --config-file $gfxcfg \
                --change-config live::addopt.keytable=1
            # tell the bootloader to hand over lang to cmdline
            gfxboot --config-file $gfxcfg \
                --change-config live::addopt.lang=1
        fi
        if [ -e /etc/bootsplash/themes/$loader_theme/bootloader/message ];then
            # boot loader graphics image file (message)...
            mv /etc/bootsplash/themes/$loader_theme/bootloader/message \
                /image/loader
            local archive=/image/loader/message
            # tell the bootloader to hand over keytable to cmdline 
            gfxboot --archive $archive \
                --change-config boot::addopt.keytable=1
            # tell the bootloader to hand over lang to cmdline
            gfxboot --archive $archive \
                --change-config boot::addopt.lang=1
            # add selected languages to the bootloader menu
            if [ ! -z "$kiwi_language" ];then
                gfxboot --archive $archive --add-language \
                    $(echo $kiwi_language | tr "," " ") --default-language en_US
            fi
        fi
    else
        #======================================
        # no gfxboot based graphics boot data
        #--------------------------------------
        echo "gfxboot devel not installed"
        echo "gfxboot branding not installed"
        echo "gfxboot graphics boot skipped !"
        test -d /image/loader || mkdir /image/loader
    fi
    #======================================
    # setup grub2 bootloader data
    #--------------------------------------
    if [ -d /usr/share/grub2/themes/$loader_theme ];then
        #======================================
        # use boot theme from grub2-branding
        #--------------------------------------
        echo "using grub2 branding data"
        mv /boot/grub2/themes/$loader_theme/background.png \
            /usr/share/grub2/themes/$loader_theme
        test -d /image/loader || mkdir /image/loader
    else
        #======================================
        # no grub2 based graphics boot data
        #--------------------------------------
        echo "grub2 branding not installed"
        echo "grub2 graphics boot skipped !"
        test -d /image/loader || mkdir /image/loader
    fi
    #======================================
    # copy bootloader binaries if required
    #--------------------------------------
    if [ "$loader" = "uboot" ] || [ "$loader" = "berryboot" ];then
        # uboot loaders
        if [ -f /boot/MLO ];then
            mv /boot/MLO /image/loader
        fi
        if [ -d /boot/vc ];then
            mv /boot/vc /image/loader
        fi
        mv /boot/*.dat /image/loader &>/dev/null
        mv /boot/*.bin /image/loader &>/dev/null
        mv /boot/*.img /image/loader &>/dev/null
        mv /boot/*.imx /image/loader &>/dev/null
        mv /boot/*.dtb /image/loader &>/dev/null
        mv /boot/dtb*  /image/loader &>/dev/null
        mv /boot/*.elf /image/loader &>/dev/null
    else
        # boot loader binaries
        :
    fi
    #======================================
    # copy isolinux loader data
    #--------------------------------------
    # isolinux boot code...
    if [ -f /usr/share/syslinux/isolinux.bin ];then
        mv /usr/share/syslinux/isolinux.bin /image/loader
    elif [ -f /usr/lib/syslinux/isolinux.bin ];then
        mv /usr/lib/syslinux/isolinux.bin  /image/loader
    fi
    # use either gfxboot.com or gfxboot.c32
    if [ -f /usr/share/syslinux/gfxboot.com ];then
        mv /usr/share/syslinux/gfxboot.com /image/loader
    elif [ -f /usr/share/syslinux/gfxboot.c32 ];then
        mv /usr/share/syslinux/gfxboot.c32 /image/loader
    fi
    # add menu capabilities for non graphics boot
    if [ -f /usr/share/syslinux/menu.c32 ];then
        mv /usr/share/syslinux/menu.c32 /image/loader
    fi
    if [ -f /usr/share/syslinux/chain.c32 ];then
        mv /usr/share/syslinux/chain.c32 /image/loader
    fi
    if [ -f /usr/share/syslinux/mboot.c32 ];then
        mv /usr/share/syslinux/mboot.c32 /image/loader
    fi
    if [ -f /boot/memtest* ];then
        mv /boot/memtest* /image/loader/memtest
    fi
    #======================================
    # create splash screen
    #--------------------------------------
    if [ -d /usr/share/plymouth/themes/$splash_theme ];then
        echo "plymouth splash system is used"
        touch "/plymouth.splash.active"
        return
    fi
    if [ ! -f /sbin/splash ];then
        echo "bootsplash not installed... skipped"
        return
    fi
    sname[0]="08000600.spl"
    sname[1]="10240768.spl"
    sname[2]="12801024.spl"
    index=0
    if [ ! -d /etc/bootsplash/themes/$splash_theme ];then
        theme="SuSE-$splash_theme"
    fi
    if [ ! -d /etc/bootsplash/themes/$splash_theme ];then
        echo "bootsplash branding not installed... skipped"
        return
    fi
    mkdir -p /image/loader/branding
    cp /etc/bootsplash/themes/$splash_theme/images/logo.mng \
        /image/loader/branding
    cp /etc/bootsplash/themes/$splash_theme/images/logov.mng \
        /image/loader/branding
    for cfg in 800x600 1024x768 1280x1024;do
        cp /etc/bootsplash/themes/$splash_theme/images/bootsplash-$cfg.jpg \
        /image/loader/branding
        cp /etc/bootsplash/themes/$splash_theme/images/silent-$cfg.jpg \
        /image/loader/branding
        cp /etc/bootsplash/themes/$splash_theme/config/bootsplash-$cfg.cfg \
        /image/loader/branding
    done
    mkdir -p /image/loader/animations
    cp /etc/bootsplash/themes/$splash_theme/animations/* \
        /image/loader/animations &>/dev/null
    for cfg in 800x600 1024x768 1280x1024;do
        /sbin/splash -s -c -f \
            /etc/bootsplash/themes/$splash_theme/config/bootsplash-$cfg.cfg |\
            gzip -9c \
        > /image/loader/${sname[$index]}
        tdir=/image/loader/xxx
        mkdir $tdir
        cp -a --parents /etc/bootsplash/themes/$splash_theme/config/*-$cfg.* \
            $tdir
        cp -a --parents /etc/bootsplash/themes/$splash_theme/images/*-$cfg.* \
            $tdir
        ln -s /etc/bootsplash/themes/$splash_theme/config/bootsplash-$cfg.cfg \
                $tdir/etc/splash.cfg
        pushd $tdir
        chmod -R a+rX .
        find | cpio --quiet -o -H newc |\
            gzip -9 >> /image/loader/${sname[$index]}
        popd
        rm -rf $tdir
        index=`expr $index + 1`
    done
}

#======================================
# suseSetupProductInformation
#--------------------------------------
function suseSetupProductInformation {
    # /.../
    # This function will use zypper to search for the installed
    # product and prepare the product specific information
    # for YaST
    # ----
    if [ ! -x /usr/bin/zypper ];then
        echo "zypper not installed... skipped"
        return
    fi
    local zypper="zypper --non-interactive --no-gpg-checks"
    local product=$($zypper search -t product | grep product | head -n 1)
    local p_alias=$(echo $product | cut -f4 -d'|')
    local p_name=$(echo $product | cut -f 4-5 -d'|' | tr '|' '-' | tr -d " ")
    p_alias=$(echo $p_alias)
    p_name=$(echo $p_name)
    echo "Installing product information for $p_name"
    $zypper install -t product $p_alias
}

#======================================
# baseStripFirmware
#--------------------------------------
function baseStripFirmware {
    # /.../
    # check all kernel modules if they require a firmware and
    # strip out all firmware files which are not referenced
    # by a kernel module
    # ----
    local base=/lib/modules
    local name
    local bmdir
    mkdir -p /lib/firmware-required
    find $base -name "*.ko" | xargs modinfo | grep ^firmware | while read i;do
        name=$(echo $(echo $i | cut -f2 -d:))
        if [ -z "$name" ];then
            continue
        fi
        for match in /lib/firmware/$name /lib/firmware/*/$name;do
            if [ -e $match ];then
                match=$(echo $match | sed -e 's@\/lib\/firmware\/@@')
                bmdir=$(dirname $match)
                mkdir -p /lib/firmware-required/$bmdir
                mv /lib/firmware/$match /lib/firmware-required/$bmdir
            else
                echo "Deleting unwanted firmware: $match"
            fi
        done
    done
    rm -rf /lib/firmware
    mv /lib/firmware-required /lib/firmware
}

#======================================
# baseStripModules
#--------------------------------------
function baseStripModules {
    # /.../
    # search for update modules and remove the old version
    # which might be provided by the standard kernel
    # ----
    local kernel=/lib/modules
    local files=$(find $kernel -type f -name "*.ko")
    local mlist=$(for i in $files;do echo $i;done | sed -e s@.*\/@@g | sort)
    local count=1
    local mosum=1
    local modup
    #======================================
    # create sorted module array
    #--------------------------------------
    for mod in $mlist;do
        name_list[$count]=$mod
        count=$((count + 1))
    done
    count=1
    #======================================
    # find duplicate modules by their name
    #--------------------------------------
    while [ $count -lt ${#name_list[*]} ];do
        mod=${name_list[$count]}
        mod_next=${name_list[$((count + 1))]}
        if [ "$mod" = "$mod_next" ];then
            mosum=$((mosum + 1))
        else
            if [ $mosum -gt 1 ];then
                modup="$modup $mod"
            fi
            mosum=1
        fi
        count=$((count + 1))
    done
    #======================================
    # sort out duplicates prefer updates
    #--------------------------------------
    if [ -z "$modup" ];then
        echo "baseStripModules: No old versions for update drivers found"
        return
    fi
    for file in $files;do
        for mod in $modup;do
            if [[ $file =~ $mod ]] && [[ ! $file =~ "updates" ]];then
                echo "baseStripModules: Update driver found for $mod"
                echo "baseStripModules: Removing old version: $file"
                rm -f $file
            fi
        done
    done
}

#======================================
# baseCreateKernelTree
#--------------------------------------
function baseCreateKernelTree {
    echo "Creating copy of kernel tree for strip operations"
    mkdir -p /kernel-tree
    cp -a /lib/modules/* /kernel-tree/
}

#======================================
# baseSyncKernelTree
#--------------------------------------
function baseSyncKernelTree {
    echo "Replace kernel tree with downsized version"
    rm -rf /lib/modules/*
    cp -a /kernel-tree/* /lib/modules/
    rm -rf /kernel-tree
}

#======================================
# baseKernelDriverMatches
#--------------------------------------
function baseKernelDriverMatches {
    module=$1
    for pattern in $(echo $kiwi_drivers | tr , ' '); do
        if [[ $module =~ $pattern ]];then
            return 0
        fi
    done
    return 1
}

#======================================
# baseStripKernelModules
#--------------------------------------
function baseStripKernelModules {
    for kernel_dir in /kernel-tree/*;do
        kernel_version=$(/usr/bin/basename $kernel_dir)
        if [ ! -d /kernel-tree/$kernel_version/kernel ]; then
            continue
        fi
        echo "Downsizing kernel modules for $kernel_dir"
        for module in $(
            find /kernel-tree/$kernel_version/kernel -name "*.ko" | sort
        ); do
            if ! baseKernelDriverMatches $module; then
                echo "Deleting unwanted module: $module"
                rm -f $module
            fi
        done
    done
}

#======================================
# baseFixupKernelModuleDependencies
#--------------------------------------
function baseFixupKernelModuleDependencies {
    local kernel_dir
    local kernel_version
    local module
    local module_name
    local module_info
    local dependency
    for kernel_dir in /kernel-tree/*;do
        echo "Checking kernel dependencies for $kernel_dir"
        kernel_version=$(/usr/bin/basename $kernel_dir)

        for module in $(find /kernel-tree/$kernel_version -name "*.ko");do
            module_name=$(/usr/bin/basename $module)
            module_info=$(/sbin/modprobe \
                --set-version $kernel_version --ignore-install --show-depends \
                ${module_name%.ko} | sed -ne 's:.*insmod /\?::p'
            )

            for dependency in $module_info; do
                if [ ! -f /$dependency ]; then
                    continue
                fi
                dependency_module=$(echo ${dependency/lib\/modules/kernel-tree})
                if [ ! -f $dependency_module ];then
                    echo -e "Fix $module:\n  --> needs: $dependency_module"
                    mkdir -p $(/usr/bin/dirname $dependency_module)
                    cp -a $dependency $dependency_module
                fi
            done
        done
    done
}

#======================================
# baseCreateCommonKernelFile
#--------------------------------------
function baseCreateCommonKernelFile {
    # /.../
    # Search for the kernel file name and move them into
    # a common file name used by kiwi
    # ----
    local kernel_dir
    local kernel_names
    local kernel_name
    local kernel_version
    for kernel_dir in /lib/modules/*;do
        if [ ! -d "$kernel_dir" ];then
            continue
        fi
        if [ -x /bin/rpm ];then
            # if we have a package database take the kernel name from
            # the package name. This could result in multiple kernel
            # names
            kernel_names=$(rpm -qf $kernel_dir)
        else
            # without a package database take the installed kernel
            # directory name as the kernel name
            kernel_names=$kernel_dir
        fi
        for kernel_name in $kernel_names;do
            #==========================================
            # get kernel VERSION information
            #------------------------------------------
            if [ ! $? = 0 ];then
                # not in a package...
                continue
            fi
            if echo $kernel_name | grep -q "\-kmp\-";then
                # a kernel module package...
                continue
            fi
            if echo $kernel_name | grep -q "\-source\-";then
                # a kernel source package...
                continue
            fi
            kernel_version=$(/usr/bin/basename $kernel_dir)
            #==========================================
            # run depmod, deps should be up to date
            #------------------------------------------
            if [ ! -f /boot/System.map-$kernel_version ];then
                # no system map for this kernel
                echo "no system map for kernel: $kernel_name found... skip it"
                continue
            fi
            /sbin/depmod -F /boot/System.map-$kernel_version $kernel_version
            #==========================================
            # create common kernel files, last wins !
            #------------------------------------------
            pushd /boot
            if [ -f uImage-$kernel_version ];then
                # dedicated to kernels on arm
                mv uImage-$kernel_version vmlinuz
            elif [ -f Image-$kernel_version ];then
                # dedicated to kernels on arm
                mv Image-$kernel_version vmlinuz
            elif [ -f zImage-$kernel_version ];then
                # dedicated to kernels on arm
                mv zImage-$kernel_version vmlinuz
            elif [ -f vmlinuz-${kernel_version}.gz ];then
                # dedicated to kernels on x86
                mv vmlinuz-$kernel_version vmlinuz
            elif [ -f vmlinuz-${kernel_version}.el5 ];then
                # dedicated to kernels on ppc
                mv vmlinux-${kernel_version}.el5 vmlinuz
            elif [ -f vmlinux-$kernel_version ];then
                # dedicated to kernels on ppc
                mv vmlinux-$kernel_version vmlinux
            elif [ -f image-$kernel_version ];then
                # dedicated to kernels on s390
                mv image-$kernel_version vmlinuz
            elif [ -f vmlinuz-$kernel_version ];then
                # dedicated to xz kernels
                mv vmlinuz-$kernel_version vmlinuz
            elif [ -f vmlinuz ];then
                # nothing to map, vmlinuz already there
                :
            else
                echo "Failed to find a mapping kernel"
            fi
            if [ -f vmlinux-${kernel_version}.gz ];then
                mv vmlinux-${kernel_version}.gz vmlinux.gz
            fi
            popd
        done
    done
}

#======================================
# baseStripKernel
#--------------------------------------
function baseStripKernel {
    # /.../
    # this function will strip the kernel according to the drivers
    # information in the xml description. It also creates the
    # vmlinux.gz and vmlinuz files which are required for the
    # kernel extraction in case of kiwi boot images
    # ----
    baseCreateCommonKernelFile
    if [ "$kiwi_initrd_system" = "dracut" ]; then
        echo "dracut initrd system requested, kernel strip skipped"
    else
        baseCreateKernelTree
        baseStripKernelModules
        baseFixupKernelModuleDependencies
        baseSyncKernelTree
        baseStripModules
        baseStripFirmware
    fi
}

#======================================
# suseStripKernel
#--------------------------------------
function suseStripKernel {
    baseStripKernel
}

#======================================
# rhelStripKernel
#--------------------------------------
function rhelStripKernel {
    baseStripKernel
}

#======================================
# debianStripKernel
#--------------------------------------
function debianStripKernel {
    baseStripKernel
}

#======================================
# suseSetupProduct
#--------------------------------------
function suseSetupProduct {
    # /.../
    # This function will create the /etc/products.d/baseproduct
    # link pointing to the product referenced by either
    # the /etc/SuSE-brand or /etc/os-release file or the latest .prod file
    # available in /etc/products.d
    # ----
    local prod=undef
    if [ -f /etc/SuSE-brand ];then
        prod=$(head /etc/SuSE-brand -n 1)
    elif [ -f /etc/os-release ];then
        prod=$(grep "^NAME" /etc/os-release | cut -d '=' -f 2 | cut -d '"' -f 2)
    fi
    if [ -d /etc/products.d ];then
        pushd /etc/products.d
        if [ -f "${prod}.prod" ];then
            ln -sf "${prod}.prod" baseproduct
        elif [ -f "SUSE_${prod}.prod" ];then
            ln -sf "SUSE_${prod}.prod" baseproduct
        else
            prod=$(ls -1t *.prod 2>/dev/null | tail -n 1)
            if [ -f "$prod" ];then
                ln -sf "$prod" baseproduct
            fi
        fi
        popd
    fi
}

#======================================
# baseSetRunlevel
#--------------------------------------
function baseSetRunlevel {
    # /.../
    # Set the systemd default target link according to the
    # specified value Examples:
    #
    # baseSetRunlevel 5
    #   --> set graphical.target as systemd default
    #
    # baseSetRunlevel shutdown.target
    #   --> set shutdown.target as systemd default
    #
    # ----
    local target=$1
    local systemd_system=/usr/lib/systemd/system
    local systemd_default=/etc/systemd/system/default.target
    local systemd_consoles=$systemd_system/multi-user.target
    local systemd_graphics=$systemd_system/graphical.target
    case "$target" in
        1|2|3|5)
            # /.../
            # Given target is a number, map the number to a service
            # We only allow console or graphics mode
            # ----
            if [ $target -lt 5 ];then
                ln -sf $systemd_consoles $systemd_default
            else
                ln -sf $systemd_graphics $systemd_default
            fi
        ;;
        *)
            # /.../
            # Given target is a raw name; use this as systemd target
            # name and setup this target name as the default target
            # ----
            if [ -e $systemd_system/$target ]; then
                ln -sf $systemd_system/$target $systemd_default
            else
                echo "Can't find systemd target: $target"
            fi
        ;;
    esac
}

#======================================
# suseRemovePackagesMarkedForDeletion
#--------------------------------------
function suseRemovePackagesMarkedForDeletion {
    # /.../
    # This function removes all packages which are
    # added into the <packages type="delete"> section
    # ----
    local packs=$(baseGetPackagesForDeletion)
    local final=$(rpm -q $packs | grep -v 'is not installed')
    echo "suseRemovePackagesMarkedForDeletion: $final"
    Rpm -e --nodeps --noscripts $final
}

#======================================
# suseRemoveYaST
#--------------------------------------
function suseRemoveYaST {
    if [ -e /etc/YaST2/firstboot.xml ];then
        return
    fi
    if [ -e /var/lib/autoinstall/autoconf/autoconf.xml ];then
        return
    fi
    rpm -qa | grep yast | xargs rpm -e --nodeps
}

#======================================
# baseDisableCtrlAltDel
#--------------------------------------
function baseDisableCtrlAltDel {
    # /.../
    # This function disables the Ctrl-Alt-Del key sequence
    # ---
    sed -i "s/ca::ctrlaltdel/#ca::ctrlaltdel/" /etc/inittab
}

#======================================
# baseSetupBootLoaderCompatLinks
#--------------------------------------
function baseSetupBootLoaderCompatLinks {
    if [ ! -d /usr/lib/grub ];then
        mkdir -p /usr/lib/grub
        cp -l /usr/share/grub/*/* /usr/lib/grub
    fi
}

#======================================
# baseQuoteFile
#--------------------------------------
function baseQuoteFile {
    local file=$1
    local conf=$file.quoted
    # create clean input, no empty lines and comments
    cat $file | grep -v '^$' | grep -v '^[ \t]*#' > $conf
    # remove start/stop quoting from values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=[\"']\(.*\)[\"']#\1=\2#" $conf
    # remove backslash quotes if any
    sed -i -e s"#\\\\\(.\)#\1#g" $conf
    # quote simple quotation marks
    sed -i -e s"#'#'\\\\''#g" $conf
    # add '...' quoting to values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=\(.*\)#\1='\2'#" $conf
    mv $conf $file
}

#======================================
# baseSetupBuildDay
#--------------------------------------
function baseSetupBuildDay {
    local buildDay="$(LC_ALL=C date -u '+%Y%m%d')"
    echo "build_day=$buildDay" > /build_day
}

#======================================
# importDatabases
#--------------------------------------
function importDatabases {
    # /.../
    # This function allows the import of databases
    # whose export is stored in /var/cache/dbs/
    # ----
    local dir="/var/cache/dbs"
    local db_type=""
    if [ ! -d $dir ];then
        return
    fi
    for file in $dir/*; do
        if [ -f $file ]; then
            db_type=$(basename "$file" | cut -d. -f1)
        else
            echo "No database found!"
            break
        fi
        echo "Trying to import $db_type database..."
        case "$db_type" in
        'mysql')
            # bring up db
            mysql_install_db --user=mysql
            mysqld_safe --nowatch --user=mysql --skip-networking
            local i
            for((i=0; i<150; i++)); do
                sleep 0.2
                mysqladmin ping 2>/dev/null && break
            done
            # import content
            if zcat $file | mysql -u root; then
                echo "Import of $db_type successfull!"
                rm -f $file
            else
                echo "Import of $db_type failed!"
            fi
            mysqladmin shutdown
        ;;
        *)
            echo "Ignoring unknown database type $db_type!"
        ;;
        esac
    done
}

# vim: set noexpandtab:
