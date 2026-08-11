# Copyright (c) 2026 SUSE Linux GmbH.  All rights reserved.
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

# project
from kiwi.command import Command
from kiwi.path import Path


class SparseFile:
    """
    **Create sparse files**
    """
    @staticmethod
    def create(filename: str, size: str) -> None:
        if Path.which(filename='qemu-img', access_mode=os.X_OK):
            Command.run(
                ['qemu-img', 'create', filename, size]
            )
        else:
            Command.run(
                [
                    'dd', 'if=/dev/null', f'of={filename}',
                    'bs=1', 'count=0', f'seek={size}'
                ]
            )
