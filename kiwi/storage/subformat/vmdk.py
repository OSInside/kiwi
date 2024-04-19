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
from typing import Dict
import os

# project
from kiwi.system.result import Result
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command
from kiwi.storage.subformat.template.vmware_settings import (
    VmwareSettingsTemplate
)

from kiwi.exceptions import (
    KiwiTemplateError
)


class DiskFormatVmdk(DiskFormatBase):
    """
    Create vmdk disk format
    """
    def post_init(self, custom_args: Dict) -> None:
        """
        vmdk disk format post initialization method

        Store qemu options as list from custom args dict

        :param dict custom_args: custom qemu arguments dictionary
        """
        self.image_format = 'vmdk'
        self.options = self.get_qemu_option_list(custom_args)

    def create_image_format(self) -> None:
        """
        Create vmdk disk format and machine settings file
        """
        Command.run(
            [
                'qemu-img', 'convert', '-f', 'raw', self.diskname,
                '-O', 'vmdk'
            ] + self.options + [
                self.get_target_file_path_for_format('vmdk')
            ]
        )
        self._create_vmware_settings_file()

    def store_to_result(self, result: Result) -> None:
        """
        Store result files of the vmdk format conversion into the
        provided result instance. This includes the vmdk image file
        and the VMware settings file

        :param object result: Instance of Result
        """
        compression = self.runtime_config.get_bundle_compression(default=False)
        if self.xml_state.get_luks_credentials() is not None:
            compression = False
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format('vmdk'),
            use_for_bundle=True,
            compress=compression,
            shasum=True
        )
        result.add(
            key='disk_format_machine_settings',
            filename=self.get_target_file_path_for_format(
                'vmx'
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )

    def _create_vmware_settings_file(self):
        """
        In order to run a vmdk image in VMware products a settings file is
        needed or the possibility to convert machine settings into an ovf
        via VMware's proprietary ovftool
        """
        displayname = self.xml_state.xml_data.get_displayname()
        template_record = {
            'display_name':
                displayname or self.xml_state.xml_data.get_name(),
            'vmdk_file':
                os.path.basename(self.get_target_file_path_for_format('vmdk')),
            'virtual_hardware_version': '9',
            'guest_os': 'suse-64',
            'disk_id': '0'
        }

        # Basic setup
        machine_setup = self.xml_state.get_build_type_machine_section()
        memory_setup = None
        cpu_setup = None
        if machine_setup:
            memory_setup = machine_setup.get_memory()
            hardware_version = machine_setup.get_HWversion()
            guest_os = machine_setup.get_guestOS()
            cpu_setup = machine_setup.get_ncpus()
            if hardware_version:
                template_record['virtual_hardware_version'] = hardware_version
            if guest_os:
                template_record['guest_os'] = guest_os
            if memory_setup:
                template_record['memory_size'] = memory_setup
            if cpu_setup:
                template_record['number_of_cpus'] = cpu_setup

        # CD/DVD setup
        iso_setup = self.xml_state.get_build_type_vmdvd_section()
        iso_controller = 'ide'
        if iso_setup:
            iso_controller = iso_setup.get_controller() or iso_controller
            template_record['iso_id'] = iso_setup.get_id()

        # Network setup
        network_entries = self.xml_state.get_build_type_vmnic_entries()
        network_setup = {}
        for network_entry in network_entries:
            network_setup[network_entry.get_interface() or '0'] = {
                'driver': network_entry.get_driver(),
                'connection_type': network_entry.get_mode(),
                'mac': network_entry.get_mac() or 'generated',
            }

        # Disk setup
        disk_setup = self.xml_state.get_build_type_vmdisk_section()
        disk_controller = 'ide'
        if disk_setup:
            disk_controller = disk_setup.get_controller() or disk_controller
            disk_id = disk_setup.get_id()
            if not disk_controller == 'ide':
                template_record['scsi_controller_name'] = disk_controller
            if disk_id:
                template_record['disk_id'] = disk_id

        # Addition custom entries
        custom_entries = self.xml_state.get_build_type_vmconfig_entries()

        # Build settings template and write settings file
        settings_template = VmwareSettingsTemplate().get_template(
            memory_setup,
            cpu_setup,
            network_setup,
            iso_setup,
            disk_controller,
            iso_controller
        )
        try:
            settings_file = self.get_target_file_path_for_format('vmx')
            with open(settings_file, 'w') as config:
                config.write(settings_template.substitute(template_record))
                for custom_entry in custom_entries:
                    config.write(custom_entry + os.linesep)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
