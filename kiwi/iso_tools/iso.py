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
import struct
import logging
from collections import namedtuple

# project
from kiwi.iso_tools.cdrtools import IsoToolsCdrTools
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.utils.codec import Codec
from kiwi.exceptions import (
    KiwiIsoLoaderError,
    KiwiIsoMetaDataError,
    KiwiCommandError
)

log = logging.getLogger('kiwi')


class Iso:
    """
    **Implements helper methods around the creation of ISO filesystems**

    :param str header_id: static identifier string for self written headers
    :param str header_end_name: file name to store the header_id to
    :param str header_end_file: full file path for the header_end_name file
    :param str boot_path: architecture specific boot path on the ISO
    """
    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.header_id = '7984fc91-a43f-4e45-bf27-6d3aa08b24cf'
        self.header_end_name = 'header_end'
        self.header_end_file = self.source_dir + '/' + self.header_end_name
        self.boot_path = Defaults.get_iso_boot_path()

    @staticmethod
    def create_hybrid(offset, mbrid, isofile, efi_mode=False):
        """
        Create hybrid ISO

        A hybrid ISO embeds both, an isolinux signature as well as a
        disk signature. kiwi always adds an msdos and a GPT table for
        the disk signatures

        :param str offset: hex offset
        :param str mbrid: boot record id
        :param str isofile: path to the ISO file
        :param bool efi_mode: sets the iso to support efi firmware or not
        """
        ignore_errors = [
            # we ignore this error message, for details see:
            # http://www.syslinux.org/archives/2015-March/023306.html
            'Warning: more than 1024 cylinders',
            'Not all BIOSes will be able to boot this device'
        ]
        isohybrid_parameters = [
            '--offset', format(offset),
            '--id', mbrid,
            '--type', '0x83',
        ]
        if efi_mode:
            isohybrid_parameters.append('--uefi')
        isohybrid_call = Command.run(
            ['isohybrid'] + isohybrid_parameters + [isofile]
        )
        # isohybrid warning messages on stderr should be treated
        # as fatal errors except for the ones we want to ignore
        # because unexpected after effects might happen if e.g a
        # gpt partition should be embedded but only a warning
        # appears if isohybrid can't find an efi loader. Thus we
        # are more strict and fail
        if isohybrid_call.error:
            error_list = isohybrid_call.error.split(os.linesep)
            error_fatal_list = []
            for error in error_list:
                ignore = False
                for ignore_error in ignore_errors:
                    if ignore_error in error:
                        ignore = True
                        break
                if not ignore and error:
                    error_fatal_list.append(error)
            if error_fatal_list:
                raise KiwiCommandError(
                    'isohybrid issue not ignored by kiwi: {0}'.format(
                        error_fatal_list
                    )
                )

    @staticmethod
    def set_media_tag(isofile):
        """
        Include checksum tag in the ISO so it can be verified with
        the mediacheck program.

        :param str isofile: path to the ISO file
        """
        Command.run(
            [
                'tagmedia',
                '--md5',
                '--check',
                '--pad', '150',
                isofile
            ]
        )

    @staticmethod
    def relocate_boot_catalog(isofile):
        """
        Move ISO boot catalog to the standardized place

        Check location of the boot catalog and move it to the place where
        all BIOS and firwmare implementations expects it

        :param str isofile: path to the ISO file
        """
        iso_metadata = Iso._read_iso_metadata(isofile)
        Iso._validate_iso_metadata(iso_metadata)
        with open(isofile, 'rb+') as iso:
            new_boot_catalog_sector = iso_metadata.path_table_sector - 1
            new_volume_descriptor = Iso._read_iso_sector(
                new_boot_catalog_sector - 1, iso
            )
            new_volume_id = Iso._sub_string(
                data=new_volume_descriptor, length=7
            )
            if bytes(b'CD001') not in new_volume_id:
                new_boot_catalog_sector = None
                ref_sector = iso_metadata.boot_catalog_sector
                for sector in range(0x12, 0x40):
                    new_volume_descriptor = Iso._read_iso_sector(sector, iso)
                    new_volume_id = Iso._sub_string(
                        data=new_volume_descriptor, length=7
                    )
                    if bytes(b'TEA01') in new_volume_id or \
                       sector + 1 == ref_sector:

                        new_boot_catalog_sector = sector + 1
                        break

            if new_boot_catalog_sector and \
               iso_metadata.boot_catalog_sector != new_boot_catalog_sector:

                new_boot_catalog = Iso._read_iso_sector(
                    new_boot_catalog_sector, iso
                )
                empty_catalog = bytes(b'\x00') * 0x800
                if new_boot_catalog == empty_catalog:
                    eltorito_descriptor = Iso._embed_string_in_segment(
                        data=iso_metadata.eltorito_descriptor,
                        string=struct.pack('<I', new_boot_catalog_sector),
                        length=4,
                        start=0x47
                    )
                    Iso._write_iso_sector(
                        new_boot_catalog_sector, iso_metadata.boot_catalog, iso
                    )
                    Iso._write_iso_sector(
                        0x11, eltorito_descriptor, iso
                    )
                    log.debug(
                        'Relocated boot catalog from sector 0x%x to 0x%x',
                        iso_metadata.boot_catalog_sector,
                        new_boot_catalog_sector
                    )

    @staticmethod
    def fix_boot_catalog(isofile):
        """
        Fixup inconsistencies in boot catalog

        Make sure all catalog entries are in correct order and provide
        complete metadata information e.g catalog name

        :param str isofile: path to the ISO file
        """
        iso_metadata = Iso._read_iso_metadata(isofile)
        Iso._validate_iso_metadata(iso_metadata)
        boot_catalog = iso_metadata.boot_catalog
        first_catalog_entry = Iso._sub_string(
            data=boot_catalog, length=32, start=32
        )
        first_catalog_entry = Iso._embed_string_in_segment(
            data=first_catalog_entry,
            string=struct.pack('B19s', 1, bytes(b'Legacy (isolinux)')),
            length=20,
            start=12
        )
        boot_catalog = Iso._embed_string_in_segment(
            data=boot_catalog,
            string=first_catalog_entry,
            length=32,
            start=32
        )
        second_catalog_entry = Iso._sub_string(
            data=boot_catalog, length=32, start=64
        )
        second_catalog_entry = Iso._embed_string_in_segment(
            data=second_catalog_entry,
            string=struct.pack('B19s', 1, bytes(b'UEFI (grub)')),
            length=20,
            start=12
        )
        second_catalog_entry_sector = second_catalog_entry[0]
        if second_catalog_entry_sector == 0x88:
            boot_catalog = Iso._embed_string_in_segment(
                data=boot_catalog,
                string=second_catalog_entry,
                length=32,
                start=96
            )
            second_catalog_entry = struct.pack(
                'BBH28s', 0x91, 0xef, 1, bytes(b'')
            )
            boot_catalog = Iso._embed_string_in_segment(
                data=boot_catalog,
                string=second_catalog_entry,
                length=32,
                start=64
            )
            with open(isofile, 'rb+') as iso:
                Iso._write_iso_sector(
                    iso_metadata.boot_catalog_sector, boot_catalog, iso
                )
            log.debug('Fixed iso catalog contents')

    def create_header_end_marker(self):
        """
        Prepare iso file to become a hybrid iso image.

        To do this the offest address of the end of the first iso
        block is required. To lookup this address a reference(marker)
        file named 'header_end' is created and will show up as last
        file in the block.
        """
        with open(self.header_end_file, 'w') as marker:
            marker.write('%s\n' % self.header_id)

    def create_header_end_block(self, isofile):
        """
        Find offset address of file containing the header_id and
        replace it by a list of 2k blocks in range 0 - offset + 1
        This is the required preparation to support hybrid ISO
        images, meaning to let isohybrid work correctly

        :param string isofile: path to the ISO file

        :raises KiwiIsoLoaderError: if the header_id file is not found
        :return: 512 byte blocks offset address

        :rtype: int
        """
        file_count = 0
        offset = 0
        found_id = False
        iso_tool = IsoToolsCdrTools(self.source_dir)
        with open(isofile, 'rb') as iso:
            for start in iso_tool.list_iso(isofile):
                if file_count >= 8:  # check only the first 8 files
                    break
                file_count += 1
                read_buffer = ''
                for index in range(0, -9, -1):  # go back up to 8 blocks
                    offset = start + index
                    iso.seek(offset << 11, 0)
                    read_buffer = iso.read(len(self.header_id))
                    if read_buffer == self.header_id.encode():
                        iso.seek(0, 0)
                        file_count = 8
                        found_id = True
                        break

            if found_id:
                log.debug('Found ISO header_end id at offset:')
                log.debug('--> 2k blocks: %d', offset)
                log.debug('--> 512 byte blocks(isohybrid): %d', offset * 4)
                log.debug('--> bytes(loop mount): %d', offset * 2048)
                with open(self.header_end_file, 'wb') as marker:
                    for index in range(offset + 1):
                        marker.write(iso.read(2048))
            else:
                raise KiwiIsoLoaderError(
                    'Header ID not found in iso file %s' % isofile
                )
            return offset * 4

    def setup_isolinux_boot_path(self):
        """
        Write the base boot path into the isolinux loader binary

        :raises KiwiIsoLoaderError: if loader/isolinux.bin is not found
        """
        loader_base_directory = self.boot_path + '/loader'
        loader_file = '/'.join(
            [self.source_dir, self.boot_path, 'loader/isolinux.bin']
        )
        if not os.path.exists(loader_file):
            raise KiwiIsoLoaderError(
                'No isolinux loader {} found'.format(loader_file)
            )
        try:
            Command.run(
                [
                    'isolinux-config', '--base', loader_base_directory,
                    loader_file
                ]
            )
        except Exception:
            # Setup of the base directory failed. This happens if
            # isolinux-config was not able to identify the isolinux
            # signature. As a workaround a compat directory /isolinux
            # is created which hardlinks all loader files
            loader_source_directory = os.sep.join(
                [self.source_dir, loader_base_directory]
            )
            loader_compat_target_directory = os.sep.join(
                [self.source_dir, 'isolinux']
            )
            Command.run(
                [
                    'cp', '-a', '-l',
                    loader_source_directory + os.sep,
                    loader_compat_target_directory + os.sep
                ]
            )

    @staticmethod
    def _read_iso_metadata(isofile):
        iso_header_type = namedtuple(
            'iso_header_type', [
                'isofile',
                'volume_descriptor',
                'volume_id',
                'eltorito_descriptor',
                'eltorito_id',
                'path_table_sector',
                'boot_catalog_sector',
                'boot_catalog'
            ]
        )
        with open(isofile, 'rb') as iso:
            volume_descriptor = Iso._read_iso_sector(0x10, iso)
            volume_id = Iso._sub_string(
                data=volume_descriptor, length=7
            )
            eltorito_descriptor = Iso._read_iso_sector(0x11, iso)
            eltorito_id = Iso._sub_string(
                data=eltorito_descriptor, length=0x1e
            )
            try:
                path_table_sector = struct.unpack(
                    '<I', Iso._sub_string(
                        data=volume_descriptor, length=4, start=0x08c
                    )
                )[0]
            except Exception:
                # validation happens in __validate_iso_metadata
                path_table_sector = 0
            try:
                boot_catalog_sector = struct.unpack(
                    '<I', Iso._sub_string(
                        data=eltorito_descriptor, length=4, start=0x47
                    )
                )[0]
            except Exception:
                # validation happens in __validate_iso_metadata
                boot_catalog_sector = 0
            try:
                boot_catalog = Iso._read_iso_sector(
                    boot_catalog_sector, iso
                )
            except Exception:
                # validation happens in __validate_iso_metadata
                boot_catalog = None

            return iso_header_type(
                isofile=isofile,
                volume_descriptor=volume_descriptor,
                volume_id=volume_id,
                eltorito_descriptor=eltorito_descriptor,
                eltorito_id=eltorito_id,
                path_table_sector=path_table_sector,
                boot_catalog_sector=boot_catalog_sector,
                boot_catalog=boot_catalog
            )

    @staticmethod
    def _validate_iso_metadata(iso_header):
        if 'CD001' not in Codec.decode(iso_header.volume_id):
            raise KiwiIsoMetaDataError(
                '%s: this is not an iso9660 filesystem' %
                iso_header.isofile
            )
        if 'EL TORITO SPECIFICATION' not in Codec.decode(
            iso_header.eltorito_id
        ):
            raise KiwiIsoMetaDataError(
                '%s: this iso is not bootable' %
                iso_header.isofile
            )
        if iso_header.path_table_sector < 0x11:
            raise KiwiIsoMetaDataError(
                'strange path table location: 0x%x' %
                iso_header.path_table_sector
            )
        if iso_header.boot_catalog_sector < 0x12:
            raise KiwiIsoMetaDataError(
                'strange boot catalog location: 0x%x' %
                iso_header.boot_catalog_sector
            )
        if not iso_header.boot_catalog:
            raise KiwiIsoMetaDataError(
                '%s: no boot catalog found' %
                iso_header.isofile
            )

    @staticmethod
    def _read_iso_sector(sector, handle):
        handle.seek(sector * 0x800, 0)
        return handle.read(0x800)

    @staticmethod
    def _write_iso_sector(sector, data, handle):
        handle.seek(sector * 0x800, 0)
        handle.write(data)

    @staticmethod
    def _sub_string(data, length, start=0):
        return data[start:start + length]

    @staticmethod
    def _embed_string_in_segment(data, string, length, start):
        start_segment = data[0:start]
        end_segment = data[start + length:]
        return start_segment + string + end_segment
