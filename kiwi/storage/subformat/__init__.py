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
from kiwi.storage.subformat.qcow2 import DiskFormatQcow2
from kiwi.storage.subformat.vhd import DiskFormatVhd
from kiwi.storage.subformat.vhdx import DiskFormatVhdx
from kiwi.storage.subformat.vhdfixed import DiskFormatVhdFixed
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.storage.subformat.ova import DiskFormatOva
from kiwi.storage.subformat.gce import DiskFormatGce
from kiwi.storage.subformat.vdi import DiskFormatVdi
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt

from kiwi.exceptions import (
    KiwiDiskFormatSetupError
)


class DiskFormat(object):
    """
    **DiskFormat factory**

    :param string name: Format name
    :param object xml_state: Instance of XMLState
    :param string root_dir: root directory path name
    :param string target_dir: target directory path name
    """
    def __new__(self, name, xml_state, root_dir, target_dir):  # noqa: C901
        custom_args = xml_state.get_build_type_format_options()
        if name == 'qcow2':
            return DiskFormatQcow2(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vdi':
            return DiskFormatVdi(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vhd':
            return DiskFormatVhd(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vhdx':
            return DiskFormatVhdx(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vhd-fixed':
            disk_tag = xml_state.build_type.get_vhdfixedtag()
            if disk_tag:
                custom_args.update(
                    {'--tag': disk_tag}
                )
            return DiskFormatVhdFixed(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'gce':
            gce_license_tag = xml_state.build_type.get_gcelicense()
            if gce_license_tag:
                custom_args.update(
                    {'--tag': gce_license_tag}
                )
            return DiskFormatGce(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vmdk' or name == 'ova':
            vmdisk_section = xml_state.get_build_type_vmdisk_section()
            if vmdisk_section:
                disk_mode = vmdisk_section.get_diskmode()
                disk_controller = vmdisk_section.get_controller()
                if disk_mode:
                    custom_args.update(
                        {'subformat={0}'.format(disk_mode): None}
                    )
                if disk_controller:
                    custom_args.update(
                        {'adapter_type={0}'.format(disk_controller): None}
                    )
            if name == 'vmdk':
                return DiskFormatVmdk(
                    xml_state, root_dir, target_dir, custom_args
                )
            else:
                return DiskFormatOva(
                    xml_state, root_dir, target_dir, custom_args
                )
        elif name == 'vagrant':
            vagrant_config = xml_state.get_build_type_vagrant_config_section()
            if vagrant_config:
                custom_args.update(
                    {'vagrantconfig': vagrant_config}
                )
                provider = vagrant_config.get_provider()
            else:
                provider = 'undefined'
            if provider == 'libvirt':
                return DiskFormatVagrantLibVirt(
                    xml_state, root_dir, target_dir, custom_args
                )
            else:
                raise KiwiDiskFormatSetupError(
                    'No support for {0} format with {1} provider'.format(
                        name, provider
                    )
                )
        elif name == 'raw':
            return DiskFormatBase(
                xml_state, root_dir, target_dir, custom_args
            )
        else:
            raise KiwiDiskFormatSetupError(
                'No support for {0} disk format'.format(name)
            )
