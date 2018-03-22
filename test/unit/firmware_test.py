from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiNotImplementedError
from kiwi.firmware import FirmWare


class TestFirmWare(object):
    @patch('platform.machine')
    def setup(self, mock_platform):
        mock_platform.return_value = 'x86_64'
        xml_state = mock.Mock()
        xml_state.build_type.get_firmware = mock.Mock()
        xml_state.build_type.get_firmware.return_value = 'bios'
        self.firmware_bios = FirmWare(xml_state)

        xml_state.build_type.get_efiparttable.return_value = None
        xml_state.build_type.get_efipartsize.return_value = None
        xml_state.build_type.get_firmware.return_value = 'efi'
        self.firmware_efi = FirmWare(xml_state)

        xml_state.build_type.get_efiparttable.return_value = 'msdos'
        xml_state.build_type.get_efipartsize.return_value = None
        xml_state.build_type.get_firmware.return_value = 'efi'
        self.firmware_efi_mbr = FirmWare(xml_state)

        xml_state.build_type.get_efipartsize.return_value = 42
        self.firmware_efi_custom_efi_part = FirmWare(xml_state)

        xml_state.build_type.get_firmware.return_value = 'ec2'
        self.firmware_ec2 = FirmWare(xml_state)

        mock_platform.return_value = 's390x'
        xml_state.build_type.get_firmware.return_value = None
        xml_state.build_type.get_zipl_targettype = mock.Mock()
        xml_state.build_type.get_zipl_targettype.return_value = 'LDL'
        self.firmware_s390_ldl = FirmWare(xml_state)

        xml_state.build_type.get_zipl_targettype.return_value = 'CDL'
        self.firmware_s390_cdl = FirmWare(xml_state)

        xml_state.build_type.get_zipl_targettype.return_value = 'SCSI'
        self.firmware_s390_scsi = FirmWare(xml_state)

        mock_platform.return_value = 'ppc64le'
        xml_state.build_type.get_firmware.return_value = 'ofw'
        self.firmware_ofw = FirmWare(xml_state)

        xml_state.build_type.get_firmware.return_value = 'opal'
        self.firmware_opal = FirmWare(xml_state)

        mock_platform.return_value = 'arm64'

    @raises(KiwiNotImplementedError)
    def test_firmware_unsupported(self):
        xml_state = mock.Mock()
        xml_state.build_type.get_firmware = mock.Mock(
            return_value='bogus'
        )
        FirmWare(xml_state)

    def test_get_partition_table_type(self):
        assert self.firmware_bios.get_partition_table_type() == 'msdos'
        assert self.firmware_efi.get_partition_table_type() == 'gpt'
        assert self.firmware_efi_mbr.get_partition_table_type() == 'msdos'
        assert self.firmware_s390_ldl.get_partition_table_type() == 'dasd'
        assert self.firmware_s390_cdl.get_partition_table_type() == 'dasd'
        assert self.firmware_s390_scsi.get_partition_table_type() == 'msdos'

    def test_get_partition_table_type_ppc_ofw_mode(self):
        assert self.firmware_ofw.get_partition_table_type() == 'msdos'

    def test_get_partition_table_type_ppc_opal_mode(self):
        assert self.firmware_opal.get_partition_table_type() == 'gpt'

    def test_legacy_bios_mode(self):
        assert self.firmware_bios.legacy_bios_mode() is False
        assert self.firmware_efi.legacy_bios_mode() is True

    def test_legacy_bios_mode_non_x86_platform(self):
        self.firmware_efi.arch = 'arm64'
        assert self.firmware_efi.legacy_bios_mode() is False

    def test_ec2_mode(self):
        assert self.firmware_ec2.ec2_mode() == 'ec2'
        assert self.firmware_bios.ec2_mode() is None

    def test_efi_mode(self):
        assert self.firmware_bios.efi_mode() is None
        assert self.firmware_efi.efi_mode() == 'efi'

    def test_bios_mode(self):
        assert self.firmware_bios.bios_mode() is True
        assert self.firmware_efi.bios_mode() is False

    def test_ofw_mode(self):
        assert self.firmware_ofw.ofw_mode() is True

    def test_opal_mode(self):
        assert self.firmware_opal.opal_mode() is True

    def test_get_legacy_bios_partition_size(self):
        assert self.firmware_bios.get_legacy_bios_partition_size() == 0
        assert self.firmware_efi.get_legacy_bios_partition_size() == 2

    def test_get_efi_partition_size(self):
        assert self.firmware_bios.get_efi_partition_size() == 0
        assert self.firmware_efi.get_efi_partition_size() == 20
        assert self.firmware_efi_custom_efi_part.get_efi_partition_size() == 42

    def test_get_prep_partition_size(self):
        assert self.firmware_ofw.get_prep_partition_size() == 8
