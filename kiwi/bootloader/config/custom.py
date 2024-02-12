# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import Dict

# project
from kiwi.system.identifier import SystemIdentifier
from kiwi.bootloader.config.base import BootLoaderConfigBase


class BootLoaderConfigCustom(BootLoaderConfigBase):
    """
    **custom bootloader configuration.**
    """
    def setup_disk_boot_images(self, boot_uuid, lookup_path=None) -> None:
        raise NotImplementedError

    def setup_disk_image_config(
        self, boot_uuid: str = '', root_uuid: str = '', hypervisor: str = '',
        kernel: str = '', initrd: str = '', boot_options: Dict[str, str] = {}
    ) -> None:
        raise NotImplementedError

    def setup_install_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        raise NotImplementedError

    def setup_install_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ) -> None:
        raise NotImplementedError

    def setup_live_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        raise NotImplementedError

    def setup_live_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ) -> None:
        raise NotImplementedError

    def setup_sysconfig_bootloader(self) -> None:
        raise NotImplementedError

    def write(self) -> None:
        raise NotImplementedError
