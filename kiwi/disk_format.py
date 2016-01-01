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
# project
from disk_format_qcow2 import DiskFormatQcow2
from disk_format_vhd import DiskFormatVhd
from disk_format_vhdfixed import DiskFormatVhdFixed
from disk_format_vmdk import DiskFormatVmdk

from exceptions import (
    KiwiDiskFormatSetupError
)


class DiskFormat(object):
    """
        DiskFormat factory
    """
    def __new__(self, name, xml_state, source_dir, target_dir):
        if name == 'qcow2':
            return DiskFormatQcow2(
                xml_state, source_dir, target_dir
            )
        elif name == 'vhd':
            return DiskFormatVhd(
                xml_state, source_dir, target_dir
            )
        elif name == 'vhdfixed':
            custom_args = None
            disk_tag = xml_state.build_type.get_vhdfixedtag()
            if disk_tag:
                custom_args = {
                    '--tag': disk_tag
                }
            return DiskFormatVhdFixed(
                xml_state, source_dir, target_dir, custom_args
            )
        elif name == 'vmdk':
            custom_args = None
            vmdisk_section = xml_state.get_build_type_vmdisk_section()
            if vmdisk_section:
                custom_args = {
                    'subformat=': vmdisk_section.get_diskmode(),
                    'adapter_type=': vmdisk_section.get_controller()
                }
            return DiskFormatVmdk(
                xml_state, source_dir, target_dir, custom_args
            )
        else:
            raise KiwiDiskFormatSetupError(
                'Support for %s disk format not implemented' % name
            )
