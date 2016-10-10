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
import re

# In python2 bytes is string which is different from
# the bytes type in python3. The bytes type from the
# builtins generalizes this type to be bytes always
from builtins import bytes

# project
from .base import DiskFormatBase
from ...command import Command
from ...logger import log
from .template.vmware_settings import VmwareSettingsTemplate

from ...exceptions import (
    KiwiVmdkToolsError,
    KiwiTemplateError
)


class DiskFormatVmdk(DiskFormatBase):
    """
    Create vmdk disk format
    """
    def post_init(self, custom_args):
        """
        vmdk disk format post initialization method

        Store qemu options as list from custom args dict

        Attributes

        * :attr:`options`
            qemu format conversion options

        * :attr:`image_format`
            disk format name: vmdk
        """
        self.image_format = 'vmdk'
        self.options = self.get_qemu_option_list(custom_args)

    def create_image_format(self):
        """
        Create vmdk disk format and machine settings file
        """
        Command.run(
            [
                'qemu-img', 'convert', '-f', 'raw', self.diskname,
                '-O', self.image_format
            ] + self.options + [
                self.get_target_name_for_format(self.image_format)
            ]
        )
        self._update_vmdk_descriptor()
        self._create_vmware_settings_file()

    def store_to_result(self, result):
        """
        Store result files of the vmdk format conversion into the
        provided result instance. This includes the vmdk image file
        and the VMware settings file

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_name_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        result.add(
            key='disk_format_machine_settings',
            filename=self.get_target_name_for_format(
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
        template_record = {
            'display_name':
                self.xml_state.xml_data.get_displayname() or
                self.xml_state.xml_data.get_name(),
            'vmdk_file':
                self.get_target_name_for_format(self.image_format),
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
        network_setup = self.xml_state.get_build_type_vmnic_section()
        network_driver = None
        network_connection_type = None
        network_mac = 'generated'
        if network_setup:
            network_driver = network_setup.get_driver()
            network_connection_type = network_setup.get_mode()
            network_mac = network_setup.get_mac() or network_mac
            template_record['nic_id'] = network_setup.get_interface() or '0'
            template_record['mac_address'] = \
                network_mac
            template_record['network_connection_type'] = \
                network_connection_type
            template_record['network_driver'] = \
                network_driver

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
            iso_controller,
            network_mac,
            network_driver,
            network_connection_type
        )
        try:
            settings_file = self.get_target_name_for_format('vmx')
            with open(settings_file, 'w') as config:
                config.write(settings_template.substitute(template_record))
                for custom_entry in custom_entries:
                    config.write(custom_entry + os.linesep)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def _update_vmdk_descriptor(self):
        """
        Update the VMDK descriptor with the VMware tools version
        and type information. This is done to let VMware's virtualization
        infrastructure know about the installed VMware tools at boot
        time of the image within a VMware virtual environment
        e.g VCloud Air. It's required to have vmtoolsd installed as
        part of the image. If not found a warning is provided to the
        user and the VMDK descriptor stays untouched
        """
        vmdk_vmtoolsd = self.root_dir + '/usr/bin/vmtoolsd'
        if not os.path.exists(vmdk_vmtoolsd):
            log.warning(
                'Could not find vmtoolsd in image root %s', self.root_dir
            )
            log.warning(
                'Update of VMDK metadata skipped'
            )
            return
        log.info('Updating VMDK metadata')
        vmdk_tools_install_type = 4
        vmdk_tools_version = self._get_vmdk_tools_version()
        vmdk_image_name = self.get_target_name_for_format('vmdk')
        log.info(
            '--> Setting tools version: %d', vmdk_tools_version
        )
        log.info(
            '--> Setting tools install type: %d', vmdk_tools_install_type
        )
        vmdk_descriptor_call = Command.run(
            ['dd', 'if=' + vmdk_image_name, 'bs=1', 'count=1024', 'skip=512']
        )
        vmdk_descriptor_lines = \
            vmdk_descriptor_call.output.strip('\0').split('\n')
        if (vmdk_descriptor_lines[0] != 'encoding="UTF-8"'):
            vmdk_descriptor_lines.insert(0, 'encoding="UTF-8"')
        vmdk_descriptor_lines.append(
            'ddb.toolsInstallType = "%s"' % vmdk_tools_install_type
        )
        vmdk_descriptor_lines.append(
            'ddb.toolsVersion = "%s"' % vmdk_tools_version
        )
        with open(vmdk_image_name, 'ab') as vmdk:
            vmdk.seek(512, 0)
            vmdk.write(bytes('\n'.join(vmdk_descriptor_lines), 'utf-8'))
            vmdk.seek(0, 2)

    def _get_vmdk_tools_version(self):
        vmdk_tools_version_call = Command.run(
            ['chroot', self.root_dir, 'vmtoolsd', '--version']
        )
        vmdk_tools_version = vmdk_tools_version_call.output
        vmdk_tools_version_format = re.match(
            ''.join(
                [
                    '^VMware Tools daemon, version ',
                    '(.*)',
                    '\.',
                    '(.*)',
                    '\.',
                    '(.*)',
                    '\.',
                    '(.*?)',
                    ' \(.*\)',
                    '$'
                ]
            ), vmdk_tools_version
        )
        if vmdk_tools_version_format:
            return \
                (int(vmdk_tools_version_format.group(1)) * 1024) + \
                (int(vmdk_tools_version_format.group(2)) * 32) + \
                int(vmdk_tools_version_format.group(3))
        else:
            raise KiwiVmdkToolsError(
                'vmtools version %s does not match format' % vmdk_tools_version
            )
