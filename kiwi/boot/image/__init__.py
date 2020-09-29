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
import importlib
from typing import List
from abc import (
    ABCMeta,
    abstractmethod
)

from kiwi.exceptions import (
    KiwiBootImageSetupError
)


class BootImage(metaclass=ABCMeta):
    """
    **BootImge Factory**

    :param object xml_state: Instance of :class:`XMLState`
    :param string target_dir: target dir to store the initrd
    :param string root_dir: system image root directory
    :param list signing_keys: list of package signing keys
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        xml_state: object, target_dir: str,
        root_dir: str=None, signing_keys: List=None  # noqa: E252
    ):
        initrd_system = xml_state.get_initrd_system()
        name_map = {
            'builtin_kiwi':
                'BootImageKiwi' if initrd_system == 'kiwi' else None,
            'dracut':
                'BootImageDracut' if initrd_system == 'dracut' else None
        }
        for boot_image_namespace, boot_image_name in list(name_map.items()):
            if boot_image_name:
                break
        try:
            boot_image = importlib.import_module(
                'kiwi.boot.image.{0}'.format(boot_image_namespace)
            )
            return boot_image.__dict__[boot_image_name](
                xml_state, target_dir, root_dir, signing_keys
            )
        except Exception as issue:
            raise KiwiBootImageSetupError(
                'Support for {0} initrd system not implemented: {1}'.format(
                    initrd_system, issue
                )
            )
