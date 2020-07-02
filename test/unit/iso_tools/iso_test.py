from builtins import bytes
from mock import (
    call, patch, mock_open
)
from pytest import raises
import mock
import struct
import pytest
import sys


from kiwi.iso_tools.iso import Iso
from kiwi.path import Path
from tempfile import NamedTemporaryFile

from kiwi.exceptions import (
    KiwiIsoLoaderError,
    KiwiIsoMetaDataError,
    KiwiCommandError
)


class TestIso:
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.iso = Iso('source-dir')

    def test_create_header_end_marker(self):
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.iso.create_header_end_marker()
        assert m_open.return_value.write.called_once_with(
            'source-dir/header_end 1000000\n'
        )

    @patch('os.path.exists')
    def test_setup_isolinux_boot_path_raises(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiIsoLoaderError):
            self.iso.setup_isolinux_boot_path()

    @patch('os.path.exists')
    @patch('kiwi.iso_tools.iso.Command.run')
    def test_setup_isolinux_boot_path(self, mock_command, mock_exists):
        mock_exists.return_value = True
        self.iso.setup_isolinux_boot_path()
        mock_command.assert_called_once_with(
            [
                'isolinux-config', '--base', 'boot/x86_64/loader',
                'source-dir/boot/x86_64/loader/isolinux.bin'
            ]
        )

    @patch('kiwi.iso_tools.iso.Command.run')
    @patch('os.path.exists')
    def test_setup_isolinux_boot_path_failed_isolinux_config(
        self, mock_exists, mock_command
    ):
        mock_exists.return_value = True
        command_raises = [False, True]

        def side_effect(arg):
            if command_raises.pop():
                raise Exception

        mock_command.side_effect = side_effect
        self.iso.setup_isolinux_boot_path()
        assert mock_command.call_args_list[1] == call(
            [
                'cp', '-a', '-l',
                'source-dir/boot/x86_64/loader/', 'source-dir/isolinux/'
            ]
        )

    @pytest.mark.skipif(
        Path.which('isoinfo') is None, reason='requires cdrtools'
    )
    def test_create_header_end_block_on_test_iso(self):
        temp_file = NamedTemporaryFile()
        self.iso.header_end_file = temp_file.name
        assert self.iso.create_header_end_block(
            '../data/iso_with_marker.iso'
        ) == 96

    @patch('kiwi.iso_tools.iso.IsoToolsCdrTools')
    def test_create_header_end_block(self, mock_IsoToolsCdrTools):
        iso_tool = mock.Mock()
        iso_tool.list_iso.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mock_IsoToolsCdrTools.return_value = iso_tool

        m_open = mock_open(read_data=b'7984fc91-a43f-4e45-bf27-6d3aa08b24cf')
        with patch('builtins.open', m_open, create=True):
            self.iso.create_header_end_block('some-iso-file')

        assert m_open.call_args_list == [
            call('some-iso-file', 'rb'),
            call('source-dir/header_end', 'wb')
        ]

    @pytest.mark.skipif(
        Path.which('isoinfo') is None, reason='requires cdrtools'
    )
    def test_create_header_end_block_raises_on_test_iso(self):
        temp_file = NamedTemporaryFile()
        self.iso.header_end_file = temp_file.name
        with raises(KiwiIsoLoaderError):
            self.iso.create_header_end_block(
                '../data/iso_no_marker.iso'
            )

    @patch('kiwi.iso_tools.iso.IsoToolsCdrTools')
    def test_create_header_end_block_raises(
        self, mock_IsoToolsCdrTools
    ):
        with patch('builtins.open'):
            with raises(KiwiIsoLoaderError):
                self.iso.create_header_end_block('some-iso-file')

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid(self, mock_command):
        command = mock.Mock()
        command.error = None
        mock_command.return_value = command
        Iso.create_hybrid(42, '0x0815', 'some-iso', 'efi')
        mock_command.assert_called_once_with(
            [
                'isohybrid', '--offset', '42',
                '--id', '0x0815', '--type', '0x83',
                '--uefi', 'some-iso'
            ]
        )

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid_with_error(self, mock_command):
        command = mock.Mock()
        command.error = 'some error message'
        mock_command.return_value = command
        with raises(KiwiCommandError):
            Iso.create_hybrid(42, '0x0815', 'some-iso', 'efi')

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid_with_multiple_errors(self, mock_command):
        command = mock.Mock()
        command.error = \
            'isohybrid: Warning: more than 1024 cylinders: 1817\n' + \
            'isohybrid: Not all BIOSes will be able to boot this device\n' + \
            'isohybrid: some other error we do not ignore'
        mock_command.return_value = command
        with raises(KiwiCommandError):
            Iso.create_hybrid(42, '0x0815', 'some-iso', 'efi')

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid_with_cylinders_warning(self, mock_command):
        command = mock.Mock()
        command.error = \
            'isohybrid: Warning: more than 1024 cylinders: 1817\n' + \
            'isohybrid: Not all BIOSes will be able to boot this device\n'
        mock_command.return_value = command
        Iso.create_hybrid(42, '0x0815', 'some-iso', 'efi')
        mock_command.assert_called_once_with(
            [
                'isohybrid', '--offset', '42',
                '--id', '0x0815', '--type', '0x83',
                '--uefi', 'some-iso'
            ]
        )

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_set_media_tag(self, mock_command):
        Iso.set_media_tag('foo')
        mock_command.assert_called_once_with(
            ['tagmedia', '--md5', '--check', '--pad', '150', 'foo']
        )

    def test_iso_metadata_iso9660_invalid(self):
        m_open = mock_open(read_data=b'bogus')
        with patch('builtins.open', m_open, create=True):
            with raises(KiwiIsoMetaDataError):
                Iso.fix_boot_catalog('isofile')

    def test_iso_metadata_not_bootable(self):
        m_open = mock_open(read_data=b'CD001')
        with patch('builtins.open', m_open, create=True):
            with raises(KiwiIsoMetaDataError):
                Iso.fix_boot_catalog('isofile')

    def test_iso_metadata_path_table_sector_invalid(self):
        read_results = [bytes(b'EL TORITO SPECIFICATION'), bytes(b'CD001')]

        def side_effect(arg):
            return read_results.pop()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.read.side_effect = side_effect
            with raises(KiwiIsoMetaDataError):
                Iso.fix_boot_catalog('isofile')

    def test_iso_metadata_catalog_sector_invalid(self):
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        read_results = [bytes(b'EL TORITO SPECIFICATION'), volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.read.side_effect = side_effect
            with raises(KiwiIsoMetaDataError):
                Iso.fix_boot_catalog('isofile')

    def test_iso_metadata_catalog_invalid(self):
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        eltorito_descriptor = \
            bytes(b'EL TORITO SPECIFICATION') + \
            bytes(b'_') * (0x47 - 0x17) + bytes(b'0x1d5f23a')
        read_results = [eltorito_descriptor, volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.read.side_effect = side_effect
            with raises(KiwiIsoMetaDataError):
                Iso.fix_boot_catalog('isofile')

    def test_relocate_boot_catalog(self):
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        eltorito_descriptor = \
            bytes(b'EL TORITO SPECIFICATION') + \
            bytes(b'_') * (0x47 - 0x17) + bytes(b'0x1d5f23a')
        new_volume_descriptor = \
            bytes(b'bogus')
        next_new_volume_descriptor = \
            bytes(b'TEA01')
        new_boot_catalog = bytes(b'\x00') * 0x800
        read_results = [
            new_boot_catalog,
            next_new_volume_descriptor,
            new_volume_descriptor,
            bytes(b'catalog'),
            eltorito_descriptor,
            volume_descriptor
        ]

        def side_effect(arg):
            return read_results.pop()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.read.side_effect = side_effect
            Iso.relocate_boot_catalog('isofile')

        assert m_open.return_value.write.call_args_list == [
            call(bytes(b'catalog')),
            call(
                bytes(
                    b'EL TORITO SPECIFICATION'
                ) + bytes(
                    b'_'
                ) * (0x47 - 0x17) + bytes(b'\x13\x00\x00\x005f23a')
            )
        ]

    def test_fix_boot_catalog(self):
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        eltorito_descriptor = \
            bytes(b'EL TORITO SPECIFICATION') + \
            bytes(b'_') * (0x47 - 0x17) + bytes(b'0x1d5f23a')
        boot_catalog = bytes(b'_') * 64 + struct.pack('B', 0x88) + \
            bytes(b'_') * 32
        read_results = [
            boot_catalog,
            eltorito_descriptor,
            volume_descriptor
        ]

        def side_effect(arg):
            return read_results.pop()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.read.side_effect = side_effect
            Iso.fix_boot_catalog('isofile')

        if sys.byteorder == 'big':
            assert self.file_mock.write.call_args_list == [
                call(
                    bytes(
                        b'_'
                    ) * 44 + bytes(
                        b'\x01Legacy (isolinux)\x00\x00\x91\xef\x00\x01'
                    ) + bytes(
                        b'\x00'
                    ) * 28 + bytes(
                        b'\x88___________\x01UEFI (grub)'
                    ) + bytes(b'\x00') * 8
                )
            ]
        else:
            assert m_open.return_value.write.call_args_list == [
                call(
                    bytes(
                        b'_'
                    ) * 44 + bytes(
                        b'\x01Legacy (isolinux)\x00\x00\x91\xef\x01'
                    ) + bytes(
                        b'\x00'
                    ) * 29 + bytes(
                        b'\x88___________\x01UEFI (grub)'
                    ) + bytes(b'\x00') * 8
                )
            ]
