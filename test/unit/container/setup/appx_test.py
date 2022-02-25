import io
from pytest import raises
from mock import (
    patch, MagicMock
)

from kiwi.container.setup.appx import ContainerSetupAppx
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiContainerSetupError


class TestContainerSetupAppx:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.appx = ContainerSetupAppx(
            'root_dir', {
                'metadata_path': '../data/appx',
                'image_version': '1.99.1',
                'history': {
                    'created_by': 'SUSE',
                    'author': 'Marcus',
                    'application_id': '123',
                    'package_version': '2003.12.0.0',
                    'comment': 'Some Information',
                    'launcher': 'openSUSE-Tumbleweed.exe'
                }
            }
        )

    def test_setup_raises_no_manifest_file(self):
        with patch('os.path.exists', return_value=True):
            appx = ContainerSetupAppx(
                'root_dir', {'metadata_path': 'artificial'}
            )
            with patch('os.path.exists', return_value=False):
                with raises(KiwiContainerSetupError):
                    appx.setup()

    @patch('lxml.etree.parse')
    def test_setup_raises_xml_operations(self, mock_parse):
        mock_parse.side_effect = Exception
        with raises(KiwiContainerSetupError):
            self.appx.setup()

    def test_setup(self):
        Defaults.set_platform_name('x86_64')
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.appx.setup()
            # we expect all @..@ templates to got replaced
            assert '@' not in file_handle.write.call_args_list
