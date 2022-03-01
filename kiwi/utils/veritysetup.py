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
from typing import Optional

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
        self.verity_call = None

    def format(self) -> None:
        self.verity_call = Command.run(
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

    def store_credentials(
        self, credentials_filepath: str, target_block_id: BlockID
    ) -> None:
        if self.verity_call:
            partition_uuid = target_block_id.get_blkid('PARTUUID')
            with open(credentials_filepath, 'w') as verity:
                verity.write(self.verity_call.output.strip())
                verity.write(os.linesep)
                verity.write(
                    f'PARTUUID: {partition_uuid}')
                verity.write(os.linesep)
                verity.write(
                    f'Root hashoffset: {self.verity_hash_offset}')
                verity.write(os.linesep)
                verity.write('Superblock: --no-superblock')
                verity.write(os.linesep)
