from mock import patch, call
import mock
from collections import namedtuple
from .test_helper import raises, patch_open

from kiwi.iso_tools.cdrtools import IsoToolsCdrTools
from kiwi.exceptions import KiwiIsoToolError


class TestIsoToolsCdrTools(object):
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

        self.iso_tool = IsoToolsCdrTools('source-dir')

    @patch('kiwi.iso_tools.cdrtools.Path.which')
    def test_get_tool_name(self, mock_which):
        path_search_return_values = ['tool_found', None]

        def path_search(tool):
            return path_search_return_values.pop()

        mock_which.side_effect = path_search
        assert self.iso_tool.get_tool_name() == 'tool_found'
        assert mock_which.call_args_list == [
            call('mkisofs'), call('genisoimage')
        ]

    @raises(KiwiIsoToolError)
    @patch('os.path.exists')
    def test_get_tool_name_raises(self, mock_exists):
        mock_exists.return_value = False
        self.iso_tool.get_tool_name()

    @patch_open
    @patch('os.walk')
    @patch('kiwi.iso_tools.cdrtools.NamedTemporaryFile')
    def test_init_iso_creation_parameters(
        self, mock_tempfile, mock_walk, mock_open
    ):
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_tempfile.return_value = temp_type(
            name='sortfile'
        )
        mock_walk_results = [
            [('source-dir', ('EFI',), ())],
            [('source-dir', ('bar', 'baz'), ('efi', 'eggs'))]
        ]

        def side_effect(arg):
            return mock_walk_results.pop()

        mock_walk.side_effect = side_effect
        mock_open.return_value = self.context_manager_mock
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'publisher': 'org',
                'preparer': 'name',
                'volume_id': 'vol_id',
                'udf': True
            }
        )
        assert self.file_mock.write.call_args_list == [
            call('source-dir/boot/x86_64/boot.catalog 3\n'),
            call('source-dir/boot/x86_64/loader/isolinux.bin 2\n'),
            call('source-dir/efi 1000001\n'),
            call('source-dir/eggs 1\n'),
            call('source-dir/bar 1\n'),
            call('source-dir/baz 1\n'),
            call('source-dir/EFI 1\n'),
            call('source-dir/header_end 1000000\n')
        ]
        assert self.iso_tool.iso_parameters == [
            '-A', 'app_id', '-publisher', 'org', '-p', 'name', '-V', 'vol_id',
            '-iso-level', '3', '-udf',
            '-R', '-J', '-f', '-pad', '-joliet-long',
            '-sort', 'sortfile', '-no-emul-boot', '-boot-load-size', '4',
            '-boot-info-table',
            '-hide', 'boot/x86_64/boot.catalog',
            '-hide-joliet', 'boot/x86_64/boot.catalog',
        ]
        assert self.iso_tool.iso_loaders == [
            '-b', 'boot/x86_64/loader/isolinux.bin',
            '-c', 'boot/x86_64/boot.catalog'
        ]

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.iso_tools.cdrtools.CommandCapabilities.has_option_in_help')
    def test_add_efi_loader_parameters(
        self, mock_has_option_in_help, mock_getsize, mock_exists
    ):
        mock_has_option_in_help.return_value = True
        mock_getsize.return_value = 4096
        mock_exists.return_value = True
        self.iso_tool.add_efi_loader_parameters()
        assert self.iso_tool.iso_loaders == [
            '-eltorito-alt-boot', '-eltorito-platform', 'efi',
            '-b', 'boot/x86_64/efi',
            '-no-emul-boot', '-joliet-long',
            '-boot-load-size', '8'
        ]

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('kiwi.iso_tools.cdrtools.CommandCapabilities.has_option_in_help')
    def test_add_efi_loader_parameters_big_loader(
        self, mock_has_option_in_help, mock_getsize, mock_exists
    ):
        mock_has_option_in_help.return_value = False
        mock_getsize.return_value = 33554432
        mock_exists.return_value = True
        self.iso_tool.add_efi_loader_parameters()
        assert self.iso_tool.iso_loaders == [
            '-eltorito-alt-boot', '-b', 'boot/x86_64/efi',
            '-no-emul-boot', '-joliet-long'
        ]

    @patch('kiwi.iso_tools.cdrtools.Command.run')
    def test_create_iso(self, mock_command):
        self.iso_tool.create_iso('myiso', hidden_files=['hide_me'])
        mock_command.assert_called_once_with(
            [
                '/usr/bin/mkisofs',
                '-hide', 'hide_me', '-hide-joliet', 'hide_me',
                '-o', 'myiso', 'source-dir'
            ]
        )

    @patch('kiwi.iso_tools.cdrtools.Command.run')
    @patch('os.path.exists')
    def test_list_iso(self, mock_exists, mock_command):
        mock_exists.return_value = True
        output_type = namedtuple('output_type', ['output'])
        output_data = ''
        with open('../data/iso_listing.txt') as iso:
            output_data = iso.read()
        mock_command.return_value = output_type(output=output_data)
        result = self.iso_tool.list_iso('some-iso')
        assert result[2158].name == 'header_end'

    @raises(KiwiIsoToolError)
    @patch('os.path.exists')
    def test_list_iso_no_tool_found(self, mock_exists):
        mock_exists.return_value = False
        self.iso_tool.list_iso('some-iso')

    def test_has_iso_hybrid_capability(self):
        assert self.iso_tool.has_iso_hybrid_capability() is False
