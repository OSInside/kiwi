# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
import os

# project
from .path import Path
from .container_setup_base import ContainerSetupBase


class ContainerSetupDocker(ContainerSetupBase):
    """
        docker container setup
    """
    def post_init(self, custom_args):
        if custom_args:
            self.custom_args = custom_args

    def setup(self):
        Path.create(self.root_dir + '/etc/lxc')

        services_to_deactivate = [
            'device-mapper.service',
            'kbd.service',
            'swap.service',
            'udev.service',
            'proc-sys-fs-binfmt_misc.automount'
        ]

        self.create_fstab()
        self.deactivate_bootloader_setup()
        self.deactivate_root_filesystem_check()
        self.setup_static_device_nodes()
        self.setup_root_console()
        self.create_lxc_fstab()
        self.create_lxc_config()

        for service in services_to_deactivate:
            self.deactivate_systemd_service(service)

    def create_lxc_fstab(self):
        with open(self.root_dir + '/etc/lxc/fstab', 'w') as lxtab:
            lxtab.write(
                'proc /var/lib/lxc/%s/rootfs/proc proc defaults 0 0\n' %
                self.custom_args['container_name']
            )
            lxtab.write(
                'sysfs /var/lib/lxc/%s/rootfs/sys sysfs defaults 0 0\n' %
                self.custom_args['container_name']
            )

    def create_lxc_config(self):
        lxc_name = self.custom_args['container_name']
        host_bind_mounts = [
            # use name resolution setup from host in container
            ' '.join(
                [
                    '/etc/resolv.conf',
                    '/var/lib/lxc/' + lxc_name + '/rootfs/etc/resolv.conf',
                    'none',
                    'bind,ro',
                    '0',
                    '0'
                ]
            )
        ]
        with open(self.root_dir + '/etc/lxc/config', 'w') as lxconf:
            # host bind mount setup
            for bind in host_bind_mounts:
                lxconf.write('lxc.mount.entry = %s\n' % bind)
            # default network setup
            lxconf.write('lxc.network.type = veth\n')
            lxconf.write('lxc.network.flags = up\n')
            lxconf.write('lxc.network.link = br0\n')
            lxconf.write('lxc.network.name = eth0\n')
            # default terminal setup
            lxconf.write('lxc.autodev = 1\n')
            lxconf.write('lxc.tty = 4\n')
            lxconf.write('lxc.kmsg = 0\n')
            lxconf.write('lxc.pts = 1024\n')
            # specify container system root location
            lxconf.write('lxc.rootfs = /var/lib/lxc/%s/rootfs\n' % lxc_name)
            # reference container fstab file
            lxconf.write('lxc.mount = /etc/lxc/%s/fstab\n' % lxc_name)
            lxconf.write('lxc.cgroup.devices.deny = a\n')
            # /dev/null and /dev/zero in cgroup
            lxconf.write('lxc.cgroup.devices.allow = c 1:3 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 1:5 rwm\n')
            # consoles in cgroup
            lxconf.write('lxc.cgroup.devices.allow = c 5:1 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 5:0 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 4:0 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 4:1 rwm\n')
            # /dev/{,u}random in cgroup
            lxconf.write('lxc.cgroup.devices.allow = c 1:9 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 1:8 rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 136:* rwm\n')
            lxconf.write('lxc.cgroup.devices.allow = c 5:2 rwm\n')
            # real time clock in cgroup
            lxconf.write('lxc.cgroup.devices.allow = c 254:0 rwm\n')
