# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
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
import re
from typing import (
    Dict, List
)

# project
from kiwi.defaults import Defaults


class StackBuildDefaults:
    """
    **Implements stackbuild default values**

    Provides static methods for default values and state information
    """
    @staticmethod
    def get_stash_home() -> str:
        """
        Provides the base directory to store stash containers

        :return: dir path name

        :rtype: str
        """
        return '/var/tmp/kiwi-stash'

    @staticmethod
    def is_container_name_valid(name: str) -> bool:
        """
        Check container if name follows container naming rules

        Container names must start or end with a letter or number,
        and can contain only letters, numbers, and the dash (-) character.
        """
        return bool(
            re.match(r'^[0-9a-zA-Z][0-9a-zA-Z\-]*[0-9a-zA-Z]$', name)
        )

    @staticmethod
    def get_stash_exclude_list() -> List:
        """
        Provides the list of folders that are not relevant
        for the image root stash

        :return: list of file and directory names

        :rtype: list
        """
        return [
            'dev/*',
            'sys/*',
            'proc/*'
        ]

    @staticmethod
    def get_container_config(
        container_name: str, tag: str, maintainer: str
    ) -> Dict:
        """
        Provides the container config used for the stash
        created container

        :return: container config dict

        :rtype: dict
        """
        preparer = Defaults.get_preparer()
        return {
            'container_name': container_name,
            'container_tag': tag,
            'entry_command': ['/bin/sh'],
            'labels': {
                'io.osinside.kiwi.maintainer': maintainer,
                'io.osinside.kiwi.meta': preparer
            },
            'history': {
                'created_by': preparer,
                'comment': 'KIWI Root Tree Stash',
                'author': maintainer
            }
        }
