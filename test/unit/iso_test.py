
from mock import patch
from mock import call
import mock
import struct
from .test_helper import *
import sys

from kiwi.exceptions import *

from kiwi.iso import Iso
from collections import namedtuple
from tempfile import NamedTemporaryFile


class TestIso(object):
    @patch('kiwi.iso.NamedTemporaryFile')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_tempfile):
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_machine.return_value = 'x86_64'
        mock_tempfile.return_value = temp_type(
            name='sortfile'
        )
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.iso = Iso('source-dir')

    @patch('builtins.open')
    @patch('os.path.exists')
    @raises(KiwiIsoLoaderError)
    def test_init_iso_creation_parameters_no_loader(
        self, mock_exists, mock_open
    ):
        mock_exists.return_value = False
        self.iso.init_iso_creation_parameters()

    @patch('kiwi.iso.NamedTemporaryFile')
    @patch('platform.machine')
    def test_init_for_ix86_platform(self, mock_machine, mock_tempfile):
        mock_machine.return_value = 'i686'
        iso = Iso('source-dir')
        assert iso.arch == 'ix86'

    @patch('builtins.open')
    @patch('kiwi.iso.Command.run')
    @patch('os.path.exists')
    @patch('os.walk')
    def test_init_iso_creation_parameters(
        self, mock_walk, mock_exists, mock_command, mock_open
    ):
        mock_walk.return_value = [
            ('source-dir', ('bar', 'baz'), ('efi', 'eggs', 'header_end'))
        ]
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock

        self.iso.init_iso_creation_parameters(['custom_arg'])

        assert self.file_mock.write.call_args_list == [
            call('7984fc91-a43f-4e45-bf27-6d3aa08b24cf\n'),
            call('source-dir/boot/x86_64/boot.catalog 3\n'),
            call('source-dir/boot/x86_64/loader/isolinux.bin 2\n'),
            call('source-dir/efi 1000001\n'),
            call('source-dir/eggs 1\n'),
            call('source-dir/header_end 1000000\n'),
            call('source-dir/bar 1\n'),
            call('source-dir/baz 1\n')
        ]
        assert self.iso.iso_parameters == [
            'custom_arg', '-R', '-J', '-f', '-pad', '-joliet-long',
            '-sort', 'sortfile', '-no-emul-boot', '-boot-load-size', '4',
            '-boot-info-table',
            '-hide', 'boot/x86_64/boot.catalog',
            '-hide-joliet', 'boot/x86_64/boot.catalog',
        ]
        assert self.iso.iso_loaders == [
            '-b', 'boot/x86_64/loader/isolinux.bin',
            '-c', 'boot/x86_64/boot.catalog'
        ]
        mock_command.assert_called_once_with(
            [
                'isolinux-config', '--base', 'boot/x86_64/loader',
                'source-dir/boot/x86_64/loader/isolinux.bin'
            ]
        )

    @patch('os.path.exists')
    def test_add_efi_loader_parameters(self, mock_exists):
        mock_exists.return_value = True
        self.iso.add_efi_loader_parameters()
        assert self.iso.iso_loaders == [
            '-eltorito-alt-boot', '-b', 'boot/x86_64/efi',
            '-no-emul-boot', '-joliet-long'
        ]

    def test_get_iso_creation_parameters(self):
        self.iso.iso_parameters = ['a']
        self.iso.iso_loaders = ['b']
        assert self.iso.get_iso_creation_parameters() == ['a', 'b']

    @raises(KiwiIsoToolError)
    @patch('os.path.exists')
    def test_isols_no_tool_found(self, mock_exists):
        mock_exists.return_value = False
        self.iso.isols('some-iso')

    @patch('os.path.exists')
    @patch('kiwi.iso.Command.run')
    @patch('builtins.open')
    def test_isols_usr_bin_isoinfo_used(
        self, mock_open, mock_command, mock_exists
    ):
        exists_results = [False, True]

        def side_effect(self):
            return exists_results.pop()

        mock_exists.side_effect = side_effect
        self.iso.isols('some-iso')
        mock_command.assert_called_once_with(
            ['/usr/bin/isoinfo', '-R', '-l', '-i', 'some-iso']
        )

    @patch('os.path.exists')
    @patch('kiwi.iso.Command.run')
    @patch('builtins.open')
    def test_isols_usr_lib_genisoimage_isoinfo_used(
        self, mock_open, mock_command, mock_exists
    ):
        exists_results = [True, False]

        def side_effect(self):
            return exists_results.pop()

        mock_exists.side_effect = side_effect
        self.iso.isols('some-iso')
        mock_command.assert_called_once_with(
            ['/usr/lib/genisoimage/isoinfo', '-R', '-l', '-i', 'some-iso']
        )

    @patch('kiwi.iso.Command.run')
    @patch('os.path.exists')
    def test_isols(self, mock_exists, mock_command):
        mock_exists.return_value = True
        output_type = namedtuple('output_type', ['output'])
        output_data = ''
        with open('../data/iso_listing.txt') as iso:
            output_data = iso.read()
        mock_command.return_value = output_type(output=output_data)
        result = self.iso.isols('some-iso')
        assert result[2158].name == 'header_end'

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

    @patch('kiwi.iso.Command.run')
    def test_create_hybrid(self, mock_command):
        mbrid = mock.Mock()
        mbrid.get_id = mock.Mock(
            return_value='0x0815'
        )
        Iso.create_hybrid(42, mbrid, 'some-iso')
        mock_command.assert_called_once_with(
            [
                'isohybrid', '--offset', '42',
                '--id', '0x0815', '--type', '0x83',
                '--uefi', 'some-iso'
            ]
        )

    @patch('builtins.open')
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_iso9660_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = b'bogus'
        Iso.fix_boot_catalog('isofile')

    @patch('builtins.open')
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_not_bootable(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = b'CD001'
        Iso.fix_boot_catalog('isofile')

    @patch('builtins.open')
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_path_table_sector_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        read_results = [b'EL TORITO SPECIFICATION', b'CD001']

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch('builtins.open')
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_catalog_sector_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            b'CD001' + b'_' * (0x08c - 0x5) + b'0x1d5f23a'
        read_results = [b'EL TORITO SPECIFICATION', volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch('builtins.open')
    @raises(KiwiIsoMetaDataError)
    def test_iso_metadata_catalog_invalid(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            b'CD001' + b'_' * (0x08c - 0x5) + b'0x1d5f23a'
        eltorito_descriptor = \
            b'EL TORITO SPECIFICATION' + b'_' * (0x47 - 0x17) + b'0x1d5f23a'
        read_results = [eltorito_descriptor, volume_descriptor]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect
        Iso.fix_boot_catalog('isofile')

    @patch('builtins.open')
    def test_relocate_boot_catalog(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            b'CD001' + b'_' * (0x08c - 0x5) + b'0x1d5f23a'
        eltorito_descriptor = \
            b'EL TORITO SPECIFICATION' + b'_' * (0x47 - 0x17) + b'0x1d5f23a'
        new_volume_descriptor = \
            b'bogus'
        next_new_volume_descriptor = \
            b'TEA01'
        new_boot_catalog = b'\x00' * 0x800
        read_results = [
            new_boot_catalog,
            next_new_volume_descriptor,
            new_volume_descriptor,
            b'catalog',
            eltorito_descriptor,
            volume_descriptor
        ]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect

        Iso.relocate_boot_catalog('isofile')
        assert self.file_mock.write.call_args_list == [
            call(b'catalog'),
            call(
                b'EL TORITO SPECIFICATION' +
                b'_' * (0x47 - 0x17) + b'\x13\x00\x00\x005f23a'
            )
        ]

    @patch('builtins.open')
    def test_fix_boot_catalog(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        volume_descriptor = \
            b'CD001' + b'_' * (0x08c - 0x5) + b'0x1d5f23a'
        eltorito_descriptor = \
            b'EL TORITO SPECIFICATION' + b'_' * (0x47 - 0x17) + b'0x1d5f23a'
        boot_catalog = b'_' * 64 + struct.pack('B', 0x88) + b'_' * 32
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
                    b'_' * 44 +
                    b'\x01Legacy (isolinux)\x00\x00\x91\xef\x00\x01' +
                    b'\x00' * 28 +
                    b'\x88___________\x01UEFI (grub)' +
                    b'\x00' * 8
                )
            ]
        else:
            assert self.file_mock.write.call_args_list == [
                call(
                    b'_' * 44 +
                    b'\x01Legacy (isolinux)\x00\x00\x91\xef\x01' +
                    b'\x00' * 29 +
                    b'\x88___________\x01UEFI (grub)' +
                    b'\x00' * 8
                )
            ]
