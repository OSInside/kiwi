from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.disk_format_vhd import DiskFormatVhd


class TestDiskFormatVhd(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.disk_format = DiskFormatVhd(
            self.xml_state, 'source_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init(['some-option'])
        assert self.disk_format.custom_args == ['-o', 'some-option']

    @patch('kiwi.disk_format_vhd.Command.run')
    def test_create_image_format(self, mock_command):
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-c', '-f', 'raw',
                'target_dir/some-disk-image.raw', '-O', 'vpc',
                'target_dir/some-disk-image.vhd'
            ]
        )
