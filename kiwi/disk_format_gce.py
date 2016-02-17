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
from collections import OrderedDict
from tempfile import mkdtemp

# project
from .command import Command
from .disk_format_base import DiskFormatBase
from .archive_tar import ArchiveTar


class DiskFormatGce(DiskFormatBase):
    """
        create GCE - Google Compute Engine image format
    """
    def post_init(self, custom_args):
        self.tag = None
        if custom_args:
            ordered_args = OrderedDict(list(custom_args.items()))
            for key, value in list(ordered_args.items()):
                if key == '--tag':
                    self.tag = value

    def create_image_format(self):
        self.temp_image_dir = mkdtemp(
            dir=self.target_dir
        )
        diskname = ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(), '.raw'
            ]
        )
        Command.run(
            ['cp', diskname, self.temp_image_dir + '/disk.raw']
        )
        if self.tag:
            with open(self.temp_image_dir + '/manifest.json', 'w') as manifest:
                manifest.write('{"licenses":["%s"]}' % self.tag)

        archive_name = self.get_target_name_for_format('gce')

        # delete the '.gz' suffix from the name. The suffix is appended by
        # the archive creation method depending on the creation type.
        archive_name = archive_name.replace('.gz', '')

        archive = ArchiveTar(
            self.target_dir + '/' + archive_name
        )
        archive.create_gnu_gzip_compressed(
            self.temp_image_dir
        )

    def get_target_name_for_format(self, format_name):
        """
            Google requires the image name to follow their naming
            convetion. Therefore it's required to provide a suitable
            name by overriding the base class method
        """
        if format_name == 'gce':
            format_name = 'tar.gz'
        return ''.join(
            [
                self.xml_state.get_distribution_name_from_boot_attribute(),
                '-guest-gce-',
                self.xml_state.get_image_version(),
                '.' + format_name
            ]
        )
