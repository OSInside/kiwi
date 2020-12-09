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
#             IMPORTANT
#======================================
# If you change *anything* in this file
# PLEASE also adapt the documentation
# in doc/source/working_with_kiwi/shell_scripts.rst
#======================================
#             IMPORTANT
#======================================

#======================================
# work in POSIX environment
#--------------------------------------
export LANG=C
export LC_ALL=C
#======================================
# check base tools
#--------------------------------------
for tool in basename dirname;do
    if [ -x "/bin/${tool}" ] && [ ! -e "/usr/bin/${tool}" ];then
        ln -s "/bin/${tool}" "/usr/bin/${tool}"
    fi
done
for tool in setctsid klogconsole;do
    if [ -x "/usr/bin/${tool}" ] && [ ! -e "/usr/sbin/${tool}" ];then
        ln -s "/usr/bin/${tool}" "/usr/sbin/${tool}"
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
            echo "${dir}/${service}.service"
            return
        fi
        if [ -f "${dir}/${service}.mount" ];then
            echo "${dir}/${service}.mount"
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
    local service
    local legacy_service
    service=$(baseSystemdServiceInstalled "${service_name}")
    if [ -n "${service}" ];then
        systemctl "$@" "${service_name}"
    else
        legacy_service=$(baseSysVServiceInstalled "${service_name}")
        if [ -n "${legacy_service}" ];then
            # systemd is sysV init compatible and still allows
            # to enable those type of services
            systemctl "$@" "${legacy_service}"
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
    baseSystemdCall "${service}" "enable"
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
    baseSystemdCall "${service}" "disable"
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
    if [ -z "${target}" ];then
        echo "baseService: no target specified"
        return
    fi
    if [ -z "${service}" ];then
        echo "baseService: no service name specified"
        return
    fi
    if [ "${target}" = off ];then
        baseRemoveService "${service}"
    else
        baseInsertService "${service}"
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
    baseService "$@"
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
    for service in "${services[@]}";do
        echo "Activating service: ${service}"
        baseInsertService "${service}"
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
    local TDIR
    local KFN
    local dumpsigs=/usr/lib/rpm/gnupg/dumpsigs
    TDIR=$(mktemp -d)
    if [ ! -d "${TDIR}" ]; then
        echo "suseImportBuildKey: Failed to create temp dir"
        return
    fi
    if [ -d "/usr/lib/rpm/gnupg/keys" ];then
        pushd "/usr/lib/rpm/gnupg/keys" || return
    else
        pushd "${TDIR}" || return
        if [ -x "${dumpsigs}" ];then
            ${dumpsigs} /usr/lib/rpm/gnupg/suse-build-key.gpg
        fi
    fi
    for KFN in gpg-pubkey-*.asc; do
        if [ ! -e "${KFN}" ];then
            #
            # check if file exists because if the glob match did
            # not find files bash will use the glob string as
            # result and we just continue in this case
            #
            continue
        fi
        KEY=$(basename "${KFN}" .asc)
        if rpm -q "${KEY}" >/dev/null; then
            continue
        fi
        echo "Importing ${KEY} to rpm database"
        rpm --import "${KFN}"
    done
    popd || return
    rm -rf "${TDIR}"
}

#======================================
# baseSetupUserPermissions
#--------------------------------------
function baseSetupUserPermissions {
    while read -r line;do
        dir=$(echo "${line}" | cut -f6 -d:)
        uid=$(echo "${line}" | cut -f3 -d:)
        usern=$(echo "${line}" | cut -f1 -d:)
        group=$(echo "${line}" | cut -f4 -d:)
        shell=$(echo "${line}" | cut -f7 -d:)
        if [ ! -d "${dir}" ];then
            continue
        fi
        if [ "${uid}" -lt 1000 ];then
            continue
        fi
        if [[ ! "${shell}" =~ nologin|true|false ]];then
            group=$(grep "${group}" /etc/group | cut -f1 -d:)
            chown -c -R "${usern}":"${group}" "${dir}"
        fi
    done < /etc/passwd
}

#======================================
# suseConfig
#--------------------------------------
function suseConfig {
    # function kept for compatibility
    return
}

#======================================
# baseGetPackagesForDeletion
#--------------------------------------
function baseGetPackagesForDeletion {
    declare kiwi_delete=${kiwi_delete}
    echo "${kiwi_delete}"
}

#======================================
# baseGetProfilesUsed
#--------------------------------------
function baseGetProfilesUsed {
    declare kiwi_profiles=${kiwi_profiles}
    echo "${kiwi_profiles}"
}

#======================================
# baseCleanMount
#--------------------------------------
function baseCleanMount {
    echo "DEPRECATED: ${FUNCNAME[0]} is obsolete and only exists as noop method"
}

#======================================
# baseMount
#--------------------------------------
function baseMount {
    echo "DEPRECATED: ${FUNCNAME[0]} is obsolete and only exists as noop method"
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
    local keepMans="$*"
    local directories="
        /opt/gnome/share/man
        /usr/local/man
        /usr/share/man
        /opt/kde3/share/man/packages
    "
    find "${directories}" -mindepth 1 -maxdepth 2 -type f 2>/dev/null |\
        baseStripAndKeep "${keepMans}"
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
    local dir
    local directories="
        /opt/gnome/share/doc/packages
        /usr/share/doc/packages
        /opt/kde3/share/doc/packages
    "
    for dir in ${directories}; do
        docfiles=$(find "${dir}" -type f |\
            grep -iv "copying\|license\|copyright")
        rm -f "${docfiles}"
    done
    rm -rf /usr/share/info
    rm -rf /usr/share/man
}

#======================================
# baseStripLocales
#--------------------------------------
function baseStripLocales {
    local keepLocales="$*"
    find /usr/lib/locale -mindepth 1 -maxdepth 1 -type d 2>/dev/null |\
        baseStripAndKeep "${keepLocales}"
}

#======================================
# baseStripTranslations
#--------------------------------------
function baseStripTranslations {
    local keepMatching="$*"
    find /usr/share/locale -name "*.mo" |\
        grep -v "${keepMatching}" | xargs rm -f
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
    local keepInfos="$*"
    find /usr/share/info -mindepth 1 -maxdepth 1 -type f 2>/dev/null |\
        baseStripAndKeep "${keepInfos}"
}

#======================================
# baseStripAndKeep
#--------------------------------------
function baseStripAndKeep {
    # /.../
    # helper function for the baseStrip* functions
    # reads the list of files to check from stdin for removing
    # - params - files which should be kept
    # ----
    local keepFiles="$*"
    local found
    local baseFile
    local keep
    local file
    while read -r file; do
        baseFile=$(/usr/bin/basename "${file}")
        found=0
        for keep in ${keepFiles};do
            if echo "${baseFile}" | grep -q "${keep}"; then
                found=1
                break
            fi
        done
        if [ "${found}" = 0 ]; then
             Rm -rf "${file}"
        fi
    done
}
#======================================
# baseStripTools {list of toolpath} {list of tools}
# Helper function for suseStripInitrd
# function parameters: toolpath, tools.
#--------------------------------------
function baseStripTools {
    local tpath=$1
    local tools=$2
    local found
    local file
    local IFS
    find "${tpath}" -print0 | \
    while IFS= read -r -d $'\0' file; do
        found=0
        base=$(/usr/bin/basename "${file}")
        for need in ${tools};do
            if [ "${base}" = "$need" ];then
                found=1
                break
            fi
        done
        if [ "${found}" = 0 ] && [ ! -d "${file}" ];then
            Rm -fv "${file}"
        fi
    done
}
#======================================
# Rm
#--------------------------------------
function Rm {
    # /.../
    # delete files & anounce it to log
    # ----
    Debug "rm $*"
    rm "$@"
}

#======================================
# Rpm
#--------------------------------------
function Rpm {
    # /.../
    # all rpm function & anounce it to log
    # ----
    Debug "rpm $*"
    rpm "$@"
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
        case ${option} in
            b) prefix="      " ;;
            n) optn="-n" ;;
            e) opte="-e" ;;
            *) echo "Invalid argument: ${option}" ;;
        esac
    done
    shift $((OPTIND - 1))
    echo "${optn}" "${opte}" "${prefix} $1"
    OPTIND=1
}
#======================================
# Debug
#--------------------------------------
function Debug {
    # /.../
    # print message if variable DEBUG is set to 1
    # -----
    if test "${DEBUG:-0}" = 1;then
        echo "+++++> (caller:${FUNCNAME[1]}:${FUNCNAME[2]} )  $*"
    fi
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
    local lib
    local lddref
    # /.../
    # Find directly used libraries, by calling ldd
    # on files in *bin*
    # ---
    ldconfig
    rm -f /tmp/needlibs
    for i in /usr/bin/* /bin/* /sbin/* /usr/sbin/* /lib/systemd/systemd-*;do
        for n in $(ldd "$i" 2>/dev/null | cut -f2- -d "/" | cut -f1 -d " ");do
            if [ ! -e "/$n" ];then
                continue
            fi
            lddref="/$n"
            while true;do
                if lib=$(readlink "${lddref}"); then
                    lddref="${lib}"
                    continue
                fi
                break
            done
            lddref=$(basename "${lddref}")
            echo "${lddref}" >> /tmp/needlibs
        done
    done
    count=0
    for i in $(sort /tmp/needlibs | uniq);do
        for d in \
            /lib /lib64 /usr/lib /usr/lib64 \
            /usr/X11R6/lib /usr/X11R6/lib64 \
            /lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
        do
            if [ -e "$d/$i" ];then
                needlibs[${count}]="$d/$i"
                count=$((count + 1))
            fi
        done
    done
    # /.../
    # add exceptions
    # ----
    for libname in $1; do
        for libfile in \
            /lib*/"$libname"* /usr/lib*/"$libname"* \
            /lib/x86_64-linux-gnu/"$libname"* /usr/lib/x86_64-linux-gnu/"$libname"* \
            /usr/X11R6/lib*/"$libname"*
        do
            if [ -e "$libfile" ];then
                needlibs[$count]=$libfile
                count=$((count + 1))
            fi
        done
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
        if [ ! -e "$i" ];then
            continue
        fi
        if [ -d "$i" ];then
            continue
        fi
        if [ -L "$i" ];then
            continue
        fi
        for n in ${needlibs[*]};do
            if [ "$i" = "$n" ];then
                found=1; break
            fi
        done
        if [ "${found}" -eq 0 ];then
            echo "Removing library: $i"
            rm "$i"
        fi
    done
}

#======================================
# baseUpdateSysConfig
#--------------------------------------
function baseUpdateSysConfig {
    # /.../
    # Update the contents of a sysconfig variable
    # ----
    local FILE=$1
    local VAR
    local VAL
    if [ -f "${FILE}" ];then
        VAR=$2
        VAL=$3
        eval sed -i "s'@^\($VAR=\).*\$@\1\\\"$VAL\\\"@'" "${FILE}"
    else
        echo "warning: config file $FILE not found"
    fi
}

#======================================
# baseStripInitrd
#--------------------------------------
function baseStripInitrd {
    declare kiwi_initrd_system=${kiwi_initrd_system}
    declare kiwi_strip_tools=${kiwi_strip_tools}
    declare kiwi_strip_libs=${kiwi_strip_libs}
    #==========================================
    # Check for initrd system
    #------------------------------------------
    if [ "${kiwi_initrd_system}" = "dracut" ]; then
        echo "dracut initrd system requested, initrd strip skipped"
        return
    fi
    #==========================================
    # remove unneeded tools
    #------------------------------------------
    local tools="${kiwi_strip_tools}"
    tools="${tools} $*"
    for path in /sbin /usr/sbin /usr/bin /bin;do
        baseStripTools "${path}" "${tools}"
    done
}

#======================================
# suseStripInitrd
#--------------------------------------
function suseStripInitrd {
    baseStripInitrd "$@"
}

#======================================
# rhelStripInitrd
#--------------------------------------
function rhelStripInitrd {
    baseStripInitrd "$@"
}

#======================================
# debianStripInitrd
#--------------------------------------
function debianStripInitrd {
    baseStripInitrd "$@"
}

#======================================
# rhelSplashToGrub
#--------------------------------------
function rhelSplashToGrub {
    local grub_stage=/usr/lib/grub
    local rhel_logos=/boot/grub/splash.xpm.gz
    if [ ! -e "${rhel_logos}" ];then
        return
    fi
    if [ ! -d "${grub_stage}" ];then
        mkdir -p "${grub_stage}"
    fi
    mv "${rhel_logos}" "${grub_stage}"
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
    local zypper
    local product
    local p_alias
    local p_name
    if [ ! -x /usr/bin/zypper ];then
        echo "zypper not installed... skipped"
        return
    fi
    zypper="zypper --non-interactive --no-gpg-checks"
    product=$("${zypper}" search -t product | grep product | head -n 1)

    p_alias=$(echo "${product}" | cut -f4 -d'|')
    p_name=$(echo "${product}" | cut -f 4-5 -d'|' | tr '|' '-' | tr -d " ")

    echo "Installing product information for $p_name"
    $zypper install -t product "${p_alias}"
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
    local IFS
    local base=/lib/modules
    local name
    local bmdir
    local kernel_module
    local firmware
    mkdir -p /lib/firmware-required
    find "${base}" \( -name "*.ko" -o -name "*.ko.xz" \) -print0 | \
    while IFS= read -r -d $'\0' kernel_module; do
        firmware=$(modinfo "${kernel_module}" | grep ^firmware)
        if [ -z "${firmware}" ];then
            continue
        fi
        name=$(echo "$firmware" | cut -f2 -d:)
        if [ -z "${name}" ];then
            continue
        fi
        # could be more than one, loop
        for fname in $name ; do
            for match in /lib/firmware/"${fname}"      \
                         /lib/firmware/"${fname}".xz   \
                         /lib/firmware/*/"${fname}"    \
                         /lib/firmware/*/"${fname}".xz ;do
                if [ -e "${match}" ];then
                    match="${match//\/lib\/firmware\//}"
                    bmdir=$(dirname "${match}")
                    mkdir -p "/lib/firmware-required/${bmdir}"
                    mv "/lib/firmware/${match}" "/lib/firmware-required/${bmdir}"
                fi
            done
        done
    done
    # Preserve licenses and txt files (which are needed for some firmware blobs)
    find /lib/firmware \( -name 'LICENSE*' -o -name '*txt' \) -print | while read -r match; do
        if [ -e "${match}" ];then
            match="${match//\/lib\/firmware\//}"
            bmdir=$(dirname "${match}")
            mkdir -p "/lib/firmware-required/${bmdir}"
            mv "/lib/firmware/${match}" "/lib/firmware-required/${bmdir}"
        fi
    done
    rm -rf /lib/firmware
    mv /lib/firmware-required /lib/firmware
}

#======================================
# baseStripModules
#--------------------------------------
function baseStripModules {
    # /.../
    # search for updated modules and remove the old version
    # which might be provided by the standard kernel
    # ----
    local kernel=/lib/modules
    local files
    local mlist
    local count=1
    local mosum=1
    local modup
    files=$(find ${kernel} -type f \( -name "*.ko" -o -name "*.ko.xz" \) )
    mlist=$(for i in ${files};do echo "$i";done | sed -e "s@.*/@@g" | sort)
    #======================================
    # create sorted module array
    #--------------------------------------
    for mod in ${mlist};do
        name_list[$count]=${mod}
        count=$((count + 1))
    done
    count=1
    #======================================
    # find duplicate modules by their name
    #--------------------------------------
    while [ ${count} -lt ${#name_list[*]} ];do
        mod=${name_list[${count}]}
        mod_next=${name_list[$((count + 1))]}
        if [ "${mod}" = "$mod_next" ];then
            mosum=$((mosum + 1))
        else
            if [ ${mosum} -gt 1 ];then
                modup="${modup} ${mod}"
            fi
            mosum=1
        fi
        count=$((count + 1))
    done
    #======================================
    # sort out duplicates prefer updates
    #--------------------------------------
    if [ -z "${modup}" ];then
        echo "baseStripModules: No old versions for update drivers found"
        return
    fi
    for file in ${files};do
        for mod in $modup;do
            if [[ ${file} =~ ${mod} ]] && [[ ! ${file} =~ "updates" ]];then
                echo "baseStripModules: Update driver found for ${mod}"
                echo "baseStripModules: Removing old version: ${file}"
                rm -f "${file}"
            fi
        done
    done
}

#======================================
# baseCreateKernelTree
#--------------------------------------
function baseCreateKernelTree {
    # Create a copy of the kernel source tree under /kernel-tree/ for stripping
    # operations
    echo "Creating copy of kernel tree for strip operations"
    mkdir -p /kernel-tree
    cp -a /lib/modules/* /kernel-tree/
}

#======================================
# baseSyncKernelTree
#--------------------------------------
function baseSyncKernelTree {
    # Overwrite the original kernel tree with a minimized version from
    # /kernel-tree/.
    echo "Replace kernel tree with downsized version"
    rm -rf /lib/modules/*
    cp -a /kernel-tree/* /lib/modules/
    rm -rf /kernel-tree
}

#======================================
# baseKernelDriverMatches
#--------------------------------------
function baseKernelDriverMatches {
    declare kiwi_drivers=${kiwi_drivers}
    module=$1
    for pattern in $(echo "${kiwi_drivers}" | tr , ' '); do
        if [[ ${module} =~ ${pattern} ]];then
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
        kernel_version=$(/usr/bin/basename "${kernel_dir}")
        if [ ! -d "/kernel-tree/${kernel_version}/kernel" ]; then
            continue
        fi
        echo "Downsizing kernel modules for ${kernel_dir}"
        for module in $(
            find "/kernel-tree/${kernel_version}/kernel" -name "*.ko" -o -name "*.ko.xz" | sort
        ); do
            if ! baseKernelDriverMatches "${module}"; then
                echo "Deleting unwanted module: ${module}"
                rm -f "${module}"
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
    local module_files
    for kernel_dir in /kernel-tree/*;do
        echo "Checking kernel dependencies for ${kernel_dir}"
        kernel_version=$(/usr/bin/basename "${kernel_dir}")
        module_files=$(find "/kernel-tree/${kernel_version}" -name "*.ko" -o -name "*.ko.xz")

        for module in ${module_files};do
            module_u=${module%.xz}
            module_name=$(/usr/bin/basename "${module_u}")
            module_info=$(/sbin/modprobe \
                --set-version "${kernel_version}" --ignore-install \
                --show-depends "${module_name%.ko}" |\
                sed -ne 's:.*insmod /\?::p'
            )

            for dependency in ${module_info}; do
                if [ ! -f "/${dependency}" ]; then
                    continue
                fi
                dependency_module=${dependency/lib\/modules/kernel-tree}
                if [ ! -f "${dependency_module}" ];then
                    echo -e "Fix ${module}:\n  --> needs: ${dependency_module}"
                    mkdir -p "$(/usr/bin/dirname "${dependency_module}")"
                    cp -a "${dependency}" "${dependency_module}"
                fi
            done
        done
    done
}

#======================================
# baseUpdateModuleDependencies
#--------------------------------------
function baseUpdateModuleDependencies {
    local kernel_dir
    local kernel_version
    for kernel_dir in /lib/modules/*;do
        [ -d "${kernel_dir}" ] || continue
        kernel_version=$(/usr/bin/basename "${kernel_dir}")
        if [ -f "/boot/System.map-${kernel_version}" ];then
            /sbin/depmod -F \
                "/boot/System.map-${kernel_version}" "${kernel_version}"
        fi
    done
}

#======================================
# baseStripKernel
#--------------------------------------
function baseStripKernel {
    # /.../
    # this function will strip the kernel
    #
    # 1. handle <strip type="delete"> requests. Because this
    #    information is generic not only files of the kernel
    #    are affected but also other data which is unwanted
    #    gets deleted here
    #
    # 2. only keep kernel modules matching the <drivers>
    #    patterns from the kiwi boot image description
    #
    # 3. lookup kernel module dependencies and bring back
    #    modules which were removed but still required by
    #    other modules kept in the system to stay consistent
    #
    # 4. lookup for duplicate kernel modules due to kernel
    #    module updates and keep only the latest version
    #
    # 5. lookup for kernel firmware files and keep only those
    #    for which a kernel driver is still present in the
    #    system
    # ----
    declare kiwi_initrd_system=${kiwi_initrd_system}
    declare kiwi_strip_delete=${kiwi_strip_delete}
    if [ "${kiwi_initrd_system}" = "dracut" ]; then
        echo "dracut initrd system requested, kernel strip skipped"
    else
        for delete in ${kiwi_strip_delete};do
            echo "Removing file/directory: ${delete}"
            rm -rf "${delete}"
        done
        baseCreateKernelTree
        baseStripKernelModules
        baseFixupKernelModuleDependencies
        baseSyncKernelTree
        baseStripModules
        baseStripFirmware
        baseUpdateModuleDependencies
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
    # This function creates the /etc/products.d/baseproduct
    # link pointing to the product referenced by either
    # /etc/SuSE-brand or /etc/os-release or the latest .prod file
    # available in /etc/products.d
    # ----
    local prod=undef
    if [ -f /etc/SuSE-brand ];then
        prod=$(head /etc/SuSE-brand -n 1)
    elif [ -f /etc/os-release ];then
        prod=$(grep "^NAME" /etc/os-release | cut -d '=' -f 2 | cut -d '"' -f 2)
    fi
    if [ -d /etc/products.d ];then
        pushd /etc/products.d || return
        if [ -f "${prod}.prod" ];then
            ln -sf "${prod}.prod" baseproduct
        elif [ -f "SUSE_${prod}.prod" ];then
            ln -sf "SUSE_${prod}.prod" baseproduct
        else
            prod=$(find . -maxdepth 1 -name "*.prod" 2>/dev/null | tail -n 1)
            if [ -f "${prod}" ];then
                ln -sf "${prod}" baseproduct
            fi
        fi
        popd || return
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
    case "${target}" in
        1|2|3|5)
            # /.../
            # Given target is a number, map the number to a service
            # We only allow console or graphics mode
            # ----
            if [ "${target}" -lt 5 ];then
                ln -sf "${systemd_consoles}" "${systemd_default}"
            else
                ln -sf "${systemd_graphics}" "${systemd_default}"
            fi
        ;;
        *)
            # /.../
            # Given target is a raw name; use this as systemd target
            # name and setup this target name as the default target
            # ----
            if [ -e "${systemd_system}/${target}" ]; then
                ln -sf "${systemd_system}/${target}" "${systemd_default}"
            else
                echo "Can't find systemd target: ${target}"
            fi
        ;;
    esac
}

#======================================
# baseCleanup
#--------------------------------------
function baseCleanup {
    # /.../
    # Delete files from the system which are considered
    # one time initialization files to be re-created on
    # the final target system
    # ----
    # systemd random seed
    rm -f /var/lib/systemd/random-seed
}

#======================================
# suseCleanup
#--------------------------------------
function suseCleanup {
    # /.../
    # Delete files from a SUSE system which are considered
    # one time initialization files to be re-created on
    # the final target system
    # ----
    baseCleanup
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
    local yast_pkgs
    # prevent non-zero exit status when no yast packages were found
    yast_pkgs=$(rpm -qa | grep yast || :)
    if [ "${yast_pkgs}" != "" ];then
        echo "${yast_pkgs}" | xargs rpm -e --nodeps
    fi
}

#======================================
# baseSetupBuildDay
#--------------------------------------
function baseSetupBuildDay {
    local buildDay
    buildDay="$(LC_ALL=C date -u '+%Y%m%d')"
    echo "build_day=${buildDay}" > /build_day
}

#======================================
# baseQuoteFile
#--------------------------------------
function baseQuoteFile {
    local file=$1
    local conf=$file.quoted
    # create clean input, no empty lines and comments
    grep -v '^$' "${file}" | grep -v '^[ \t]*#' > "${conf}"
    # remove start/stop quoting from values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=[\"']\(.*\)[\"']#\1=\2#" "${conf}"
    # remove backslash quotes if any
    sed -i -e s"#\\\\\(.\)#\1#g" "${conf}"
    # quote simple quotation marks
    sed -i -e s"#'\+#'\\\\''#g" "${conf}"
    # add '...' quoting to values
    sed -i -e s"#\(^[a-zA-Z0-9_]\+\)=\(.*\)#\1='\2'#" "${conf}"
    mv "${conf}" "${file}"
}

#======================================
# baseVagrantSetup
#--------------------------------------
function baseVagrantSetup {
    # insert the default insecure ssh key from here:
    # https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub
    mkdir -p /home/vagrant/.ssh/
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key" > /home/vagrant/.ssh/authorized_keys
    chmod 0600 /home/vagrant/.ssh/authorized_keys
    chown -R vagrant:vagrant /home/vagrant/

    # recommended ssh settings for vagrant boxes
    echo "UseDNS no" >> /etc/ssh/sshd_config
    echo "GSSAPIAuthentication no" >> /etc/ssh/sshd_config

    # vagrant assumes that it can sudo without a password
    # => add the vagrant user to the sudoers list
    SUDOERS_LINE="vagrant ALL=(ALL) NOPASSWD: ALL"
    if [ -d /etc/sudoers.d ]; then
        echo "$SUDOERS_LINE" >| /etc/sudoers.d/vagrant
        visudo -cf /etc/sudoers.d/vagrant
        chmod 0440 /etc/sudoers.d/vagrant
    else
        echo "$SUDOERS_LINE" >> /etc/sudoers
        visudo -cf /etc/sudoers
    fi

    # the default shared folder
    mkdir -p /vagrant
    chown -R vagrant:vagrant /vagrant

    # SSH service
    baseInsertService sshd
}

# vim: set noexpandtab:
