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
import os
from collections import OrderedDict
from tempfile import mkdtemp

# project
from kiwi.command import Command
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.archive.tar import ArchiveTar


class DiskFormatGce(DiskFormatBase):
    """
    **Create GCE - Google Compute Engine image format**
    """
    def post_init(self, custom_args):
        """
        GCE disk format post initialization method

        Store disk tag from custom args

        :param dict custom_args:
            custom gce argument dictionary

            .. code:: python

                {'--tag': 'billing_code'}
        """
        self.image_format = 'gce'
        self.tag = None
        if custom_args:
            ordered_args = OrderedDict(list(custom_args.items()))
            for key, value in list(ordered_args.items()):
                if key == '--tag':
                    self.tag = value

    def create_image_format(self):
        """
        Create GCE disk format and manifest
        """
        gce_tar_ball_file_list = []
        self.temp_image_dir = mkdtemp(
            prefix='kiwi_gce_subformat.', dir=self.target_dir
        )
        diskname = ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + self.xml_state.get_image_version(),
                '.raw'
            ]
        )
        if self.tag:
            with open(self.temp_image_dir + '/manifest.json', 'w') as manifest:
                manifest.write('{"licenses": ["%s"]}' % self.tag)
            gce_tar_ball_file_list.append('manifest.json')

        Command.run(
            ['cp', diskname, self.temp_image_dir + '/disk.raw']
        )
        gce_tar_ball_file_list.append('disk.raw')

        archive_name = os.path.basename(
            self.get_target_file_path_for_format(self.image_format)
        )

        # delete the '.gz' suffix from the name. The suffix is appended by
        # the archive creation method depending on the creation type.
        archive_name = archive_name.replace('.gz', '')

        archive = ArchiveTar(
            filename=self.target_dir + '/' + archive_name,
            file_list=gce_tar_ball_file_list
        )
        archive.create_gnu_gzip_compressed(
            self.temp_image_dir
        )

    def store_to_result(self, result):
        """
        Store result file of the gce format conversion into the
        provided result instance. In this case compression is unwanted
        because the gce tarball is already created as a compressed
        archive

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

    def get_target_file_path_for_format(self, format_name):
        """
        Google requires the image name to follow their naming
        convetion. Therefore it's required to provide a suitable
        name by overriding the base class method

        :param string format_name: gce

        :return: file path name

        :rtype: str
        """
        if format_name == 'gce':
            format_name = 'tar.gz'
        return ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + self.xml_state.get_image_version(),
                '.' + format_name
            ]
        )
