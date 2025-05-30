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
from textwrap import dedent
from typing import (
    List, Dict
)

# project
from kiwi.storage.subformat.vagrant_base import DiskFormatVagrantBase, VagrantConfigDict
from kiwi.storage.subformat.vmdk import DiskFormatVmdk
from kiwi.command import Command


class DiskFormatVagrantVMware(DiskFormatVagrantBase):
    """
    **Create a vagrant box for the vmware provider**
    """

    def vagrant_post_init(self, custom_args: VagrantConfigDict) -> None:
        self.image_format = 'vagrant.vmware_desktop.box'
        self.provider = 'vmware_desktop'
        self.options = self.get_qemu_option_list(custom_args)

    def create_box_img(self, temp_image_dir: str) -> List[str]:
        """
        Creates the vmdk disk image for the vmware_desktop vagrant provider

        :param str temp_image_dir:
            Path to the temporary directory used to build the box image

        :return:
            A list of files relevant for the vmware box to be
            included in the vagrant box

        :rtype: list
        """
        vmdk = DiskFormatVmdk(
            self.xml_state, self.root_dir, self.target_dir,
            custom_args=self.options
        )
        vmdk.create_image_format()
        box_image = os.sep.join([temp_image_dir, 'box.img'])
        Command.run(
            [
                'mv', self.get_target_file_path_for_format(vmdk.image_format),
                box_image
            ]
        )
        return [box_image]

    def get_additional_metadata(self) -> Dict:
        """
        Provide box metadata needed to create the box in vagrant

        :return:
            Returns a dictionary containing the virtual image format
            and the size of the image.

        :rtype: dict
        """
        return {
            'format': 'vmdk'
        }

    def get_additional_vagrant_config_settings(self) -> str:
        """
        Returns settings for the libvirt provider telling vagrant to use kvm.

        :return:
            ruby code to be evaluated as string

        :rtype: str
        """
        # return dedent('''
        #     config.vm.synced_folder ".", "/vagrant", type: "rsync"
        #     config.vm.provider :libvirt do |libvirt|
        #       libvirt.driver = "kvm"
        #     end
        # ''').strip()
        return ''
