from mock import call, patch
import mock
import struct
from .test_helper import raises, patch_open
import sys
from builtins import bytes

from kiwi.exceptions import (
    KiwiIsoLoaderError,
    KiwiIsoMetaDataError,
    KiwiCommandError
)

from kiwi.iso_tools.iso import Iso
from tempfile import NamedTemporaryFile


class TestIso(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.iso = Iso('source-dir')

    @patch_open
    def test_create_header_end_marker(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.iso.create_header_end_marker()
        assert self.file_mock.write.called_once_with(
            'source-dir/header_end 1000000\n'
        )

    @raises(KiwiIsoLoaderError)
    @patch('os.path.exists')
    def test_setup_isolinux_boot_path_raises(self, mock_exists):
        mock_exists.return_value = False
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
    @patch('kiwi.iso_tools.iso.Path.create')
    @patch('os.path.exists')
    def test_setup_isolinux_boot_path_failed_isolinux_config(
        self, mock_exists, mock_path, mock_command
    ):
        mock_exists.return_value = True
        command_raises = [False, True]

        def side_effect(arg):
            if command_raises.pop():
                raise Exception

        mock_command.side_effect = side_effect
        self.iso.setup_isolinux_boot_path()
        mock_path.assert_called_once_with('source-dir/isolinux')
        assert mock_command.call_args_list[1] == call(
            [
                'bash', '-c',
                'ln source-dir/boot/x86_64/loader/* source-dir/isolinux'
            ]
        )

    def test_create_header_end_block(self):
        temp_file = NamedTemporaryFile()
        self.iso.header_end_file = temp_file.name
        assert self.iso.create_header_end_block(
            '../data/iso_with_marker.iso'
        ) == 96

    @raises(KiwiIsoLoaderError)
    def test_create_header_end_block_raises(self):
        temp_file = NamedTemporaryFile()
        self.iso.header_end_file = temp_file.name
        self.iso.create_header_end_block(
            '../data/iso_no_marker.iso'
        )

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

    @raises(KiwiCommandError)
    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid_with_error(self, mock_command):
        command = mock.Mock()
        command.error = 'some error message'
        mock_command.return_value = command
        Iso.create_hybrid(42, '0x0815', 'some-iso', 'efi')

    @raises(KiwiCommandError)
    @patch('kiwi.iso_tools.iso.Command.run')
    def test_create_hybrid_with_multiple_errors(self, mock_command):
        command = mock.Mock()
        command.error = \
            'isohybrid: Warning: more than 1024 cylinders: 1817\n' + \
            'isohybrid: Not all BIOSes will be able to boot this device\n' + \
            'isohybrid: some other error we do not ignore'
        mock_command.return_value = command
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

    @patch_open
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_iso9660_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = bytes(b'bogus')
        Iso.fix_boot_catalog('isofile')

    @patch_open
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_not_bootable(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = bytes(b'CD001')
        Iso.fix_boot_catalog('isofile')

    @patch_open
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_path_table_sector_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        read_results = [bytes(b'EL TORITO SPECIFICATION'), bytes(b'CD001')]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch_open
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_catalog_sector_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        read_results = [bytes(b'EL TORITO SPECIFICATION'), volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch_open
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_catalog_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            bytes(b'CD001') + bytes(b'_') * (0x08c - 0x5) + bytes(b'0x1d5f23a')
        eltorito_descriptor = \
            bytes(b'EL TORITO SPECIFICATION') + \
            bytes(b'_') * (0x47 - 0x17) + bytes(b'0x1d5f23a')
        read_results = [eltorito_descriptor, volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch_open
    def test_relocate_boot_catalog(self, mock_open):
        mock_open.return_value = self.context_manager_mock
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

        self.file_mock.read.side_effect = side_effect

        Iso.relocate_boot_catalog('isofile')
        assert self.file_mock.write.call_args_list == [
            call(bytes(b'catalog')),
            call(
                bytes(b'EL TORITO SPECIFICATION') +
                bytes(b'_') * (0x47 - 0x17) + bytes(b'\x13\x00\x00\x005f23a')
            )
        ]

    @patch_open
    def test_fix_boot_catalog(self, mock_open):
        mock_open.return_value = self.context_manager_mock
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

        self.file_mock.read.side_effect = side_effect

        Iso.fix_boot_catalog('isofile')

        if sys.byteorder == 'big':
            assert self.file_mock.write.call_args_list == [
                call(
                    bytes(b'_') * 44 +
                    bytes(b'\x01Legacy (isolinux)\x00\x00\x91\xef\x00\x01') +
                    bytes(b'\x00') * 28 +
                    bytes(b'\x88___________\x01UEFI (grub)') +
                    bytes(b'\x00') * 8
                )
            ]
        else:
            assert self.file_mock.write.call_args_list == [
                call(
                    bytes(b'_') * 44 +
                    bytes(b'\x01Legacy (isolinux)\x00\x00\x91\xef\x01') +
                    bytes(b'\x00') * 29 +
                    bytes(b'\x88___________\x01UEFI (grub)') +
                    bytes(b'\x00') * 8
                )
            ]
