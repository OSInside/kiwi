from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiFormatSetupError,
    KiwiResizeRawDiskError
)

from kiwi.storage.subformat.base import DiskFormatBase


class TestDiskFormatBase(object):
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
        self.disk_format = DiskFormatBase(
            self.xml_state, 'root_dir', 'target_dir'
        )

    @raises(NotImplementedError)
    def test_create_image_format(self):
        self.disk_format.create_image_format()

    @raises(KiwiFormatSetupError)
    def test_get_target_file_path_for_format_invalid_format(self):
        self.disk_format.get_target_file_path_for_format('foo')

    def test_post_init(self):
        self.disk_format.post_init({'option': 'unhandled'})
        assert self.disk_format.custom_args == {}

    def test_get_qemu_option_list(self):
        custom_args = {
            'subformat=format': None,
            'adapter_type=type': None
        }
        assert self.disk_format.get_qemu_option_list(custom_args) == [
            '-o', 'adapter_type=type', '-o', 'subformat=format'
        ]

    def test_get_target_file_path_for_format(self):
        assert self.disk_format.get_target_file_path_for_format('vhd') == \
            'target_dir/some-disk-image.x86_64-1.2.3.vhd'

    def test_store_to_result(self):
        result = mock.Mock()
        self.disk_format.image_format = 'qcow2'
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-1.2.3.qcow2',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )

    @raises(KiwiResizeRawDiskError)
    @patch('os.path.getsize')
    def test_resize_raw_disk_raises_on_shrink_disk(self, mock_getsize):
        mock_getsize.return_value = 42
        self.disk_format.resize_raw_disk(10)

    @patch('os.path.getsize')
    @patch('kiwi.storage.subformat.base.Command.run')
    def test_resize_raw_disk(self, mock_command, mock_getsize):
        mock_getsize.return_value = 42
        assert self.disk_format.resize_raw_disk(1024) is True
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'resize',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '1024'
            ]
        )

    @patch('os.path.getsize')
    @patch('kiwi.storage.subformat.base.Command.run')
    def test_resize_raw_disk_append(self, mock_command, mock_getsize):
        mock_getsize.return_value = 42
        assert self.disk_format.resize_raw_disk(1024, append=True) is True
        mock_command.assert_called_once_with(
            [
                'qemu-img', 'resize',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '+1024'
            ]
        )

    @patch('os.path.getsize')
    def test_resize_raw_disk_same_size(self, mock_getsize):
        mock_getsize.return_value = 42
        assert self.disk_format.resize_raw_disk(42) is False

    @patch('os.path.exists')
    def test_has_raw_disk(self, mock_exists):
        mock_exists.return_value = True
        assert self.disk_format.has_raw_disk() is True
        mock_exists.assert_called_once_with(
            'target_dir/some-disk-image.x86_64-1.2.3.raw'
        )

    @patch('kiwi.storage.subformat.base.Path.wipe')
    @patch('os.path.exists')
    def test_destructor(self, mock_exists, mock_wipe):
        mock_exists.return_value = True
        self.disk_format.temp_image_dir = 'tmpdir'
        self.disk_format.__del__()
        self.disk_format.temp_image_dir = None
        mock_wipe.assert_called_once_with('tmpdir')
