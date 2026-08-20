# Copyright (c) 2026 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import glob
import logging
from typing import Dict

# project
from kiwi.system.identifier import SystemIdentifier
from kiwi.bootloader.config.base import BootLoaderConfigBase

import kiwi.defaults as defaults

log = logging.getLogger('kiwi')

class BootLoaderS390xIso(BootLoaderConfigBase):
    """
    **s390x iso bootloader configuration.**
    """
    def setup_disk_boot_images(
        self, boot_uuid, efi_uuid=None, lookup_path=None
    ) -> None:
        log.info('XXX s390x_iso: setup_disk_boot_images')

    def setup_disk_image_config(
        self, boot_uuid: str = '', root_uuid: str = '', hypervisor: str = '',
        kernel: str = '', initrd: str = '', boot_options: Dict[str, str] = {}
    ) -> None:
        log.info('XXX s390x_iso: setup_disk_image_config')

    def setup_install_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        log.info('XXX s390x_iso: setup_install_boot_images -- Creating s390x install boot images from template')

    def setup_install_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ) -> None:
        log.info('XXX s390x_iso: setup_install_image_config -- Creating s390x install image config from template')

    def setup_live_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        log.info('XXX s390x_iso: setup_live_boot_images -- Creating s390x live boot images from template')

    def setup_live_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ) -> None:
        log.info('XXX s390x_iso: setup_live_image_config -- Creating s390x live image config file from template')

    def setup_sysconfig_bootloader(self) -> None:
        log.info('XXX s390x_iso: setup_sysconfig_bootloader')

    def write(self) -> None:
        log.info('XXX s390x_iso: write')
