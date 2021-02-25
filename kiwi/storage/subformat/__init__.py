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
import importlib
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.xml_state import XMLState
from kiwi.exceptions import KiwiDiskFormatSetupError


class DiskFormat(metaclass=ABCMeta):
    """
    **DiskFormat factory**

    :param string name: Format name
    :param object xml_state: Instance of XMLState
    :param string root_dir: root directory path name
    :param string target_dir: target directory path name
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    @abstractmethod
    def new(
        name: str, xml_state: XMLState, root_dir: str, target_dir: str
    ):  # noqa: E252
        name_map = {
            'qcow2': 'Qcow2',
            'vdi': 'Vdi',
            'vhd': 'Vhd',
            'vhdx': 'Vhdx',
            'vhdfixed': 'VhdFixed',
            'gce': 'Gce',
            'vmdk': 'Vmdk',
            'ova': 'Ova',
            'vagrant_libvirt': 'VagrantLibVirt',
            'vagrant_virtualbox': 'VagrantVirtualBox',
            'base': 'Base'
        }
        try:
            (custom_args, module_namespace) = DiskFormat.\
                _custom_args_for_format(name, xml_state)
            diskformat = importlib.import_module(
                'kiwi.storage.subformat.{0}'.format(module_namespace)
            )
            module_name = 'DiskFormat{0}'.format(name_map[module_namespace])
            return diskformat.__dict__[module_name](
                xml_state, root_dir, target_dir, custom_args
            )
        except Exception as issue:
            raise KiwiDiskFormatSetupError(
                'No support for {0} disk format: {1}'.format(
                    module_namespace, issue
                )
            )

    @staticmethod
    def _custom_args_for_format(name: str, xml_state: XMLState):
        custom_args = xml_state.get_build_type_format_options()
        module_namespace = name
        if name == 'vhd-fixed':
            disk_tag = xml_state.build_type.get_vhdfixedtag()
            if disk_tag:
                custom_args.update(
                    {'--tag': disk_tag}
                )
            module_namespace = 'vhdfixed'
        elif name == 'gce':
            gce_license_tag = xml_state.build_type.get_gcelicense()
            if gce_license_tag:
                custom_args.update(
                    {'--tag': gce_license_tag}
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
        elif name == 'vagrant':
            vagrant_config = xml_state.get_build_type_vagrant_config_section()
            if vagrant_config:
                custom_args.update(
                    {'vagrantconfig': vagrant_config}
                )
                module_namespace = '{0}_{1}'.format(
                    name, vagrant_config.get_provider()
                )
        elif name == 'raw':
            module_namespace = 'base'
        return [custom_args, module_namespace]
