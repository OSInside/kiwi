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
import stat
from textwrap import dedent

# project
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.path import Path
from kiwi.system.result import Result

from kiwi.exceptions import (
    KiwiFormatSetupError,
    KiwiCommandNotFound
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
        ovftype = self.xml_state.get_build_type_machine_section().get_ovftype()
        if ovftype != 'vmware':
            raise KiwiFormatSetupError('Unsupported ovftype %s' % ovftype)
        self.image_format = 'ova'
        self.options = self.get_qemu_option_list(custom_args)
        self.vmdk = DiskFormatVmdk(
            self.xml_state, self.root_dir, self.target_dir, custom_args
        )

    def create_image_format(self) -> None:
        """
        Create ova disk format using ovftool from
        https://www.vmware.com/support/developer/ovf
        """
        # Check for required ovftool
        ovftool = Path.which(filename='ovftool', access_mode=os.X_OK)
        if not ovftool:
            tool_not_found_message = dedent('''\n
                Required ovftool not found in PATH on the build host

                Building OVA images requires VMware's ovftool tool which
                can be installed from the following location

                https://developer.vmware.com/web/tool/ovf
            ''')
            raise KiwiCommandNotFound(
                tool_not_found_message
            )

        # Create the vmdk disk image and vmx config
        self.vmdk.create_image_format()

        # Convert to ova using ovftool
        vmx = self.get_target_file_path_for_format('vmx')
        ova = self.get_target_file_path_for_format('ova')
        try:
            os.unlink(ova)
        except OSError:
            pass
        ovftool_options = []
        if CommandCapabilities.has_option_in_help(
            ovftool, '--shaAlgorithm', raise_on_error=False
        ):
            ovftool_options.append('--shaAlgorithm=SHA1')
        if CommandCapabilities.has_option_in_help(
            ovftool, '--allowExtraConfig', raise_on_error=False
        ):
            ovftool_options.append('--allowExtraConfig')
        if CommandCapabilities.has_option_in_help(
            ovftool, '--exportFlags', raise_on_error=False
        ):
            ovftool_options.append('--exportFlags=extraconfig')

        Command.run(
            [ovftool] + ovftool_options + [vmx, ova]
        )
        # ovftool ignores the umask and creates files with 0600
        # apply file permission bits set in the vmx file to the
        # ova file
        st = os.stat(vmx)
        os.chmod(ova, stat.S_IMODE(st.st_mode))

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
