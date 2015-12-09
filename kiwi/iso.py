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
import re
import collections
import platform
from tempfile import NamedTemporaryFile
from collections import namedtuple

# project
from command import Command
from exceptions import (
    KiwiIsoLoaderError
)


class Iso(object):
    """
        Implements helper methods around the creation of an iso filesystem
    """
    def __init__(self, source_dir):
        self.header_id = '7984fc91-a43f-4e45-bf27-6d3aa08b24cf'
        self.header_end_name = 'header_end'
        self.arch = platform.machine()
        self.source_dir = source_dir
        self.boot_path = 'boot/' + self.arch
        self.iso_sortfile = NamedTemporaryFile()
        self.iso_parameters = []
        self.iso_loaders = []

    def init_iso_creation_parameters(self, custom_args=None):
        """
            create a set of standard parameters for the main isolinux loader
            In addition a sort file with the contents of the iso is created.
            The kiwi iso file is also prepared to become a hybrid iso image.
            In order to do this the offest address of the end of the first iso
            block is required. In order to lookup the address a reference file
            named 'header_end' is created and will show up as last file in
            the block.
        """
        loader_file = self.boot_path + '/loader/isolinux.bin'
        catalog_file = self.boot_path + '/boot.catalog'
        with open(self.source_dir + '/' + self.header_end_name, 'w') as marker:
            marker.write('%s\n' % self.header_id)
        if not os.path.exists(self.source_dir + '/' + loader_file):
            raise KiwiIsoLoaderError(
                'No isolinux loader found in %s' %
                self.source_dir + '/loader'
            )
        if custom_args:
            self.iso_parameters = custom_args
        self.iso_parameters += [
            '-R', '-J', '-f', '-pad', '-joliet-long',
            '-sort', self.iso_sortfile.name,
            '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
            '-hide', catalog_file,
            '-hide-joliet', catalog_file,
        ]
        self.iso_loaders += [
            '-b', loader_file, '-c', catalog_file
        ]
        Command.run(
            [
                'isolinux-config', '--base', self.boot_path + '/loader',
                self.source_dir + '/' + loader_file
            ]
        )
        self.__create_sortfile()

    def add_efi_loader_parameters(self):
        loader_file = self.boot_path + '/efi'
        if os.path.exists(self.source_dir + '/' + loader_file):
            self.iso_loaders += [
                '-eltorito-alt-boot', '-b', loader_file,
                '-no-emul-boot', '-joliet-long'
            ]

    def get_iso_creation_parameters(self):
        return self.iso_parameters + self.iso_loaders

    def add_iso_header_end_marker(self):
        # TODO: see the glump file creation in the old kiwi
        pass

    def relocate_boot_catalog(self, isofile):
        # TODO
        pass

    def fix_boot_catalog(self, isofile):
        # TODO
        pass

    def isols(self, isofile):
        listing_type = namedtuple(
            'listing_type', ['name', 'filetype', 'start']
        )
        listing = Command.run(
            ['isoinfo', '-R', '-l', '-i', isofile]
        )
        listing_result = {}
        for line in listing.output.split('\n'):
            iso_entry = re.search(
                '^(.).*\s\[\s*(\d+)(\s+\d+)?\]\s+(.*?)\s*$', line
            )
            if iso_entry:
                entry_type = iso_entry.group(1)
                entry_name = iso_entry.group(4)
                entry_addr = int(iso_entry.group(2))
                if entry_type == '-':
                    listing_result[entry_addr] = listing_type(
                        name=entry_name,
                        filetype=entry_type,
                        start=entry_addr
                    )
        return collections.OrderedDict(
            sorted(listing_result.items())
        )

    def __create_sortfile(self):
        catalog_file = \
            self.source_dir + '/' + self.boot_path + '/boot.catalog'
        loader_file = \
            self.source_dir + '/' + self.boot_path + '/loader/isolinux.bin'
        with open(self.iso_sortfile.name, 'w') as sortfile:
            sortfile.write('%s 3\n' % catalog_file)
            sortfile.write('%s 2\n' % loader_file)

            for basedir, dirnames, filenames in os.walk(self.source_dir):
                for filename in filenames:
                    if filename == 'efi':
                        sortfile.write('%s/%s 1000001\n' % (basedir, filename))
                    elif filename == self.header_end_name:
                        sortfile.write('%s/%s 1000000\n' % (basedir, filename))
                    else:
                        sortfile.write('%s/%s 1\n' % (basedir, filename))
                for dirname in dirnames:
                    sortfile.write('%s/%s 1\n' % (basedir, dirname))
