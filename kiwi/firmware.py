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
import platform

# project
from defaults import Defaults

from exceptions import (
    KiwiNotImplementedError
)


class FirmWare(object):
    """
        According to the selected firmware some parameters in a disk
        image changes. This class provides methods to provide firmware
        dependent information
    """
    def __init__(self, firmware):
        if not firmware:
            firmware = 'bios'
        host_architecture = platform.machine()
        firmware_types = Defaults.get_firmware_types()
        if firmware not in firmware_types[host_architecture]:
            raise KiwiNotImplementedError(
                'support for firmware %s for arch %s not implemented' %
                (firmware, host_architecture)
            )
        self.efi_capable_firmware_names = [
            'efi', 'uefi', 'vboot'
        ]
        self.ec2_firmware_names = [
            'ec2', 'ec2hvm'
        ]
        self.firmware = firmware

    def get_partition_table_type(self):
        if self.efi_mode():
            return 'gpt'
        elif self.firmware == 'bios':
            return 'msdos'

    def legacy_bios_mode(self):
        if self.get_partition_table_type() == 'gpt':
            return True
        else:
            return False

    def efi_mode(self):
        if self.firmware in self.efi_capable_firmware_names:
            return self.firmware

    def ec2_mode(self):
        if self.firmware in self.ec2_firmware_names:
            return self.firmware

    def bios_mode(self):
        if self.firmware == 'bios':
            return True
        else:
            return False

    def get_legacy_bios_partition_size(self):
        if self.legacy_bios_mode():
            return Defaults.get_default_legacy_bios_mbytes()
        else:
            return 0

    def get_efi_partition_size(self):
        if self.efi_mode():
            return Defaults.get_default_efi_boot_mbytes()
        else:
            return 0
