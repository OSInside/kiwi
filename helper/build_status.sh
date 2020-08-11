#!/bin/bash

for project in \
    Virtualization:Appliances:Images:Testing_x86:suse \
    Virtualization:Appliances:Images:Testing_x86:centos \
    Virtualization:Appliances:Images:Testing_x86:fedora \
    Virtualization:Appliances:Images:Testing_x86:ubuntu \
    Virtualization:Appliances:Images:Testing_s390:suse \
    Virtualization:Appliances:Images:Testing_arm:suse \
    Virtualization:Appliances:Images:Testing_arm:fedora \
    Virtualization:Appliances:Images:Testing_ppc:suse \
    Virtualization:Appliances:Images:Testing_ppc:fedora \
    Virtualization:Appliances:Images:Testing_x86:archlinux
do
    echo "${project}"
    if [ ! "$1" = "refresh" ];then
        osc -A https://api.opensuse.org \
            results -V "${project}" | grep -B100 Legend | grep -v Legend
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
   disabled            
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
