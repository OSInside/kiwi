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
import re

# project
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.command import Command
from kiwi.exceptions import (
    KiwiFormatSetupError
)


class DiskFormatOva(DiskFormatVmdk):
    """
    Create ova disk format, based on vmdk
    """
    def post_init(self, custom_args):
        """
        vmdk disk format post initialization method

        Store qemu options as list from custom args dict

        Attributes

        * :attr:`options`
            qemu format conversion options

        * :attr:`image_format`
            disk format name: ova
        """
        ovftype = self.xml_state.get_build_type_machine_section().get_ovftype()
        if ovftype is not None and ovftype != 'vmware':
            raise KiwiFormatSetupError('Unsupported ovftype %s' % ovftype)
        self.image_format = 'ova'
        self.options = self.get_qemu_option_list(custom_args)

    def create_image_format(self):
        # Creates the vmdk disk image and vmx config
        super(DiskFormatOva, self).create_image_format()
        # Converts to ova using ovftool
        vmx = self.get_target_name_for_format('vmx')
        ova = self.get_target_name_for_format('ova')
        try:
            os.unlink(ova)
        except OSError:
            pass
        ovftool_cmd = ['ovftool']
        ovftool_help = Command.run(['ovftool', '--help'])
        if re.search(r'--shaAlgorithm\b', ovftool_help.output):
            ovftool_cmd.append('--shaAlgorithm=SHA1')
        ovftool_cmd.extend([vmx, ova])
        Command.run(ovftool_cmd)
        # ovftool ignores the umask and creates files with 0600 for some reason
        st = os.stat(vmx)
        os.chmod(ova, stat.S_IMODE(st.st_mode))

    def store_to_result(self, result):
        """
        Store the resulting ova file into the provided result instance.

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_name_for_format('ova'),
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
