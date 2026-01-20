# Copyright (c) 2026 SUSE LLC.  All rights reserved.
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


class OvaComposeTemplate:
    """
    OVA compose settings template
    """
    def __init__(self):
        self.cr = '\n'

        self.header = dedent('''
            system:
                name: "${display_name}"
                type: vmx-20
                os_vmw: "${guest_os}"
                firmware: "${firmware}"
                secure_boot: ${secure_boot}
        ''').strip() + self.cr

        self.hardware = dedent('''
            hardware:
                cpus: ${number_of_cpus}
                memory: ${memory_size}
                sata1:
                    type: sata_controller
                scsi1:
                    type: scsi_controller
                nvme1:
                    type: nvme_controller
                cdrom1:
                    type: cd_drive
                    parent: sata1
                rootdisk:
                    type: hard_disk
                    parent: nvme1
                    disk_image: "${vmdk_file}"
                usb2:
                    type: usb_controller
                usb3:
                    type: usb3_controller
                ethernet1:
                    type: ethernet
                    subtype: VmxNet3
                    network: vm_network
                videocard1:
                    type: video_card
                vmci1:
                    type: vmci
        ''').strip() + self.cr

        self.network = dedent('''
            networks:
                vm_network:
                    name: "VM Network"
                    description: "The VM Network network"
        ''').strip() + self.cr

    def get_template(self, hardware_setup: bool = False):
        """
        Set data for the ova-compose template

        :param hardware_setup: if True, include hardware section

        :rtype: Template
        """
        template_data = self.header
        template_data += self.network
        if hardware_setup:
            template_data += self.hardware

        return Template(template_data)
