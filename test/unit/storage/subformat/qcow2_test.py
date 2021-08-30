from mock import (
    patch, Mock, call
)

import kiwi

from kiwi.defaults import Defaults
from kiwi.storage.subformat.qcow2 import DiskFormatQcow2


class TestDiskFormatQcow2:
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
        self.disk_format = DiskFormatQcow2(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value'})
        assert self.disk_format.options == ['-o', 'option=value']

    @patch('kiwi.storage.subformat.qcow2.Command.run')
    @patch('kiwi.storage.subformat.qcow2.Temporary.new_file')
    def test_create_image_format(self, mock_Temporary_new_file, mock_command):
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_Temporary_new_file.return_value = tmpfile
        self.disk_format.create_image_format()
        assert mock_command.call_args_list == [
            call(
                [
                    'qemu-img', 'convert', '-f', 'raw',
                    'target_dir/some-disk-image.x86_64-1.2.3.raw',
                    '-O', 'qcow2',
                    'tmpfile'
                ]
            ),
            call(
                [
                    'qemu-img', 'convert', '-c', '-f', 'qcow2',
                    'tmpfile',
                    '-O', 'qcow2',
                    'target_dir/some-disk-image.x86_64-1.2.3.qcow2'
                ]
            )
        ]

    def test_store_to_result(self):
        result = Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-1.2.3.qcow2',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )
