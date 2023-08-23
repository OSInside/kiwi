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
from typing import (
    Optional, Dict, IO
)

# project
import kiwi.defaults as defaults

from kiwi.utils.signature import Signature
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.utils.block import BlockID

from kiwi.exceptions import KiwiOffsetError


class VeritySetup:
    """
    **Create block level verification data on file or device**
    """
    def __init__(
        self, image_filepath: str, data_blocks: Optional[int] = None,
        hash_offset: int = 0
    ) -> None:
        """
        Construct new VeritySetup

        :param str image_filepath: block device node or filename
        :param int data_blocks:
            Number of blocks to verify, if not provided the whole
            image_filepath is used
        :param int hash_offset:
            Optional offset to start writing verity hash.
            If not specified it is assumed image_filepath
            is a file and not a block special such that the
            offset is calculated from the size of the file
        """
        self.image_filepath = image_filepath
        self.data_blocks = data_blocks
        self.verity_hash_offset = \
            hash_offset or os.path.getsize(self.image_filepath)
        self.verity_dict: Dict[str, str] = {}
        self.verification_metadata_file: Optional[IO[bytes]] = None

    def format(self) -> Dict[str, str]:
        """
        Run veritysetup on the given device node or filename
        and store the verification information onto the same
        device node or filename

        :return: veritysetup result information in key/value format

        :rtype: dict
        """
        verity_call = Command.run(
            [
                'veritysetup', 'format',
                self.image_filepath, self.image_filepath,
                '--no-superblock',
                f'--hash-offset={self.verity_hash_offset}',
                f'--hash-block-size={defaults.VERITY_HASH_BLOCKSIZE}'
            ] + (
                [
                    f'--data-blocks={self.data_blocks}',
                    f'--data-block-size={defaults.VERITY_DATA_BLOCKSIZE}'
                ] if self.data_blocks else []
            )
        )
        for line in verity_call.output.split(os.linesep):
            try:
                # strip out any space, tabs, newlines
                line = ''.join(line.split())
                # split out key:value based data
                (key, value) = line.split(':', 2)
                self.verity_dict[key] = value
            except ValueError:
                # ignore any occurrence for which split failed
                pass
        return self.verity_dict

    def get_hash_byte_size(self) -> int:
        """
        Run veritysetup into a temporary file to estimate
        the required bytesize

        :return: a byte value

        :rtype: int
        """
        temp_file = Temporary().new_file()
        Command.run(
            [
                'veritysetup', 'format',
                self.image_filepath, temp_file.name,
                '--no-superblock',
                f'--hash-block-size={defaults.VERITY_HASH_BLOCKSIZE}'
            ] + (
                [
                    f'--data-blocks={self.data_blocks}',
                    f'--data-block-size={defaults.VERITY_DATA_BLOCKSIZE}'
                ] if self.data_blocks else []
            )
        )
        return os.path.getsize(temp_file.name)

    def get_block_storage_filesystem(self) -> str:
        """
        Retrieve filesystem type from image_filepath. The method
        only returns a value if image_filepath at construction
        time of the VeritySetup object is a block device containing
        a filesystem

        :rtype: blkid TYPE value or empty string

        :return: str
        """
        try:
            return BlockID(self.image_filepath).get_filesystem()
        except Exception:
            return ''

    def write_verification_metadata(self, device_node: str) -> None:
        """
        Write metadata block beginning at
        getsize64() - defaults.DM_METADATA_OFFSET
        of the given device_node

        :param str device_node: block device node name
        """
        if self.verification_metadata_file:
            meta_data_size = os.path.getsize(
                self.verification_metadata_file.name
            )
            if meta_data_size > defaults.DM_METADATA_OFFSET:
                raise KiwiOffsetError(
                    'Metadata size of {0}b exceeds {1}b limit'.format(
                        meta_data_size, defaults.DM_METADATA_OFFSET
                    )
                )
            with open(self.verification_metadata_file.name, 'rb') as meta:
                with open(device_node, 'r+b') as target:
                    # seek --defaults.DM_METADATA_OFFSET from the
                    # end to reach the metadata start
                    # Please note, writing of the metadata block can destroy
                    # the filesystem on the device_node if it was not created
                    # with a smaller size than the device_node, you have been
                    # warned.
                    target.seek(-defaults.DM_METADATA_OFFSET, 2)
                    target.write(meta.read())

    def create_verity_verification_metadata(self) -> None:
        """
        Create a metadata block containing information for
        dm_verity verification in the following format:

        |header_string|0xFF|dm_verity_credentials|0xFF|0x0|

        header_string:
            '{version} {fstype} ro verity'

        dm_verity_credentials:
            '{hash_type} {data_blksize} {hash_blksize}
             {data_blocks} {hash_start_block} {algorithm} {root_hash} {salt}'

        Please note, writing of the metadata block can destroy
        the filesystem on the device_node if it was not created
        with a smaller size than the device_node !
        """
        metadata_format_version = defaults.DM_METADATA_FORMAT_VERSION
        filesystem = self.get_block_storage_filesystem()
        if filesystem and self.verity_dict:
            header_string = '{0} {1} ro verity'.format(
                metadata_format_version, filesystem
            )

            hash_start_block = int(
                self.verity_hash_offset / int(
                    self.verity_dict['Hashblocksize']
                )
            )
            dm_verity_credentials = '{0} {1} {2} {3} {4} {5} {6} {7}'.format(
                self.verity_dict['Hashtype'],
                self.verity_dict['Datablocksize'],
                self.verity_dict['Hashblocksize'],
                self.verity_dict['Datablocks'],
                hash_start_block,
                self.verity_dict['Hashalgorithm'],
                self.verity_dict['Roothash'],
                self.verity_dict['Salt']
            )

            self.verification_metadata_file = Temporary().new_file()
            with open(self.verification_metadata_file.name, 'wb') as meta:
                meta.write(header_string.encode("ascii"))
                meta.write(b'\xFF')
                meta.write(dm_verity_credentials.encode("ascii"))
                meta.write(b'\xFF')
                meta.write(b'\0')

    def sign_verification_metadata(self) -> None:
        """
        Create an openssl based signature from the metadata block
        and attach it at the end of the block.
        """
        if self.verification_metadata_file:
            Signature(self.verification_metadata_file.name).sign()

    def store_credentials(
        self, credentials_filepath: str, target_block_id: BlockID
    ) -> None:
        """
        Store verification credentials and other metadata to
        the given credentials_filepath

        :param str credentials_filepath: file path name
        :param BlockID target_block_id:
            instance of BlockID of the target storage device
        """
        if self.verity_dict:
            with open(credentials_filepath, 'w') as verity:
                for key in sorted(self.verity_dict.keys()):
                    verity.write(f'{key}: {self.verity_dict[key]}{os.linesep}')
                verity.write(
                    f'Root hashoffset: {self.verity_hash_offset}')
                verity.write(os.linesep)
                verity.write('Superblock: --no-superblock')
                verity.write(os.linesep)
