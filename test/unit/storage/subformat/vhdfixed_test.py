import sys
from builtins import bytes
from unittest.mock import (
    call, patch, Mock, mock_open
)
from pytest import raises

import kiwi

from kiwi.defaults import Defaults
from kiwi.storage.subformat.vhdfixed import DiskFormatVhdFixed

from kiwi.exceptions import KiwiVhdTagError


class TestDiskFormatVhdFixed:
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
        self.xml_state.get_luks_credentials = Mock(
            return_value=None
        )
        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = True
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.disk_format = DiskFormatVhdFixed(
            self.xml_state, 'root_dir', 'target_dir', {'force_size': None}
        )

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value', '--tag': 'tag'})
        assert self.disk_format.options == [
            '-o', 'option=value', '-o', 'subformat=fixed'
        ]
        assert self.disk_format.tag == 'tag'

    @patch('kiwi.storage.subformat.vhdfixed.Command.run')
    def test_create_image_format_invalid_tag(self, mock_command):
        self.disk_format.tag = 'invalid'
        with raises(KiwiVhdTagError):
            self.disk_format.create_image_format()

    @patch('kiwi.storage.subformat.vhdfixed.Command.run')
    def test_create_image_format(self, mock_command):
        self.disk_format.tag = '12345678-1234-1234-1234-123456789999'

        m_open = mock_open(read_data='dev_zero_data')
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        mock_command.assert_called_once_with(
            [
                'qemu-img', 'convert', '-f', 'raw',
                'target_dir/some-disk-image.x86_64-1.2.3.raw', '-O', 'vpc',
                '-o', 'force_size', '-o', 'subformat=fixed',
                'target_dir/some-disk-image.x86_64-1.2.3.vhdfixed'
            ]
        )
        assert m_open.call_args_list == [
            call('target_dir/some-disk-image.x86_64-1.2.3.vhdfixed', 'r+b'),
            call('/dev/zero', 'rb'),
            call('target_dir/some-disk-image.x86_64-1.2.3.vhdfixed', 'r+b')
        ]
        assert m_open.return_value.write.call_args_list[0] == call(
            'dev_zero_data'
        )
        if sys.byteorder == 'little':
            # on little endian machines
            assert m_open.return_value.write.call_args_list[1] == call(
                bytes(b'xV4\x124\x124\x12\x124\x124Vx\x99\x99')
            )
        else:
            # on big endian machines
            assert m_open.return_value.write.call_args_list[1] == call(
                bytes(b'\x124Vx\x124\x124\x124\x124Vx\x99\x99')
            )
        assert m_open.return_value.seek.call_args_list == [
            call(65536, 0), call(0, 2),
            call(65536, 0), call(0, 2)
        ]

    def test_store_to_result_default(self):
        result = Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=True,
            filename='target_dir/some-disk-image.x86_64-1.2.3.vhdfixed',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )

    def test_store_to_result_with_luks(self):
        result = Mock()
        self.xml_state.get_luks_credentials = Mock(return_value='foo')
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-1.2.3.vhdfixed',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )
        self.xml_state.get_luks_credentials = Mock(return_value=None)
