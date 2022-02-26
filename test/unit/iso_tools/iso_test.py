from mock import (
    call, patch
)
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.iso_tools.iso import Iso

from kiwi.exceptions import KiwiIsoLoaderError


class TestIso:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso = Iso('source-dir')

    def setup_method(self, cls):
        self.setup()

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

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_set_media_tag(self, mock_command):
        Iso.set_media_tag('foo')
        mock_command.assert_called_once_with(
            ['tagmedia', '--md5', '--check', '--pad', '150', 'foo']
        )
