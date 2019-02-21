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
import json
import os
import random

from tempfile import mkdtemp

from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.storage.subformat.template.vagrant_config import VagrantConfigTemplate
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiFormatSetupError
)


class DiskFormatVagrantBase(DiskFormatBase):
    """
    Base class for creating vagrant boxes.

    The documentation of the vagrant box format can be found here:
    https://www.vagrantup.com/docs/boxes/format.html
    In a nutshell, a vagrant box is a tar, tar.gz or zip archive of the
    following:

    1. ``metadata.json``: A json file that contains the name of the provider
       and arbitrary additional data (that vagrant doesn't care about).
    2. ``Vagrantfile``: A Vagrantfile which defines the boxes' MAC address. It
       can be also used to define other settings of the box, e.g. the method
       via which the ``/vagrant/`` directory is shared.
    3. The actual virtual disk image: this is provider specific and vagrant
       simply forwards it to your virtual machine provider.

    Required methods/variables that child classes must implement:

    - ``provider: str``:
      A static variable or property, should contain the name of the provider.
      This value is used to create the ``metadata.json`` file and the attribute
      :attr:`image_format`.
      (Note: you also must add the image format to
      :func:`kiwi.defaults.Defaults.get_disk_format_types`)

    - :meth:`create_box_img`

    Optional methods:

    - :meth:`get_additional_metadata`

    - :meth:`get_additional_vagrant_config_settings`

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

        self.vagrantconfig = custom_args['vagrantconfig']
        self.vagrant_post_init()

    def vagrant_post_init(self):
        pass

    def create_box_img(self, temp_image_dir):
        """
        Provider specific image creation step: this function creates the actual
        box image. It must be implemented by a child class.

        :param str temp_image_dir: path to a temporary directory inside which the
            image should be built
        :return: A list of files that were create by this function and that
            should be included in the vagrant box
        :rtype: List(str)
        """
        raise NotImplementedError

    def create_image_format(self):
        """
        Create a vagrant box for any provider. This includes:

        * creation of box metadata.json
        * creation of box Vagrantfile
        * creation of result format tarball from the files created above
        """
        self.temp_image_dir = mkdtemp(prefix='kiwi_vagrant_box.')

        box_img_files = self.create_box_img(self.temp_image_dir)

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
                os.path.basename(metadata_json),
                os.path.basename(vagrantfile)
            ] + [
                os.path.basename(box_img_file)
                for box_img_file in box_img_files
            ]
        )

    def store_to_result(self, result):
        """
        Store result file of the vagrant format conversion into the
        provided result instance. In this case compression is unwanted
        because the box is already created as a compressed tarball

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=False,
            shasum=True
        )

    @classmethod
    def get_additional_metadata(cls):
        """
        Provide :meth:`create_image_format` with additional metadata that will
        be included in ``metadata.json``.

        The default implementation returns an empty dictionary.

        :return: A dictionary that is serializable to JSON
        :rtype: dict
        """
        return {}

    @classmethod
    def get_additional_vagrant_config_settings(cls):
        """
        Supply additional configuration settings for vagrant to be included in
        the resulting box.

        This function can be used by child classes to customize the behavior
        for different providers: the supplied configuration settings get
        forwarded to :func:`VagrantConfigTemplate.get_template` as the
        parameter ``custom_settings`` and included in the ``Vagrantfile``.

        The default implementation returns nothing.

        :return: additional vagrant settings
        :rtype: str
        """
        pass

    def _create_box_metadata(self):
        metadata = self.get_additional_metadata()
        metadata['provider'] = self.provider
        return json.dumps(
            metadata, sort_keys=True, indent=2, separators=(',', ': ')
        )

    def _create_box_vagrantconfig(self):
        template = VagrantConfigTemplate()
        vagrant_config = template.get_template(
            custom_settings=self.get_additional_vagrant_config_settings()
        )
        return vagrant_config.substitute(
            {'mac_address': self._random_mac()}
        )

    @staticmethod
    def _random_mac():
        return '%02x%02x%02x%02x%02x%02x'.upper() % (
            0x00, 0x16, 0x3e,
            random.randrange(0, 0x7e),
            random.randrange(0, 0xff),
            random.randrange(0, 0xff)
        )
