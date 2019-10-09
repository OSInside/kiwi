from mock import (
    patch, call, mock_open
)
from pytest import raises
from collections import namedtuple

from kiwi.iso_tools.cdrtools import IsoToolsCdrTools

from kiwi.exceptions import KiwiIsoToolError


class TestIsoToolsCdrTools:
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
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

    @patch('os.path.exists')
    def test_get_tool_name_raises(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiIsoToolError):
            self.iso_tool.get_tool_name()

    @patch('os.walk')
    @patch('kiwi.iso_tools.cdrtools.NamedTemporaryFile')
    def test_init_iso_creation_parameters(
        self, mock_tempfile, mock_walk
    ):
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_tempfile.return_value = temp_type(
            name='sortfile'
        )
        mock_walk_results = [
            [('source-dir', ('EFI',), ())],
            [('source-dir', ('bar', 'baz'), ('eggs', 'efi'))],
            [('source-dir', ('EFI',), ())],
            [('source-dir', ('bar', 'baz'), ('eggs', 'efi'))]
        ]

        def side_effect(arg):
            return mock_walk_results.pop()

        mock_walk.side_effect = side_effect
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.iso_tool.init_iso_creation_parameters(
                {
                    'mbr_id': 'app_id',
                    'publisher': 'org',
                    'preparer': 'name',
                    'volume_id': 'vol_id',
                    'udf': True
                }
            )
        assert m_open.return_value.write.call_args_list == [
            call('source-dir/boot/x86_64/boot.catalog 3\n'),
            call('source-dir/boot/x86_64/loader/isolinux.bin 2\n'),
            call('source-dir/EFI 1\n'),
            call('source-dir/bar 1\n'),
            call('source-dir/baz 1\n'),
            call('source-dir/efi 1000001\n'),
            call('source-dir/eggs 1\n'),
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

        self.iso_tool.iso_loaders = []
        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.iso_tool.init_iso_creation_parameters(
                {
                    'efi_mode': 'uefi',
                    'mbr_id': 'app_id',
                    'publisher': 'org',
                    'preparer': 'name',
                    'volume_id': 'vol_id',
                    'udf': True
                }
            )
        assert self.iso_tool.iso_loaders == [
            '-b', 'boot/x86_64/loader/eltorito.img',
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
    @patch('kiwi.iso_tools.cdrtools.Path.which')
    def test_create_iso(self, mock_Path_which, mock_command):
        self.iso_tool.create_iso('myiso', hidden_files=['hide_me'])
        mock_command.assert_called_once_with(
            [
                mock_Path_which.return_value,
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

    @patch('os.path.exists')
    def test_list_iso_no_tool_found(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiIsoToolError):
            self.iso_tool.list_iso('some-iso')

    def test_has_iso_hybrid_capability(self):
        assert self.iso_tool.has_iso_hybrid_capability() is False
