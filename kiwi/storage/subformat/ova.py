# Copyright (c) 2018 Eaton.  All rights reserved.
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
import pathlib
from textwrap import dedent

# project
from kiwi.firmware import FirmWare
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command
from kiwi.path import Path
from kiwi.system.result import Result
from kiwi.storage.subformat.template.ova_compose import (
    OvaComposeTemplate
)

from kiwi.exceptions import (
    KiwiFormatSetupError,
    KiwiCommandNotFound,
    KiwiTemplateError
)


class DiskFormatOva(DiskFormatBase):
    """
    **Create ova disk format, based on vmdk**
    """
    def post_init(self, custom_args: dict) -> None:
        """
        vmdk disk format post initialization method

        Store qemu options as list from custom args dict

        :param dict custom_args: custom qemu arguments dictionary
        """
        ovftype = 'vmware'  # default OVA target infrastructure
        self.machine_setup = self.xml_state.get_build_type_machine_section()
        if self.machine_setup and self.machine_setup.get_ovftype():
            ovftype = self.machine_setup.get_ovftype()
        if ovftype != 'vmware':
            raise KiwiFormatSetupError(f'Unsupported ovftype {ovftype}')
        self.image_format = 'ova'
        # ensure streamOptimized format is enabled
        custom_args.update(
            {'subformat=streamOptimized': None}
        )
        self.firmware = FirmWare(
            self.xml_state
        )
        self.vmdk = DiskFormatVmdk(
            self.xml_state, self.root_dir, self.target_dir, custom_args
        )

    def create_image_format(self) -> None:
        """
        Create ova disk format using ovftool from
        https://www.vmware.com/support/developer/ovf
        """
        # Check for required mkova tool
        ova_compose = Path.which(filename='ova-compose', access_mode=os.X_OK)
        if not ova_compose:
            tool_not_found_message = dedent('''\n
                Required ova-compose not found in PATH on the build host

                Building OVA images requires the ova-compose tool which
                is usually provided by the open-vmdk package.
            ''')
            raise KiwiCommandNotFound(
                tool_not_found_message
            )

        # Create the vmdk disk image and vmx config
        self.vmdk.create_image_format()

        compose_meta = self.get_target_file_path_for_format('meta')
        ova = self.get_target_file_path_for_format('ova')

        # Create ova composer meta file
        self._create_ova_compose_meta_file()

        pathlib.Path(ova).unlink(missing_ok=True)
        os.chdir(self.target_dir)
        Command.run(
            [
                ova_compose,
                '--input-file', compose_meta,
                '--output-file', ova,
                '--format', 'ova'
            ]
        )

    def store_to_result(self, result: Result) -> None:
        """
        Store the resulting ova file into the provided result instance.

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format('ova'),
            use_for_bundle=True,
            compress=self.runtime_config.get_bundle_compression(
                default=False
            ),
            shasum=True
        )

    def _create_ova_compose_meta_file(self) -> None:
        """
        Create the ova-compose meta file used to create the final ova file
        """
        displayname = self.xml_state.xml_data.get_displayname()
        efi_mode = self.firmware.efi_mode()
        template_record = {
            'display_name':
                displayname or self.xml_state.xml_data.get_name(),
            'vmdk_file':
                os.path.basename(self.get_target_file_path_for_format('vmdk')),
            'guest_os': 'other4xLinux64Guest',
            'memory_size': 4096,
            'number_of_cpus': 2,
            'firmware': 'efi' if efi_mode else 'bios',
            'secure_boot': 'true' if efi_mode == 'uefi' else 'false'
        }

        # Basic setup
        machine_setup = self.xml_state.get_build_type_machine_section()
        if machine_setup:
            memory_setup = machine_setup.get_memory()
            guest_os = machine_setup.get_guestOS()
            cpu_setup = machine_setup.get_ncpus()
            if guest_os:
                template_record['guest_os'] = guest_os
            if memory_setup:
                template_record['memory_size'] = memory_setup
            if cpu_setup:
                template_record['number_of_cpus'] = cpu_setup

        # Build settings template and write settings file
        settings_template = OvaComposeTemplate().get_template(
            bool(machine_setup)
        )
        try:
            settings_file = self.get_target_file_path_for_format('meta')
            with open(settings_file, 'w') as config:
                config.write(settings_template.substitute(template_record))
        except Exception as issue:
            raise KiwiTemplateError(
                f'{type(issue).__name__}: {format(issue)}'
            )
