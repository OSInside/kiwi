
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.storage.subformat import DiskFormat


class TestDiskFormat(object):
    @raises(KiwiDiskFormatSetupError)
    def test_format_not_implemented(self):
        DiskFormat('foo', mock.Mock(), 'root_dir', 'target_dir')

    @patch('kiwi.storage.subformat.DiskFormatQcow2')
    def test_disk_format_qcow2(self, mock_qcow2):
        xml_state = mock.Mock()
        DiskFormat('qcow2', xml_state, 'root_dir', 'target_dir')
        mock_qcow2.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir'
        )

    @patch('kiwi.storage.subformat.DiskFormatVdi')
    def test_disk_format_vdi(self, mock_vdi):
        xml_state = mock.Mock()
        DiskFormat('vdi', xml_state, 'root_dir', 'target_dir')
        mock_vdi.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir'
        )

    @patch('kiwi.storage.subformat.DiskFormatVhd')
    def test_disk_format_vhd(self, mock_vhd):
        xml_state = mock.Mock()
        DiskFormat('vhd', xml_state, 'root_dir', 'target_dir')
        mock_vhd.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir'
        )

    @patch('kiwi.storage.subformat.DiskFormatVhdFixed')
    def test_disk_format_vhdfixed(self, mock_vhdfixed):
        xml_state = mock.Mock()
        xml_state.build_type.get_vhdfixedtag = mock.Mock(
            return_value='disk-tag'
        )
        DiskFormat('vhdfixed', xml_state, 'root_dir', 'target_dir')
        mock_vhdfixed.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir', {'--tag': 'disk-tag'}
        )

    @patch('kiwi.storage.subformat.DiskFormatGce')
    def test_disk_format_gce(self, mock_gce):
        xml_state = mock.Mock()
        xml_state.build_type.get_gcelicense = mock.Mock(
            return_value='gce_license_tag'
        )
        DiskFormat('gce', xml_state, 'root_dir', 'target_dir')
        mock_gce.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir', {'--tag': 'gce_license_tag'}
        )

    @patch('kiwi.storage.subformat.DiskFormatVmdk')
    def test_disk_format_vmdk(self, mock_vmdk):
        xml_state = mock.Mock()
        vmdisk = mock.Mock()
        vmdisk.get_controller = mock.Mock(
            return_value='controller'
        )
        vmdisk.get_diskmode = mock.Mock(
            return_value='disk-mode'
        )
        xml_state.get_build_type_vmdisk_section = mock.Mock(
            return_value=vmdisk
        )
        DiskFormat('vmdk', xml_state, 'root_dir', 'target_dir')
        mock_vmdk.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir',
            {'adapter_type=controller': None, 'subformat=disk-mode': None}
        )

    @patch('kiwi.storage.subformat.DiskFormatBase')
    def test_disk_format_base(self, mock_base):
        xml_state = mock.Mock()
        DiskFormat('raw', xml_state, 'root_dir', 'target_dir')
        mock_base.assert_called_once_with(
            xml_state, 'root_dir', 'target_dir',
        )
