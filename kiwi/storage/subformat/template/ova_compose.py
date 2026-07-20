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
                type: vmx-${virtual_hardware_version}
                os_vmw: "${guest_os}"
                firmware: "${firmware}"
                secure_boot: ${secure_boot}
        ''').strip() + self.cr

        self.network = dedent('''
            networks:
                vm_network:
                    name: "VM Network"
                    description: "The VM Network"
        ''').strip() + self.cr

    def _get_controller(self, controller: str | None, device_id: str) -> tuple[str, str, str]:
        controller_map = {
            'ide': ('ide', 'ide_controller'),
            'sata': ('sata', 'sata_controller'),
            'scsi': ('scsi', 'scsi_controller'),
            'lsilogic': ('scsi', 'scsi_controller'),
            'lsisas1068': ('scsi', 'scsi_controller'),
            'paravirtual': ('scsi', 'scsi_controller'),
            'nvme': ('nvme', 'nvme_controller')
        }
        normalized_controller = (controller or 'nvme').lower()
        controller_name, controller_type = controller_map.get(
            normalized_controller, ('nvme', 'nvme_controller')
        )
        return f'{controller_name}{device_id}', controller_type, normalized_controller

    def _add_controller(
            self, hardware_lines: list, controllers_added: set,
            controller_name: str, controller_type: str,
            controller_subtype: str | None = None) -> None:
        if controller_name in controllers_added:
            return
        hardware_lines.append(f'    {controller_name}:')
        hardware_lines.append(f'        type: {controller_type}')
        if controller_subtype:
            hardware_lines.append(f'        subtype: {controller_subtype}')
        controllers_added.add(controller_name)

    def _get_network_setup(self, network_setup: dict = None) -> tuple[list, list]:
        hardware_lines = []
        network_lines = [
            'networks:'
        ]

        if network_setup:
            for nic_id, nic_setup in list(network_setup.items()):
                network_name = f'vm_network_{nic_id}'
                nic_name = f'ethernet{nic_id}'
                nic_driver = nic_setup.get('driver') or 'VmxNet3'

                hardware_lines.extend([
                    f'    {nic_name}:',
                    '        type: ethernet',
                    f'        subtype: {nic_driver}',
                    f'        network: {network_name}'
                ])

                if nic_setup.get('mac') and nic_setup['mac'] != 'generated':
                    hardware_lines.append(
                        f'        mac_address: "{nic_setup["mac"]}"'
                    )

                if nic_setup.get('connection_type'):
                    hardware_lines.append(
                        f'        connection_type: "{nic_setup["connection_type"]}"'
                    )

                network_lines.extend([
                    f'    {network_name}:',
                    f'        name: "VM Network {nic_id}"',
                    f'        description: "The VM Network {nic_id} network"'
                ])
        else:
            hardware_lines.extend([
                '    ethernet0:',
                '        type: ethernet',
                '        subtype: VmxNet3',
                '        network: vm_network_0'
            ])
            network_lines.extend([
                '    vm_network_0:',
                '        name: "VM Network"',
                '        description: "The VM Network network"'
            ])

        return hardware_lines, network_lines

    def _get_hardware_template(
            self, memory_setup: bool = False, cpu_setup: bool = False,
            network_setup: dict = None, iso_setup: bool = False,
            disk_controller: str = None, iso_controller: str = 'ide',
            disk_id: str = '0', iso_id: str = '0') -> str:
        """
        Generate hardware template with VMware feature parity.

        :rtype: str
        """
        hardware_lines = [
            'hardware:'
        ]
        if cpu_setup:
            hardware_lines.append('    cpus: ${number_of_cpus}')
        if memory_setup:
            hardware_lines.append('    memory: ${memory_size}')

        controllers_added: set[str] = set()

        disk_parent, disk_controller_type, disk_controller_subtype = self._get_controller(
            disk_controller, str(disk_id)
        )
        self._add_controller(
            hardware_lines, controllers_added,
            disk_parent, disk_controller_type, disk_controller_subtype
        )

        if iso_setup:
            iso_parent, iso_controller_type, iso_controller_subtype = self._get_controller(
                iso_controller, str(iso_id)
            )
            self._add_controller(
                hardware_lines, controllers_added,
                iso_parent, iso_controller_type, iso_controller_subtype
            )
            hardware_lines.extend([
                f'    cdrom{iso_id}:',
                '        type: cd_drive',
                f'        parent: {iso_parent}'
            ])

        hardware_lines.extend([
            '    rootdisk:',
            '        type: hard_disk',
            f'        parent: {disk_parent}',
            '        disk_image: "${vmdk_file}"',
            '    usb2:',
            '        type: usb_controller',
            '    usb3:',
            '        type: usb3_controller'
        ])

        nic_hardware, network_lines = self._get_network_setup(network_setup)
        hardware_lines.extend(nic_hardware)

        return '\n'.join(hardware_lines) + self.cr + '\n'.join(network_lines) + self.cr

    def get_template(
            self, memory_setup=False, cpu_setup=False, network_setup=False,
            iso_setup=False, disk_controller='ide', iso_controller='ide',
            disk_id='0', iso_id='0') -> Template:
        """
        Set data for the ova-compose template

        :param bool memory_setup: with main memory setup true|false
        :param bool cpu_setup: with number of CPU's setup true|false
        :param dict network_setup: with network emulation setup
        :param bool iso_setup: with CD/DVD drive emulation true|false
        :param string disk_controller: add disk controller setup to template
        :param string iso_controller: add CD/DVD controller setup to template
        :param string disk_id: disk controller id
        :param string iso_id: cdrom controller id

        :rtype: Template
        """
        template_data = self.header
        hardware = self._get_hardware_template(
            memory_setup=memory_setup,
            cpu_setup=cpu_setup,
            network_setup=network_setup,
            iso_setup=iso_setup,
            disk_controller=disk_controller,
            iso_controller=iso_controller,
            disk_id=disk_id,
            iso_id=iso_id
        )
        template_data += hardware

        return Template(template_data)
