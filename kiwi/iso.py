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
from logger import log
from command import Command
from exceptions import (
    KiwiIsoLoaderError
)


class Iso(object):
    """
        Implements helper methods around the creation of an iso filesystem
    """
    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.header_id = '7984fc91-a43f-4e45-bf27-6d3aa08b24cf'
        self.header_end_name = 'header_end'
        self.header_end_file = self.source_dir + '/' + self.header_end_name
        self.arch = platform.machine()
        self.boot_path = 'boot/' + self.arch
        self.iso_sortfile = NamedTemporaryFile()
        self.iso_parameters = []
        self.iso_loaders = []

    @classmethod
    def create_hybrid(self, offset, mbrid, isofile):
        Command.run(
            [
                'isohybrid',
                '--offset', offset,
                '--id', mbrid.get_id(),
                '--type', '0x83',
                '--uefi', isofile
            ]
        )

    @classmethod
    def relocate_boot_catalog(self, isofile):
        # TODO
        pass

    @classmethod
    def fix_boot_catalog(self, isofile):
        # TODO
        pass

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
        with open(self.header_end_file, 'w') as marker:
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

    def create_header_end_block(self, isofile):
        file_count = 0
        offset = 0
        found_id = False
        with open(isofile, 'rb') as iso:
            for start in self.isols(isofile):
                if file_count >= 8:  # check only the first 8 files
                    break
                file_count += 1
                read_buffer = ''
                for index in range(0, -9, -1):  # go back up to 8 blocks
                    offset = start + index
                    iso.seek(offset << 11, 0)
                    read_buffer = iso.read(len(self.header_id))
                    if read_buffer == self.header_id:
                        iso.seek(0, 0)
                        file_count = 8
                        found_id = True
                        break

            if found_id:
                log.debug('Found ISO header_end id at offset:')
                log.debug('--> 2k blocks: %d', offset)
                log.debug('--> 512 byte blocks(isohybrid): %d', offset * 4)
                log.debug('--> bytes(loop mount): %d', offset * 2048)
                with open(self.header_end_file, 'w') as marker:
                    for index in range(offset):
                        marker.write(iso.read(2048))
            else:
                raise KiwiIsoLoaderError(
                    'Header ID not found in iso file %s' % isofile
                )
            return offset * 4

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
