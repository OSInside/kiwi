from mock import (
    patch, Mock
)

import kiwi

from kiwi.defaults import Defaults
from kiwi.storage.subformat.vhdx import DiskFormatVhdx


class TestDiskFormatVhdx:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        self.xml_state = Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = False
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.disk_format = DiskFormatVhdx(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value'})
        assert self.disk_format.options == [
            '-o', 'option=value', '-o', 'subformat=dynamic'
        ]

    @patch('kiwi.storage.subformat.vhdx.Command.run')
    def test_create_image_format(self, mock_command):
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-f', 'raw',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '-O', 'vhdx',
                '-o', 'subformat=dynamic',
                'target_dir/some-disk-image.x86_64-1.2.3.vhdx'
            ]
        )
