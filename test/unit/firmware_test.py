from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.firmware import FirmWare


class TestFirmWare(object):
    def setup(self):
        self.firmware_bios = FirmWare('bios')
        self.firmware_efi = FirmWare('efi')
        self.firmware_ec2 = FirmWare('ec2')

    @raises(KiwiNotImplementedError)
    def test_firmware_unsupported(self):
        FirmWare('foo')

    def test_firmware_default(self):
        firmware = FirmWare(None)
        assert firmware.firmware == 'bios'

    def test_get_partition_table_type(self):
        assert self.firmware_bios.get_partition_table_type() == 'msdos'
        assert self.firmware_efi.get_partition_table_type() == 'gpt'

    def test_legacy_bios_mode(self):
        assert self.firmware_bios.legacy_bios_mode() is False
        assert self.firmware_efi.legacy_bios_mode() is True

    def test_ec2_mode(self):
        assert self.firmware_ec2.ec2_mode() == 'ec2'
        assert self.firmware_bios.ec2_mode() is None

    def test_efi_mode(self):
        assert self.firmware_bios.efi_mode() is None
        assert self.firmware_efi.efi_mode() == 'efi'

    def test_bios_mode(self):
        assert self.firmware_bios.bios_mode() is True
        assert self.firmware_efi.bios_mode() is False

    def test_get_legacy_bios_partition_size(self):
        assert self.firmware_bios.get_legacy_bios_partition_size() == 0
        assert self.firmware_efi.get_legacy_bios_partition_size() == 2

    def test_get_efi_partition_size(self):
        assert self.firmware_bios.get_efi_partition_size() == 0
        assert self.firmware_efi.get_efi_partition_size() == 200
