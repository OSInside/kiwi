from mock import patch

import mock

from kiwi.storage.subformat.vhd import DiskFormatVhd


class TestDiskFormatVhd(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.disk_format = DiskFormatVhd(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value'})
        assert self.disk_format.options == ['-o', 'option=value']

    @patch('kiwi.storage.subformat.vhd.Command.run')
    def test_create_image_format(self, mock_command):
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-f', 'raw',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '-O', 'vpc',
                'target_dir/some-disk-image.x86_64-1.2.3.vhd'
            ]
        )
