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
import json
import os
import random
from textwrap import dedent
from tempfile import mkdtemp

# project
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.storage.subformat.qcow2 import DiskFormatQcow2
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiFormatSetupError
)


class DiskFormatVagrantLibVirt(DiskFormatBase):
    """
    **Create vagrant box for libvirt provider**
    """
    def post_init(self, custom_args):
        """
        vagrant disk format post initialization method

        store vagrantconfig information provided via custom_args

        :param dict custom_args:
            Contains instance of xml_parse::vagrantconfig

            .. code:: python

                {'vagrantconfig': object}
        """
        if not custom_args or 'vagrantconfig' not in custom_args:
            raise KiwiFormatSetupError(
                'object init requires custom_args hash with a vagrantconfig'
            )

        if not custom_args['vagrantconfig']:
            raise KiwiFormatSetupError(
                'no vagrantconfig provided'
            )

        self.image_format = 'vagrant.libvirt.box'
        self.vagrantconfig = custom_args['vagrantconfig']

    def create_image_format(self):
        """
        Create vagrant box for libvirt provider. This includes

        * creation of qcow2 disk image format as box.img
        * creation of box metadata.json
        * creation of box Vagrantfile
        * creation of result format tarball from the files created above
        """
        self.temp_image_dir = mkdtemp(prefix='kiwi_vagrant_box.')

        qcow = DiskFormatQcow2(
            self.xml_state, self.root_dir, self.target_dir
        )
        qcow.create_image_format()
        box_img = os.sep.join([self.temp_image_dir, 'box.img'])
        Command.run(
            [
                'mv', self.get_target_file_path_for_format(qcow.image_format),
                box_img
            ]
        )

        metadata_json = os.sep.join([self.temp_image_dir, 'metadata.json'])
        with open(metadata_json, 'w') as meta:
            meta.write(self._create_box_metadata())

        vagrantfile = os.sep.join([self.temp_image_dir, 'Vagrantfile'])
        with open(vagrantfile, 'w') as vagrant:
            vagrant.write(self._create_box_vagrantconfig())

        Command.run(
            [
                'tar', '-C', self.temp_image_dir,
                '-czf', self.get_target_file_path_for_format(self.image_format),
                os.path.basename(box_img),
                os.path.basename(metadata_json),
                os.path.basename(vagrantfile)
            ]
        )

    def _create_box_metadata(self):
        metadata = {
            'provider': 'libvirt',
            'format': 'qcow2',
            'virtual_size': format(self.vagrantconfig.get_virtualsize() or 42)
        }
        return json.dumps(
            metadata, sort_keys=True, indent=2, separators=(',', ': ')
        )

    def _create_box_vagrantconfig(self):
        vagrantconfig = dedent('''
            Vagrant::Config.run do |config|
              config.vm.base_mac = "{mac_address}"
            end
            include_vagrantfile = File.expand_path(
              "../include/_Vagrantfile", __FILE__
            )
            load include_vagrantfile if File.exist?(include_vagrantfile)
        ''').strip()
        return vagrantconfig.format(
            mac_address=self._random_mac()
        )

    def _random_mac(self):
        return '%02x%02x%02x%02x%02x%02x'.upper() % (
            0x00, 0x16, 0x3e,
            random.randrange(0, 0x7e),
            random.randrange(0, 0xff),
            random.randrange(0, 0xff)
        )
