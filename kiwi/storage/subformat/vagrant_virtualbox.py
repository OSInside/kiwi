# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
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
import random
from textwrap import dedent
from typing import List

# project
from kiwi.storage.subformat.template.virtualbox_ovf import (
    VirtualboxOvfTemplate
)
from kiwi.storage.subformat.vagrant_base import DiskFormatVagrantBase
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.command import Command


class DiskFormatVagrantVirtualBox(DiskFormatVagrantBase):
    """
    **Create a vagrant box for the virtualbox provider**
    """

    def vagrant_post_init(self) -> None:
        self.provider = 'virtualbox'
        self.image_format = 'vagrant.virtualbox.box'

    def get_additional_vagrant_config_settings(self) -> str:
        """
        Configure the default shared folder to use rsync when guest additions
        are not present inside the box.

        :return:
            ruby code to be evaluated as string

        :rtype: str
        """
        extra_settings = dedent('''
            config.vm.base_mac = "{mac_address}"
        ''').strip().format(mac_address=self._random_mac())

        if not self.xml_state.get_vagrant_config_virtualbox_guest_additions():
            extra_settings += os.linesep + dedent('''
            config.vm.synced_folder ".", "/vagrant", type: "rsync"
            ''').strip()

        return extra_settings

    def create_box_img(self, temp_image_dir: str) -> List[str]:
        """
        Create the vmdk image for the Virtualbox vagrant provider.

        This function creates the vmdk disk image and the ovf file.
        The latter is created via the class :class:`VirtualboxOvfTemplate`.

        :param str temp_image_dir:
            Path to the temporary directory used to build the box image

        :return:
            A list of files relevant for the virtualbox box to be
            included in the vagrant box

        :rtype: list
        """
        vmdk = DiskFormatVmdk(self.xml_state, self.root_dir, self.target_dir)
        vmdk.create_image_format()
        box_img = os.sep.join([temp_image_dir, 'box.vmdk'])
        Command.run(
            [
                'mv', self.get_target_file_path_for_format(vmdk.image_format),
                box_img
            ]
        )
        box_ovf = os.sep.join([temp_image_dir, 'box.ovf'])
        ovf_template = VirtualboxOvfTemplate()
        disk_image_capacity = self.vagrantconfig.get_virtualsize() or 42
        xml_description_specification = self.xml_state \
            .get_description_section().specification
        with open(box_ovf, "w") as ovf_file:
            ovf_file.write(
                ovf_template.get_template().substitute(
                    {
                        'root_uuid': self.xml_state.get_root_filesystem_uuid(),
                        'vm_name': self.xml_state.xml_data.name,
                        'disk_image_capacity': disk_image_capacity,
                        'vm_description': xml_description_specification
                    }
                )
            )
        return [box_img, box_ovf]

    @staticmethod
    def _random_mac():
        return '%02x%02x%02x%02x%02x%02x'.upper() % (
            0x00, 0x16, 0x3e,
            random.randrange(0, 0x7e),
            random.randrange(0, 0xff),
            random.randrange(0, 0xff)
        )
