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
from string import Template
from textwrap import dedent


class VmwareSettingsTemplate(object):
    """
    VMware machine settings template
    """
    def __init__(self):
        self.cr = '\n'

        self.header = dedent('''
            #!/usr/bin/env vmware
            # kiwi generated VMware settings file
            config.version = "8"
            tools.syncTime = "true"
            uuid.action = "create"
            virtualHW.version = "${virtual_hardware_version}"
            displayName = "${display_name}"
            guestOS = "${guest_os}"
        ''').strip() + self.cr

        self.ide_disk = dedent('''
            ide${disk_id}:0.present = "true"
            ide${disk_id}:0.fileName= "${vmdk_file}"
            ide${disk_id}:0.redo = ""
        ''').strip() + self.cr

        self.scsi_disk = dedent('''
            scsi${disk_id}.present = "true"
            scsi${disk_id}.sharedBus = "none"
            scsi${disk_id}.virtualDev = "${scsi_controller_name}"
            scsi${disk_id}:0.present = "true"
            scsi${disk_id}:0.fileName = "${vmdk_file}"
            scsi${disk_id}:0.deviceType = "scsi-hardDisk"
        ''').strip() + self.cr

        self.network = dedent('''
            ethernet{nic_id}.present = "true"
            ethernet{nic_id}.allow64bitVmxnet = "true"
        ''').strip() + self.cr

        self.network_mac_static = dedent('''
            ethernet{nic_id}.addressType = "static"
            ethernet{nic_id}.address = "{mac_address}"
        ''').strip() + self.cr

        self.network_mac_generated = dedent('''
            ethernet{nic_id}.addressType = "generated"
        ''').strip() + self.cr

        self.network_driver = dedent('''
            ethernet{nic_id}.virtualDev = "{network_driver}"
        ''').strip() + self.cr

        self.network_connection_type = dedent('''
            ethernet{nic_id}.connectionType = "{mode}"
        ''').strip() + self.cr

        self.memory = dedent('''
            memsize = "${memory_size}"
        ''').strip() + self.cr

        self.number_of_cpus = dedent('''
            numvcpus = "${number_of_cpus}"
        ''').strip() + self.cr

        self.ide_iso = dedent('''
            ide${iso_id}:0.present = "true"
            ide${iso_id}:0.deviceType = "cdrom-raw"
            ide${iso_id}:0.autodetect = "true"
            ide${iso_id}:0.startConnected = "true"
        ''').strip() + self.cr

        self.scsi_iso = dedent('''
            scsi${iso_id}:0.present = "true"
            scsi${iso_id}:0.deviceType = "cdrom-raw"
            scsi${iso_id}:0.autodetect = "true"
            scsi${iso_id}:0.startConnected = "true"
        ''').strip() + self.cr

        self.usb = dedent('''
            usb.present = "true"
        ''').strip() + self.cr

        self.defaults = dedent('''
            priority.grabbed = "normal"
            priority.ungrabbed = "normal"
            powerType.powerOff = "soft"
            powerType.powerOn  = "soft"
            powerType.suspend  = "soft"
            powerType.reset    = "soft"
        ''').strip() + self.cr

    def get_template(
        self, memory_setup=False, cpu_setup=False, network_setup=False,
        iso_setup=False, disk_controller='ide', iso_controller='ide'
    ):
        """
        VMware machine configuration template

        :param bool memory_setup: with main memory setup true|false
        :param bool cpu_setup: with number of CPU's setup true|false
        :param bool network_setup: with network emulation true|false
        :param bool iso_setup: with CD/DVD drive emulation true|false
        :param string disk_controller: add disk controller setup to template
        :param string iso_controller: add CD/DVD controller setup to template
        :param string network_mac: add static MAC address setup to template
        :param string network_driver: add network driver setup to template
        :param string network_connection_type: add connection type to template

        :rtype: Template
        """
        template_data = self.header
        template_data += self.defaults

        if memory_setup:
            template_data += self.memory

        if cpu_setup:
            template_data += self.number_of_cpus

        if disk_controller == 'ide':
            template_data += self.ide_disk
        else:
            template_data += self.scsi_disk

        if network_setup:
            for nic_id, nic_setup in list(network_setup.items()):
                template_data += self.network.format(nic_id=nic_id)
                if nic_setup['mac'] == 'generated':
                    template_data += self.network_mac_generated.format(
                        nic_id=nic_id
                    )
                else:
                    template_data += self.network_mac_static.format(
                        nic_id=nic_id, mac_address=nic_setup['mac']
                    )
                if nic_setup['driver']:
                    template_data += self.network_driver.format(
                        nic_id=nic_id, network_driver=nic_setup['driver']
                    )
                if nic_setup['connection_type']:
                    template_data += self.network_connection_type.format(
                        nic_id=nic_id, mode=nic_setup['connection_type']
                    )

        if iso_setup:
            if iso_controller == 'ide':
                template_data += self.ide_iso
            else:
                template_data += self.scsi_iso

        template_data += self.usb

        return Template(template_data)
