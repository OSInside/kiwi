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
import re

# project
from .defaults import Defaults

from .exceptions import (
    KiwiNotImplementedError
)


class FirmWare:
    """
    **Implements firmware specific methods**

    According to the selected firmware some parameters in a disk
    image changes. This class provides methods to provide firmware
    dependant information

    * :param object xml_state: instance of :class:`XMLState`
    """
    def __init__(self, xml_state):
        self.arch = Defaults.get_platform_name()
        self.zipl_target_type = \
            xml_state.get_build_type_bootloader_targettype()
        self.firmware = xml_state.build_type.get_firmware()
        self.efipart_mbytes = xml_state.build_type.get_efipartsize()
        self.efi_partition_table = xml_state.build_type.get_efiparttable()
        self.efi_csm = True if xml_state.build_type.get_eficsm() is None \
            else xml_state.build_type.get_eficsm()

        if not self.firmware:
            self.firmware = Defaults.get_default_firmware(self.arch)

        if self.firmware and self.firmware != 'custom':
            firmware_types = Defaults.get_firmware_types()
            if self.firmware not in firmware_types[self.arch]:
                raise KiwiNotImplementedError(
                    'support for firmware %s for arch %s not implemented' %
                    (self.firmware, self.arch)
                )

    def get_partition_table_type(self):
        """
        Provides partition table type according to architecture and firmware

        :return: partition table name

        :rtype: str
        """
        if 's390' in self.arch:
            if self.zipl_target_type and 'CDL' in self.zipl_target_type:
                return 'dasd'
            else:
                return 'msdos'
        elif 'ppc64' in self.arch:
            return 'gpt'
        elif self.efi_mode():
            default_efi_table = Defaults.get_default_efi_partition_table_type()
            return self.efi_partition_table or default_efi_table
        else:
            return 'msdos'

    def legacy_bios_mode(self) -> bool:
        """
        Check if the legacy boot from BIOS systems should be activated

        :return: True or False

        :rtype: bool
        """
        if self.get_partition_table_type() == 'gpt':
            if (self.arch == 'x86_64' or re.match('i.86', self.arch)) and \
               (self.firmware == 'efi' or self.firmware == 'uefi') and \
               self.efi_csm:
                return True
            else:
                return False
        else:
            return False

    def efi_mode(self) -> str:
        """
        Check if EFI mode is requested

        :return: The requested EFI mode or None if no EFI mode requested

        :rtype: str
        """
        if self.firmware in Defaults.get_efi_capable_firmware_names():
            return self.firmware
        return ''

    def ec2_mode(self):
        """
        Check if EC2 mode is requested

        :return: True or False

        :rtype: bool
        """
        if self.firmware in Defaults.get_ec2_capable_firmware_names():
            return self.firmware

    def bios_mode(self):
        """
        Check if BIOS mode is requested

        :return: True or False

        :rtype: bool
        """
        if self.firmware == 'bios':
            return True
        else:
            return False

    def ofw_mode(self):
        """
        Check if OFW mode is requested

        :return: True or False

        :rtype: bool
        """
        if self.firmware == 'ofw':
            return True
        else:
            return False

    def opal_mode(self):
        """
        Check if Opal mode is requested

        :return: True or False

        :rtype: bool
        """
        if self.firmware == 'opal':
            return True
        else:
            return False

    def get_legacy_bios_partition_size(self):
        """
        Size of legacy bios_grub partition if legacy BIOS mode is
        required. Returns 0 if no such partition is needed

        :return: mbsize value

        :rtype: int
        """
        if self.legacy_bios_mode():
            return Defaults.get_default_legacy_bios_mbytes()
        else:
            return 0

    def get_efi_partition_size(self):
        """
        Size of EFI partition.
        Returns 0 if no such partition is needed

        :return: mbsize value

        :rtype: int
        """
        if self.efi_mode():
            if self.efipart_mbytes:
                return self.efipart_mbytes
            else:
                return Defaults.get_default_efi_boot_mbytes()
        else:
            return 0

    def get_prep_partition_size(self):
        """
        Size of Prep partition if OFW mode is requested.
        Returns 0 if no such partition is needed

        :return: mbsize value

        :rtype: int
        """
        if self.ofw_mode():
            return Defaults.get_default_prep_mbytes()
        else:
            return 0
