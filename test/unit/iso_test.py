from nose.tools import *
from mock import patch
from mock import call
import mock

import nose_helper

from kiwi.exceptions import *

from kiwi.iso import Iso
from collections import namedtuple


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
        self.iso = Iso('source-dir')

    @patch('__builtin__.open')
    @patch('os.path.exists')
    @raises(KiwiIsoLoaderError)
    def test_init_iso_creation_parameters_no_loader(
        self, mock_exists, mock_open
    ):
        mock_exists.return_value = False
        self.iso.init_iso_creation_parameters()

    @patch('__builtin__.open')
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
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.iso.init_iso_creation_parameters(['custom_arg'])

        assert file_mock.write.call_args_list == [
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

    def test_add_iso_header_end_marker(self):
        # TODO
        self.iso.add_iso_header_end_marker()

    def test_relocate_boot_catalog(self):
        # TODO
        self.iso.relocate_boot_catalog('isofile')

    def test_fix_boot_catalog(self):
        # TODO
        self.iso.fix_boot_catalog('isofile')
