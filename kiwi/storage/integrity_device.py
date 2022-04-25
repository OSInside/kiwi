# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
import logging
from typing import (
    Optional, List, Dict, IO, Union
)

# project
import kiwi.defaults as defaults

from kiwi.command import Command
from kiwi.utils.temporary import Temporary
from kiwi.utils.signature import Signature
from kiwi.utils.block import BlockID
from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice

from kiwi.exceptions import KiwiOffsetError

log = logging.getLogger('kiwi')


class IntegrityDevice(DeviceProvider):
    """
    **Implements dm_integrity setup on a storage device**

    :param object storage_provider: Instance of class based on DeviceProvider
    """
    def __init__(self, storage_provider: DeviceProvider) -> None:
        # bind the underlaying block device providing class instance
        # to this object (e.g loop) if present. This is done to guarantee
        # the correct destructor order when the device should be released.
        self.storage_provider = storage_provider

        self.integrity_device: Optional[str] = None
        self.integrity_name = 'integrityRoot'
        self.integrity_algorithm = defaults.INTEGRITY_ALGORITHM
        self.integrity_format_options = [
            '--integrity', self.integrity_algorithm,
            '--sector-size', format(defaults.INTEGRITY_SECTOR_SIZE)
        ]
        self.integrity_open_options = [
            '--integrity', self.integrity_algorithm
        ]
        self.integrity_metadata_file: Optional[IO[bytes]] = None

    def get_device(self) -> Optional[MappedDevice]:
        """
        Instance of MappedDevice providing the dm_integrity device

        :return: mapped integrity device

        :rtype: MappedDevice
        """
        if self.integrity_device:
            return MappedDevice(
                device=self.integrity_device, device_provider=self
            )
        return None

    def create_dm_integrity(self, options: List[str] = []) -> None:
        """
        Create dm_integrity device.

        :param list options: further integritysetup format options
        """
        storage_device = self.storage_provider.get_device()
        log.info(f'Creating dm_integrity on {storage_device}')

        Command.run(
            [
                'integritysetup', '-v', '--batch-mode'
            ] + self.integrity_format_options + options + [
                'format', storage_device
            ]
        )
        Command.run(
            [
                'integritysetup', '-v', '--batch-mode'
            ] + self.integrity_open_options + options + [
                'open', storage_device, self.integrity_name
            ]
        )
        self.integrity_device = '/dev/mapper/' + self.integrity_name

    def create_integrity_metadata(self) -> None:
        """
        Create a metadata block containing information for
        dm_integrity device map in the following format:

        |header_string|0xFF|dm_integrity_meta|0xFF|0x0|

        header_string:
            '{version} {fstype} {ro|rw} integrity'

        dm_integrity_meta:
            '{provided_data_sectors} {sector_size}
            {parameter_count} {parameters}'

        The information for dm_integrity_meta is taken from the
        dm_integrity superblock. From the flags field of the superblock
        a list of space separated parameters is created. The first
        element of the parameter list contains information about the
        used hash algorithm which is not part of the superblock
        and provided according to the parameters passed along with
        the integritysetup call. The number of parameters in the
        resulting parameter list is provided as value in parameter_count
        and prepended to the actual list of parameters.

        Please note, writing of the metadata block can destroy
        the filesystem on the device_node if it was not created
        with a smaller size than the device_node !
        """
        metadata_format_version = defaults.DM_METADATA_FORMAT_VERSION
        filesystem = BlockID(self.integrity_device).get_filesystem()
        integrity_superblock = self._get_integrity_superblock()
        if filesystem and integrity_superblock:
            filesystem_mode = 'ro' if filesystem == 'squashfs' else 'rw'

            header_string = '{0} {1} {2} integrity'.format(
                metadata_format_version, filesystem, filesystem_mode
            )

            parameters = [
                f'internal_hash:{self.integrity_algorithm}'
            ] + list(integrity_superblock['flags'])
            dm_integrity_meta = '{0} {1} {2} {3}'.format(
                integrity_superblock['provided_data_sectors'],
                integrity_superblock['sector_size'],
                len(parameters),
                ' '.join(parameters)
            )

            self.integrity_metadata_file = Temporary().new_file()
            with open(self.integrity_metadata_file.name, 'wb') as meta:
                meta.write(header_string.encode("ascii"))
                meta.write(b'\xFF')
                meta.write(dm_integrity_meta.encode("ascii"))
                meta.write(b'\xFF')
                meta.write(b'\0')

    def sign_integrity_metadata(self) -> None:
        """
        Create an openssl based signature from the metadata block
        and attach it at the end of the block.
        """
        if self.integrity_metadata_file:
            Signature(self.integrity_metadata_file.name).sign()

    def write_integrity_metadata(self) -> None:
        """
        Write metadata block beginning at
        getsize64() - defaults.DM_METADATA_OFFSET
        """
        if self.integrity_metadata_file:
            meta_data_size = os.path.getsize(
                self.integrity_metadata_file.name
            )
            if meta_data_size > defaults.DM_METADATA_OFFSET:
                raise KiwiOffsetError(
                    'Metadata size of {0}b exceeds {1}b limit'.format(
                        meta_data_size, defaults.DM_METADATA_OFFSET
                    )
                )
            with open(self.integrity_metadata_file.name, 'rb') as meta:
                with open(self.storage_provider.get_device(), 'r+b') as target:
                    # seek --defaults.DM_METADATA_OFFSET from the
                    # end to reach the metadata start
                    # Please note, writing of the metadata block can destroy
                    # the filesystem on the device_node if it was not created
                    # with a smaller size than the device_node, you have been
                    # warned.
                    target.seek(-defaults.DM_METADATA_OFFSET, 2)
                    target.write(meta.read())

    def create_integritytab(self, filename: str) -> None:
        """
        Create integritytab, setting the UUID and options of the storage device

        :param string filename: file path name

        integrity UUID={0} - integrity-algorithm=foo

        """
        storage_device = self.storage_provider.get_device()
        with open(filename, 'w') as integritytab:
            block_operation = BlockID(storage_device)
            integritytab.write(
                '{0} PARTUUID={1} - integrity-algorithm={2}{3}'.format(
                    self.integrity_name,
                    block_operation.get_blkid('PARTUUID'),
                    self.integrity_algorithm,
                    os.linesep
                )
            )

    def is_loop(self) -> bool:
        """
        Check if storage provider is loop based

        Return loop status from base storage provider

        :return: True or False

        :rtype: bool
        """
        return self.storage_provider.is_loop()

    def _get_integrity_superblock(self) -> Dict[str, Union[str, List[str]]]:
        integrity: Dict[str, Union[str, List[str]]] = {}
        dump_call = Command.run(
            ['integritysetup', 'dump', self.storage_provider.get_device()]
        )
        for line in dump_call.output.strip().split(os.linesep):
            if line and not line.startswith('Info for'):
                entry = line.split(' ')
                if entry[0] == 'flags':
                    integrity[entry[0]] = entry[1:]
                else:
                    integrity[entry[0]] = entry[1]
        return integrity

    def __del__(self):
        if self.integrity_device:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                Command.run(
                    ['integritysetup', 'close', self.integrity_name]
                )
            except Exception:
                log.warning(
                    'Shutdown of integrity map %s failed, %s still busy',
                    self.integrity_name, self.integrity_device
                )
