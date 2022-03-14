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
    Optional, Dict
)

# project
from kiwi.command import Command
from kiwi.utils.block import BlockID


class VeritySetup:
    """
    **Create block level verification data on file or device**
    """
    def __init__(
        self, image_filepath: str, data_blocks: Optional[int] = None
    ) -> None:
        """
        Construct new VeritySetup

        :param str image_filepath: block device node or filename
        :param int data_blocks:
            Number of blocks to verify, if not provided the whole
            image_filepath is used
        """
        self.image_filepath = image_filepath
        self.data_blocks = data_blocks
        self.verity_hash_offset = os.path.getsize(self.image_filepath)
        self.verity_dict: Dict[str, str] = {}

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
                f'--hash-offset={self.verity_hash_offset}'
            ] + (
                [
                    f'--data-blocks={self.data_blocks}'
                ] if self.data_blocks else []
            )
        )
        for line in verity_call.output.split(os.linesep):
            try:
                (key, value) = line.replace(' ', '').split(':', 2)
                self.verity_dict[key] = value
            except ValueError:
                # ignore any occurrence for which split failed
                pass
        return self.verity_dict

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
            partition_uuid = target_block_id.get_blkid('PARTUUID')
            with open(credentials_filepath, 'w') as verity:
                for key in sorted(self.verity_dict.keys()):
                    verity.write(f'{key}: {self.verity_dict[key]}{os.linesep}')
                verity.write(
                    f'PARTUUID: {partition_uuid}')
                verity.write(os.linesep)
                verity.write(
                    f'Root hashoffset: {self.verity_hash_offset}')
                verity.write(os.linesep)
                verity.write('Superblock: --no-superblock')
                verity.write(os.linesep)
