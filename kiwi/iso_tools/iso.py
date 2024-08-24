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
# project
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.runtime_config import RuntimeConfig


class Iso:
    """
    **Implements helper methods around the creation of ISO filesystems**
    """
    def __init__(self, source_dir: str) -> None:
        """
        Create an instance of Iso helpers

        :param str source_dir:
            Directory path for iso source dir, root of ISO
        """
        self.source_dir = source_dir
        self.boot_path = Defaults.get_iso_boot_path()

    @staticmethod
    def set_media_tag(isofile: str) -> None:
        """
        Include checksum tag in the ISO so it can be verified with
        the mediacheck program.

        :param str isofile: path to the ISO file
        """
        media_tagger = RuntimeConfig().get_iso_media_tag_tool()
        if media_tagger == 'checkmedia':
            Command.run(
                [
                    'tagmedia',
                    '--digest', 'sha256',
                    '--check',
                    '--pad', '0',
                    isofile
                ]
            )
        elif media_tagger == 'isomd5sum':
            Command.run(
                [
                    'implantisomd5',
                    '--force',
                    isofile
                ]
            )
