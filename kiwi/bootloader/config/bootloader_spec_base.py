# Copyright (c) 2022 Marcus Schäfer
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
from typing import (
    Dict, NamedTuple
)

# project
from kiwi.bootloader.config.base import BootLoaderConfigBase

target_type = NamedTuple(
    'target_type', [
        ('disk', str),
        ('install', str),
        ('live', str)
    ]
)


class BootLoaderSpecBase(BootLoaderConfigBase):
    """
    **Base class for Boot Loader Specification**

    This base class follows the bootloader specifications as
    described in:

    * https://uapi-group.org/specifications/specs/boot_loader_specification

    All supported bootloaders which follows this specification
    are derived from this base class

    :param object xml_state: instance of :class:`XMLState`
    :param str root_dir: root directory path name
    :param str boot_dir: boot directory path name
    :param dict custom_args:
        custom bootloader configuration parameters
    """
    def post_init(self, custom_args: Dict = {}) -> None:
        """
        Post init for all bootloader spec loaders

        Store custom arguments in an instance dict and initialize
        target identifiers
        """
        self.target = target_type(
            disk='disk', install='install(iso)', live='live(iso)'
        )
        self.custom_args = custom_args
        self.timeout = self.get_boot_timeout_seconds()
        self.cmdline = ''

    def write(self) -> None:
        """
        For bootloaders following the bootloader spec
        no collective write will happen
        """
        pass

    def setup_sysconfig_bootloader(self) -> None:
        """
        For bootloaders following the bootloader spec
        no setting to sysconfig/bootloader will be made
        """
        pass

    def setup_disk_image_config(
        self, boot_uuid: str = '', root_uuid: str = '', hypervisor: str = '',
        kernel: str = '', initrd: str = '', boot_options: Dict = {}
    ) -> None:
        """
        Create boot config file to boot from disk

        :param str boot_uuid: boot device UUID
        :param str root_uuid: root device UUID
        :param str hypervisor: unused
        :param str kernel: kernel name
        :param str initrd: initrd name
        :param dict boot_options:
            custom options dictionary required to setup the bootloader.

        Targeted to bootloader spec interface
        """
        self.custom_args['boot_uuid'] = boot_uuid
        self.custom_args['root_uuid'] = root_uuid
        self.custom_args['kernel'] = kernel
        self.custom_args['initrd'] = initrd
        self.custom_args['boot_options'] = boot_options
        self.cmdline = ' '.join(
            [self.get_boot_cmdline(boot_options.get('root_device'))]
        )
        self.setup_loader(self.target.disk)
        self.set_loader_entry(self.target.disk)

    def setup_install_image_config(
        self, mbrid: str, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ) -> None:
        """
        Create boot config file to boot install ISO image

        :param str mbrid: mbrid file name on boot device
        :param str hypervisor: unused
        :param str kernel: kernel name
        :param str initrd: initrd name

        Targeted to bootloader spec interface
        """
        self._setup_iso_image_config(mbrid, 'install(iso)', kernel, initrd)

    def setup_live_image_config(
        self, mbrid: str, hypervisor: str = '',
        kernel: str = '', initrd: str = ''
    ):
        """
        Create boot config file to boot live ISO image

        :param str mbrid: mbrid file name on boot device
        :param str hypervisor: unused
        :param str kernel: kernel name
        :param str initrd: initrd name

        Targeted to bootloader spec interface
        """
        self._setup_iso_image_config(mbrid, 'live(iso)', kernel, initrd)

    def setup_disk_boot_images(self, boot_uuid: str, lookup_path: str = ''):
        """
        Create bootloader image(s) for disk boot

        :param string mbrid: unused
        :param str lookup_path: unused

        Targeted to bootloader spec interface
        """
        self.create_loader_image(self.target.disk)

    def setup_install_boot_images(self, mbrid: str, lookup_path: str = ''):
        """
        Create bootloader image(s) for install ISO boot

        :param string mbrid: unused
        :param str lookup_path: unused

        Targeted to bootloader spec interface
        """
        self.create_loader_image(self.target.install)

    def setup_live_boot_images(self, mbrid: str, lookup_path: str = ''):
        """
        Create bootloader image(s) for live ISO boot

        :param string mbrid: unused
        :param str lookup_path: unused

        Targeted to bootloader spec interface
        """
        self.create_loader_image(self.target.live)

    def create_loader_image(self, target: str) -> None:
        """
        Create on demand bootloader image(s)

        For bootloaders following the bootloader spec we expect
        that the creation of a custom boot image is not needed.
        However, if needed this entry point exists

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)

        Implementation in specialized loader class
        """
        raise NotImplementedError

    def setup_loader(self, target: str) -> None:
        """
        Setup main bootloader configuration boot/loader.conf

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)

        Implementation in specialized loader class
        """
        raise NotImplementedError

    def set_loader_entry(self, target: str) -> None:
        """
        Setup bootloader menu entry boot/loader/entries/X.conf

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)

        Implementation in specialized loader class
        """
        raise NotImplementedError

    def _setup_iso_image_config(
        self, mbrid: str, target: str, kernel: str = '', initrd: str = ''
    ):
        self.custom_args['mbrid'] = mbrid
        self.custom_args['kernel'] = kernel
        self.custom_args['initrd'] = initrd

        self.setup_loader(target)
        self.set_loader_entry(target)
