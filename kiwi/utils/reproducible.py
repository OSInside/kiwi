# Copyright (c) 2026 Marcus Schäfer.  All rights reserved.
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
import uuid
import hashlib
import logging
from typing import Optional

log = logging.getLogger('kiwi')

# namespace for name based (version 5) UUIDs created by kiwi
KIWI_UUID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, 'https://github.com/OSInside/kiwi'
)


class Reproducible:
    """
    **Helper methods for reproducible builds**

    All methods follow the specification from
    https://reproducible-builds.org/specs/source-date-epoch
    and only change behavior if the SOURCE_DATE_EPOCH environment
    variable is set. If not set, randomly generated or time based
    values stay as they are.
    """

    @staticmethod
    def get_source_date_epoch() -> Optional[int]:
        """
        Value of the SOURCE_DATE_EPOCH environment variable

        :return: seconds since the epoch or None if not set

        :rtype: int
        """
        sde = os.environ.get('SOURCE_DATE_EPOCH')
        return int(sde) if sde else None

    @staticmethod
    def get_seeded_uuid(seed: str) -> Optional[str]:
        """
        Name based UUID from SOURCE_DATE_EPOCH and the given seed

        Different seed values produce different UUIDs, the same
        seed and SOURCE_DATE_EPOCH always produce the same UUID

        :param str seed: name which makes the UUID unique in its scope

        :return: UUID string or None if SOURCE_DATE_EPOCH is not set

        :rtype: str
        """
        sde = Reproducible.get_source_date_epoch()
        if sde is None:
            return None
        return format(uuid.uuid5(KIWI_UUID_NAMESPACE, f'{sde}:{seed}'))

    @staticmethod
    def get_seeded_hex(seed: str) -> Optional[str]:
        """
        Hex string (32 bytes) from SOURCE_DATE_EPOCH and the given seed

        :param str seed: name which makes the value unique in its scope

        :return: hex string or None if SOURCE_DATE_EPOCH is not set

        :rtype: str
        """
        sde = Reproducible.get_source_date_epoch()
        if sde is None:
            return None
        return hashlib.sha256(f'{sde}:{seed}'.encode()).hexdigest()

    @staticmethod
    def clamp_mtime(path: str) -> None:
        """
        Set the modification time of path and all entries below path
        which are newer than SOURCE_DATE_EPOCH to SOURCE_DATE_EPOCH.
        Files created as part of the image build process, e.g.
        bootloader configuration files, otherwise carry the time
        of the build in their metadata

        :param str path: directory path
        """
        sde = Reproducible.get_source_date_epoch()
        if sde is None:
            return
        log.info(f'Clamping mtime below {path} to SOURCE_DATE_EPOCH:{sde}')
        entries = [path]
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                entries.append(os.path.join(root, name))
        for entry in entries:
            if os.lstat(entry).st_mtime > sde:
                os.utime(entry, (sde, sde), follow_symlinks=False)
