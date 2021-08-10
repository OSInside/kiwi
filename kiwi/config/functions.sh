#!/bin/bash
# Copyright (c) 2021 SUSE Software Solutions Germany GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
#======================================
# work in POSIX environment
#--------------------------------------
export LANG=C
export LC_ALL=C

#======================================
# Common Functions
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

function baseSysVServiceInstalled {
    local service=$1
    if [ -x "/etc/init.d/${service}" ];then
        echo "${service}"
    fi
}

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

function baseStripLocales {
    local keepLocales="$*"
    find /usr/lib/locale -mindepth 1 -maxdepth 1 -type d 2>/dev/null |\
        baseStripAndKeep "${keepLocales}"
}

function baseStripTranslations {
    local keepMatching="$*"
    find /usr/share/locale -name "*.mo" |\
        grep -v "${keepMatching}" | xargs rm -f
}

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
            /lib/x86_64-linux-gnu/"$libname"* \
            /usr/lib/x86_64-linux-gnu/"$libname"* \
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
        firmware=$(modinfo "${kernel_module}" | grep ^firmware || :)
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
                    mv "/lib/firmware/${match}" \
                        "/lib/firmware-required/${bmdir}"
                fi
            done
        done
    done
    # Preserve licenses and txt files (which are needed for some firmware blobs)
    find /lib/firmware \( -name 'LICENSE*' -o -name '*txt' \) -print |\
    while read -r match; do
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

function baseStripKernelModules {
    for kernel_dir in /kernel-tree/*;do
        kernel_version=$(/usr/bin/basename "${kernel_dir}")
        if [ ! -d "/kernel-tree/${kernel_version}/kernel" ]; then
            continue
        fi
        echo "Downsizing kernel modules for ${kernel_dir}"
        for module in $(
            find "/kernel-tree/${kernel_version}/kernel" \
                -name "*.ko" -o -name "*.ko.xz" | sort
        ); do
            if ! baseKernelDriverMatches "${module}"; then
                echo "Deleting unwanted module: ${module}"
                rm -f "${module}"
            fi
        done
    done
}

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

function baseSetupBuildDay {
    local buildDay
    buildDay="$(LC_ALL=C date -u '+%Y%m%d')"
    echo "build_day=${buildDay}" > /build_day
}

function baseVagrantSetup {
    # insert the default insecure ssh key from here:
    # https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub
    mkdir -p /home/vagrant/.ssh/
    chmod 0700 /home/vagrant/.ssh/
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key" > /home/vagrant/.ssh/authorized_keys
    chmod 0600 /home/vagrant/.ssh/authorized_keys
    chown -R vagrant:vagrant /home/vagrant/

    # apply recommended ssh settings for vagrant boxes
    SSHD_CONFIG=/etc/ssh/sshd_config.d/99-vagrant.conf
    if [[ ! -d "$(dirname ${SSHD_CONFIG})" ]]; then
        SSHD_CONFIG=/etc/ssh/sshd_config
        # prepend the settings, so that they take precedence
        echo -e "UseDNS no\nGSSAPIAuthentication no\n$(cat ${SSHD_CONFIG})" > ${SSHD_CONFIG}
    else
        echo -e "UseDNS no\nGSSAPIAuthentication no" > ${SSHD_CONFIG}
    fi

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


#======================================
# Common Functions (SUSE)
#--------------------------------------
function suseRemoveService {
    # function kept for compatibility
    baseRemoveService "$@"
}

function suseInsertService {
    # function kept for compatibility
    baseInsertService "$@"
}

function suseService {
    # function kept for compatibility
    baseService "$@"
}

function suseStripInitrd {
    baseStripInitrd "$@"
}

function suseStripKernel {
    baseStripKernel
}

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
        prod=$(while read -r line; do if [[ $line =~ ^NAME ]]; then echo "$line"; fi; done < /etc/os-release | cut -d '=' -f 2 | cut -d '"' -f 2)
    fi
    if [ -d /etc/products.d ];then
        pushd /etc/products.d || return
        if [ -f "${prod}.prod" ];then
            ln -sf "${prod}.prod" baseproduct
        elif [ -f "SUSE_${prod}.prod" ];then
            ln -sf "SUSE_${prod}.prod" baseproduct
        else
            find_prod() {
                for f in *; do
                    if [[ $f =~ \.prod$ ]]; then
                        echo "$f"
                    fi
                done
            }
            prod=$(find_prod | tail -n 1)
            if [ -f "${prod}" ];then
                ln -sf "${prod}" baseproduct
            fi
        fi
        popd || return
    fi
}


#======================================
# Helper methods
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

function Debug {
    # /.../
    # print message if variable DEBUG is set to 1
    # -----
    if test "${DEBUG:-0}" = 1;then
        echo "+++++> (caller:${FUNCNAME[1]}:${FUNCNAME[2]} )  $*"
    fi
}

function baseQuoteFile {
    # /.../
    # Quote file to be shell sourceable
    # -----
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

function baseCreateKernelTree {
    # /.../
    # Create a copy of the kernel source tree under
    # /kernel-tree/ for stripping operations
    # ----
    echo "Creating copy of kernel tree for strip operations"
    mkdir -p /kernel-tree
    cp -a /lib/modules/* /kernel-tree/
}

function baseSyncKernelTree {
    # /.../
    # Overwrite the original kernel tree with a minimized
    # version from /kernel-tree/.
    # ----
    echo "Replace kernel tree with downsized version"
    rm -rf /lib/modules/*
    cp -a /kernel-tree/* /lib/modules/
    rm -rf /kernel-tree
}

function baseFixupKernelModuleDependencies {
    # /.../
    # Browse through the kernel tree and check if kernel
    # module dependencies are broken, if yes fix them
    # ----
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
        module_files=$(
            find "/kernel-tree/${kernel_version}" \
                -name "*.ko" -o -name "*.ko.xz"
        )

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

function baseKernelDriverMatches {
    # /.../
    # Check if the provided kernel module name matches
    # the kiwi driver pattern
    # ----
    declare kiwi_drivers=${kiwi_drivers}
    module=$1
    for pattern in $(echo "${kiwi_drivers}" | tr , ' '); do
        if [[ ${module} =~ ${pattern} ]];then
            return 0
        fi
    done
    return 1
}

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

function baseStripTools {
    # /.../
    # baseStripTools {list of toolpath} {list of tools}
    # Helper function for suseStripInitrd, only keep
    # the provided tools from the list
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

function Rm {
    # /.../
    # delete files & anounce it to log
    # ----
    Debug "rm $*"
    rm "$@"
}

function deprecated {
    {
        echo "DEPRECATED: $1() is obsolete"
        echo "["
        cat
        echo "]"
    } >&2
    exit 1
}


#======================================
# Deprecated methods
#--------------------------------------
function baseCleanMount {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Cleanup operations are a responsibility of the kiwi code
	EOF
}

function baseMount {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Mounting of kernel and other base filesystems are a
	responsibility of the kiwi code
	EOF
}

function suseActivateDefaultServices {
    deprecated "${FUNCNAME[0]}" <<- EOF
	There is no generic applicable list of default services
	It is expected that the installation of software handles
	this properly. Optional services should be handled explicitly
	EOF
}

function baseSetupUserPermissions {
    deprecated "${FUNCNAME[0]}" <<- EOF
	This is done in kiwi by chkstat
	EOF
}

function suseConfig {
    deprecated "${FUNCNAME[0]}" <<- EOF
	suse script no longer present
	EOF
}

function baseGetPackagesForDeletion {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Provided by the kiwi_delete environment variable
	EOF
}

function baseGetProfilesUsed {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Provided by the kiwi_profiles environment variable
	EOF
}

function baseStripMans {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Man pages are marked as documentation by the package manager
	and can be excluded via rpm-excludedocs
	EOF
}

function baseStripDocs {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Documentation lives at different places and a method
	to do this in a common way should not be a responsibility
	of kiwi
	EOF
}

function baseStripInfos {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Info files are marked as documentation by the package manager
	and can be excluded via rpm-excludedocs
	EOF
}

function Rpm {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Please call rpm as it fits in the caller scope
	EOF
}

function rhelStripInitrd {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Useful only in the context of a kiwi created initrd
	This concept was never exposed to RHEL/Fedora
	EOF
}

function debianStripInitrd {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Useful only in the context of a kiwi created initrd
	This concept was never exposed to Debian/Ubuntu
	EOF
}

function rhelStripKernel {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Useful only in the context of a kiwi created initrd
	This concept was never exposed to RHEL/Fedora
	EOF
}

function debianStripKernel {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Useful only in the context of a kiwi created initrd
	This concept was never exposed to Debian/Ubuntu
	EOF
}

function rhelSplashToGrub {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Code based on distros out of support and no longer using kernel splash
	EOF
}

function suseSetupProductInformation {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Utilizes zypper to install a product information.
	Product handling in zypper has changed. The method here
	was based on distros out of support
	EOF
}

function baseCleanup {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Cleanup operations are a responsibility of the kiwi code
	EOF
}

function suseCleanup {
    deprecated "${FUNCNAME[0]}" <<- EOF
	Cleanup operations are a responsibility of the kiwi code
	EOF
}

function suseRemoveYaST {
    deprecated "${FUNCNAME[0]}" <<- EOF
	There is no standard uninstall method for YaST which
	is common across distributions. To prevent installation of
	YaST make sure it does not get pulled in with the packages.
	If this is inevitable delete it based on packages in the
	kiwi delete/uninstall <packages> sections
	EOF
}

# vim: set noexpandtab:
