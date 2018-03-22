from mock import patch, call
from collections import namedtuple
from .test_helper import raises

from kiwi.iso_tools.cdrtools import IsoToolsCdrTools
from kiwi.exceptions import KiwiIsoToolError


class TestIsoToolsCdrTools(object):
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

    @raises(KiwiIsoToolError)
    @patch('os.path.exists')
    def test_get_tool_name_raises(self, mock_exists):
        mock_exists.return_value = False
        self.iso_tool.get_tool_name()

    def test_init_iso_creation_parameters(self):
        self.iso_tool.init_iso_creation_parameters('sortfile', ['custom_arg'])
        assert self.iso_tool.iso_parameters == [
            'custom_arg', '-R', '-J', '-f', '-pad', '-joliet-long',
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
