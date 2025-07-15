#!/bin/bash
set -exuo pipefail

declare kiwi_profiles=${kiwi_profiles}

#======================================
# Disable recommends
#--------------------------------------
sed -i 's/.*solver.onlyRequires.*/solver.onlyRequires = true/g' \
    /etc/zypp/zypp.conf

#======================================
# Exclude docs installation
#--------------------------------------
sed -i 's/.*rpm.install.excludedocs.*/rpm.install.excludedocs = yes/g' \
    /etc/zypp/zypp.conf

#======================================
# Exclude the installation of multiversion kernels
#--------------------------------------
sed -i 's/^multiversion/# multiversion/' \
    /etc/zypp/zypp.conf

#==========================================
# remove package docs
#------------------------------------------
rm -rf /usr/share/doc/packages/*
rm -rf /usr/share/doc/manual/*

function vagrantSetup {
    # This function configures the image to work as a vagrant box.
    # These are the following steps:
    # - add the vagrant user to /etc/sudoers
    # - insert the insecure vagrant ssh key
    # - create the default /vagrant share
    # - apply some recommended ssh settings

    # insert the default insecure ssh key from here:
    # https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub
    mkdir -p /home/vagrant/.ssh/
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key" > /home/vagrant/.ssh/authorized_keys
    chmod 0600 /home/vagrant/.ssh/authorized_keys
    chown -R vagrant:vagrant /home/vagrant/

    # recommended ssh settings for vagrant boxes
    echo "UseDNS no" >> /usr/etc/ssh/sshd_config
    echo "GSSAPIAuthentication no" >> /usr/etc/ssh/sshd_config

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
    systemctl enable sshd

    # start vboxsf service only if the guest tools are present
    if rpm -q virtualbox-guest-tools 2> /dev/null; then
        echo vboxsf > /etc/modules-load.d/vboxsf.conf
    fi

    # drop any network udev rules for libvirt, so that the networks are called
    # ethX
    # this is not required for Virtualbox as it handles networking differently
    # and doesn't need this hack
    if [ "${kiwi_profiles}" != "virtualbox" ]; then
        rm -f /etc/udev/rules.d/*-net.rules
    fi

    # setup DHCP on eth0 properly
    cat << EOF > /etc/sysconfig/network/ifcfg-eth0
STARTMODE=auto
BOOTPROTO=dhcp
EOF
}
vagrantSetup

#=================================================
# enable haveged to get enough entropy in a VM
#-------------------------------------------------
systemctl enable haveged
