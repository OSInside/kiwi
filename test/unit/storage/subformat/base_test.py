from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.storage.subformat.base import DiskFormatBase

import kiwi

from kiwi.exceptions import (
    KiwiFormatSetupError,
    KiwiResizeRawDiskError
)


class TestDiskFormatBase:
    @patch('kiwi.storage.subformat.base.DiskFormatBase.post_init')
    def setup(self, mock_post_init):
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
        self.xml_state.get_luks_credentials = Mock(
            return_value=None
        )
        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = True
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        DiskFormatBase(
            self.xml_state, 'root_dir', 'target_dir', {'option': 'unhandled'}
        )
        mock_post_init.assert_called_once_with({'option': 'unhandled'})
        mock_post_init.reset_mock()
        self.disk_format = DiskFormatBase(
            self.xml_state, 'root_dir', 'target_dir'
        )
        mock_post_init.assert_called_once_with({})

    @patch('kiwi.storage.subformat.base.DiskFormatBase.post_init')
    def setup_method(self, cls, mock_post_init):
        self.setup()

    def test_create_image_format(self):
        with raises(NotImplementedError):
            self.disk_format.create_image_format()

    def test_get_target_file_path_for_format_invalid_format(self):
        with raises(KiwiFormatSetupError):
            self.disk_format.get_target_file_path_for_format('foo')

    def test_post_init(self):
        # in the base class this method just pass
        self.disk_format.post_init({})

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

    def test_store_to_result_default(self):
        result = Mock()
        self.disk_format.image_format = 'qcow2'
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=True,
            filename='target_dir/some-disk-image.x86_64-1.2.3.qcow2',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )

    def test_store_to_result_with_luks(self):
        result = Mock()
        self.xml_state.get_luks_credentials = Mock(return_value='foo')
        self.disk_format.image_format = 'qcow2'
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-1.2.3.qcow2',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )
        self.xml_state.get_luks_credentials = Mock(return_value=None)

    @patch('os.path.getsize')
    def test_resize_raw_disk_raises_on_shrink_disk(self, mock_getsize):
        mock_getsize.return_value = 42
        with raises(KiwiResizeRawDiskError):
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
    def test_context_manager_exit(self, mock_exists, mock_wipe):
        mock_exists.return_value = True
        with DiskFormatBase(
            self.xml_state, 'root_dir', 'target_dir'
        ) as disk_format:
            disk_format.temp_image_dir = 'tmpdir'
        mock_wipe.assert_called_once_with('tmpdir')
