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

from ...exceptions import (
    KiwiBootLoaderInstallSetupError
)


class BootLoaderInstall(metaclass=ABCMeta):
    """
    **BootLoaderInstall Factory**

    :param string name: bootloader name
    :param string root_dir: root directory path name
    :param object device_provider: instance of :class:`DeviceProvider`
    :param dict custom_args: custom arguments dictionary
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        name: str, root_dir: str, device_provider: object,
        custom_args: Dict = None
    ):
        name_map = {
            'grub2': {'grub2': 'BootLoaderInstallGrub2'},
            'grub2_s390x_emu': {'grub2': 'BootLoaderInstallGrub2'}
        }
        try:
            (bootloader_namespace, bootloader_name) = \
                list(name_map[name].items())[0]
            bootloader_install = importlib.import_module(
                'kiwi.bootloader.install.{}'.format(bootloader_namespace)
            )
            return bootloader_install.__dict__[bootloader_name](
                root_dir, device_provider, custom_args
            )
        except Exception:
            raise KiwiBootLoaderInstallSetupError(
                f'Support for {name} bootloader installation not implemented'
            )
