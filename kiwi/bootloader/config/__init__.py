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
import importlib
from typing import Dict
from abc import (
    ABCMeta,
    abstractmethod
)

from kiwi.exceptions import (
    KiwiBootLoaderConfigSetupError
)


class BootLoaderConfig(metaclass=ABCMeta):
    """
    **BootLoaderConfig factory**

    :param string name: bootloader name
    :param object xml_state: instance of :class:`XMLState`
    :param string root_dir: root directory path name
    :param dict custom_args: custom bootloader config arguments dictionary
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        name: str, xml_state: object, root_dir: str,
        boot_dir: str = None, custom_args: Dict = None
    ):
        name_map = {
            'grub2': 'BootLoaderConfigGrub2'
            if name == 'grub2' or name == 'grub2_s390x_emu' else None,

            'isolinux': 'BootLoaderConfigIsoLinux'
            if name == 'isolinux' else None
        }

        for bootloader_namespace, bootloader_name in list(name_map.items()):
            if bootloader_name:
                break
        try:
            booloader_config = importlib.import_module(
                'kiwi.bootloader.config.{}'.format(bootloader_namespace)
            )
            return booloader_config.__dict__[bootloader_name](
                xml_state, root_dir, boot_dir, custom_args
            )
        except Exception:
            raise KiwiBootLoaderConfigSetupError(
                'Support for {} bootloader config not implemented'.format(name)
            )
