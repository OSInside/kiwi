#!/bin/bash

for image in \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-azure \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-docker \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-docker-derived\
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-ec2 \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-gce \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-iso \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-luks \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-MicroOS \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-oem \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-oem-legacy \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-orthos-oem \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-overlayroot \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-pxe \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-qcow-openstack\
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-tbz \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-vmx \
    Virtualization:Appliances:Images:Testing_x86:suse/test-image-vmx-lvm \
    Virtualization:Appliances:Images:Testing_x86:centos/test-image-iso-oem-vmx \
    Virtualization:Appliances:Images:Testing_x86:fedora/test-image-iso-oem-vmx \
    Virtualization:Appliances:Images:Testing_x86:ubuntu/test-image-iso-oem-vmx \
    Virtualization:Appliances:Images:Testing_s390:suse/test-image-oem \
    Virtualization:Appliances:Images:Testing_s390:suse/test-image-vmx \
    Virtualization:Appliances:Images:Testing_arm:suse/test-image-iso \
    Virtualization:Appliances:Images:Testing_arm:suse/test-image-rpi-oem \
    Virtualization:Appliances:Images:Testing_arm:fedora/test-image-iso \
    Virtualization:Appliances:Images:Testing_ppc:suse/test-image-vmx \
    Virtualization:Appliances:Images:Testing_ppc:fedora/test-image-vmx \
    Virtualization:Appliances:Images:Testing_x86:archlinux/test-image-iso-oem-vmx-kis
do
    project=$(echo "${image}" | cut -f1 -d/)
    package=$(echo "${image}" | cut -f2 -d/)
    if [ "${project_last}" != "${project}" ];then
        echo
        echo "$project"
    fi
    echo "${package}"
    osc -A https://api.opensuse.org \
        results "${project}" "${package}"
    if [ "$1" = "refresh" ];then
        echo -n "[refresh requested: ]"
        osc -A https://api.opensuse.org \
            service remoterun "${project}" "${package}"
    fi
    project_last="${project}"
done
