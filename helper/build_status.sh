#!/bin/bash

for project in \
    Virtualization:Appliances:SelfContained:fedora \
    Virtualization:Appliances:SelfContained:tumbleweed \
    Virtualization:Appliances:SelfContained:leap \
    Virtualization:Appliances:SelfContained:ubuntu \
    Virtualization:Appliances:SelfContained:universal \
    Virtualization:Appliances:Images:Testing_x86:tumbleweed \
    Virtualization:Appliances:Images:Testing_x86:rawhide \
    Virtualization:Appliances:Images:Testing_x86:leap \
    Virtualization:Appliances:Images:Testing_x86:centos \
    Virtualization:Appliances:Images:Testing_x86:fedora \
    Virtualization:Appliances:Images:Testing_x86:ubuntu \
    Virtualization:Appliances:Images:Testing_arm:ubuntu \
    Virtualization:Appliances:Images:Testing_x86:debian \
    Virtualization:Appliances:Images:Testing_s390:tumbleweed \
    Virtualization:Appliances:Images:Testing_s390:rawhide \
    Virtualization:Appliances:Images:Testing_arm:tumbleweed \
    Virtualization:Appliances:Images:Testing_arm:fedora \
    Virtualization:Appliances:Images:Testing_ppc:tumbleweed \
    Virtualization:Appliances:Images:Testing_x86:archlinux
do
    echo "${project}"
    if [ ! "$1" = "refresh" ];then
        while read -r line;do
            echo -e "$(echo "${line}" |\
                sed -e s@^F\ @'\\033[31mF \\e[0m'@ |\
                sed -e s@^U\ @'\\033[33mU \\e[0m'@ |\
                sed -e s@^D\ @'\\033[36mD \\e[0m'@ |\
                sed -e s@^\\.@'\\033[32m.\\e[0m'@ |\
                sed -e 's@^x\sF@x \\033[31mF\\e[0m'@ |\
                sed -e 's@^x\sU@x \\033[33mU\\e[0m'@ |\
                sed -e 's@^x\sD@x \\033[36mD\\e[0m'@ |\
                sed -e 's@^x\s\.@x \\033[32m.\\e[0m'@)"
        done < <(osc -A https://api.opensuse.org \
            results -V "${project}" | sed -e 's@^(\s+)  test@D @' |\
            grep -B100 Legend | grep -v Legend
        )
    else
        for package in $(osc -A https://api.opensuse.org list "${project}");do
            if [[ "${package}" =~ ^test- ]];then
                echo -n "[refresh requested for ${package}: ]"
                osc -A https://api.opensuse.org \
                    service remoterun "${project}" "${package}"
            fi
        done
        echo
    fi
done

if [ ! "$1" = "refresh" ];then
cat << EOF
Legend:
 . succeeded
 D Disabled
 U unresolvable
 F failed
 B broken
 b blocked
 % building
 f finished
 s scheduled
 L locked
 x excluded
 d dispatching
 S signing
 ? buildstatus not available
EOF
fi
