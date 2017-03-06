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
from kiwi.storage.subformat.vhdfixed import DiskFormatVhdFixed
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.storage.subformat.gce import DiskFormatGce
from kiwi.storage.subformat.vdi import DiskFormatVdi
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt

from kiwi.exceptions import (
    KiwiDiskFormatSetupError
)


class DiskFormat(object):
    """
    DiskFormat factory

    Attributes

    * :attr:`name`
        Format name

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`root_dir`
        root directory path name

    * :attr:`target_dir`
        target directory path name
    """
    def __new__(self, name, xml_state, root_dir, target_dir):
        if name == 'qcow2':
            return DiskFormatQcow2(
                xml_state, root_dir, target_dir
            )
        elif name == 'vdi':
            return DiskFormatVdi(
                xml_state, root_dir, target_dir
            )
        elif name == 'vhd':
            return DiskFormatVhd(
                xml_state, root_dir, target_dir
            )
        elif name == 'vhd-fixed':
            custom_args = None
            disk_tag = xml_state.build_type.get_vhdfixedtag()
            if disk_tag:
                custom_args = {
                    '--tag': disk_tag
                }
            return DiskFormatVhdFixed(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'gce':
            custom_args = None
            gce_license_tag = xml_state.build_type.get_gcelicense()
            if gce_license_tag:
                custom_args = {
                    '--tag': gce_license_tag
                }
            return DiskFormatGce(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vmdk':
            custom_args = None
            vmdisk_section = xml_state.get_build_type_vmdisk_section()
            if vmdisk_section:
                custom_args = {}
                disk_mode = vmdisk_section.get_diskmode()
                disk_controller = vmdisk_section.get_controller()
                if disk_mode:
                    custom_args['subformat=%s' % disk_mode] = None
                if disk_controller:
                    custom_args['adapter_type=%s' % disk_controller] = None
            return DiskFormatVmdk(
                xml_state, root_dir, target_dir, custom_args
            )
        elif name == 'vagrant':
            vagrant_config = xml_state.get_build_type_vagrant_config_section()
            if vagrant_config:
                provider = vagrant_config.get_provider()
            else:
                provider = 'undefined'
            if provider == 'libvirt':
                return DiskFormatVagrantLibVirt(
                    xml_state, root_dir, target_dir,
                    {'vagrantconfig': vagrant_config}
                )
            else:
                raise KiwiDiskFormatSetupError(
                    'No support for {0} format with {1} provider'.format(
                        name, provider
                    )
                )
        elif name == 'raw':
            return DiskFormatBase(
                xml_state, root_dir, target_dir
            )
        else:
            raise KiwiDiskFormatSetupError(
                'No support for {0} disk format'.format(name)
            )
