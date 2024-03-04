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
import sys
from typing import TYPE_CHECKING, Dict, Union, overload

if sys.version_info >= (3, 8):
    from typing import Literal  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import Literal  # pragma: no cover

from kiwi.exceptions import (
    KiwiBootLoaderConfigSetupError
)

if TYPE_CHECKING:  # pragma: nocover
    from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2
    from kiwi.bootloader.config.systemd_boot import BootLoaderSystemdBoot
    from kiwi.bootloader.config.custom import BootLoaderConfigCustom
    from kiwi.bootloader.config.zipl import BootLoaderZipl


@overload
def create_boot_loader_config(
    *, name: Literal["grub2"], xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "BootLoaderConfigGrub2":
    ...  # pragma: nocover


@overload
def create_boot_loader_config(
    *, name: Literal["grub2_s390x_emu"], xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "BootLoaderConfigGrub2":
    ...  # pragma: nocover


@overload
def create_boot_loader_config(
    *, name: Literal["systemd_boot"], xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "BootLoaderSystemdBoot":
    ...  # pragma: nocover


@overload
def create_boot_loader_config(
    *, name: Literal["zipl"], xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "BootLoaderZipl":
    ...  # pragma: nocover


@overload
def create_boot_loader_config(
    *, name: str, xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "Union[BootLoaderConfigGrub2, BootLoaderSystemdBoot, BootLoaderZipl]":
    ...  # pragma: nocover


def create_boot_loader_config(
    *, name: str, xml_state: object, root_dir: str,
    boot_dir: str = None, custom_args: Dict = None
) -> "Union[BootLoaderConfigGrub2, BootLoaderSystemdBoot, BootLoaderZipl, BootLoaderConfigCustom]":

    if name in ("grub2", "grub2_s390x_emu"):
        from kiwi.bootloader.config.grub2 import BootLoaderConfigGrub2
        return BootLoaderConfigGrub2(xml_state, root_dir, boot_dir, custom_args)
    if name == "systemd_boot":
        from kiwi.bootloader.config.systemd_boot import BootLoaderSystemdBoot
        return BootLoaderSystemdBoot(xml_state, root_dir, boot_dir, custom_args)
    if name == "zipl":
        from kiwi.bootloader.config.zipl import BootLoaderZipl
        return BootLoaderZipl(xml_state, root_dir, boot_dir, custom_args)
    if name == "custom":
        from kiwi.bootloader.config.custom import BootLoaderConfigCustom
        return BootLoaderConfigCustom(xml_state, root_dir, boot_dir, custom_args)

    raise KiwiBootLoaderConfigSetupError(
        f'Support for {name} bootloader config not implemented'
    )
