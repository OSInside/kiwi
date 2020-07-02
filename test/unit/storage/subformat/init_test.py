from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.storage.subformat import DiskFormat

from kiwi.exceptions import KiwiDiskFormatSetupError


class TestDiskFormat:
    def setup(self):
        self.xml_state = Mock()
        self.xml_state.get_build_type_format_options.return_value = {}

    def test_format_not_implemented(self):
        with raises(KiwiDiskFormatSetupError):
            DiskFormat('foo', self.xml_state, 'root_dir', 'target_dir')

    def test_disk_format_vagrant_not_implemented(self):
        self.xml_state.get_build_type_vagrant_config_section = Mock(
            return_value=None
        )
        with raises(KiwiDiskFormatSetupError):
            DiskFormat(
                'vagrant', self.xml_state, 'root_dir', 'target_dir'
            )

    @patch('kiwi.storage.subformat.DiskFormatQcow2')
    def test_disk_format_qcow2(self, mock_qcow2):
        DiskFormat('qcow2', self.xml_state, 'root_dir', 'target_dir')
        mock_qcow2.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {}
        )

    @patch('kiwi.storage.subformat.DiskFormatVdi')
    def test_disk_format_vdi(self, mock_vdi):
        DiskFormat('vdi', self.xml_state, 'root_dir', 'target_dir')
        mock_vdi.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {}
        )

    @patch('kiwi.storage.subformat.DiskFormatVhd')
    def test_disk_format_vhd(self, mock_vhd):
        DiskFormat('vhd', self.xml_state, 'root_dir', 'target_dir')
        mock_vhd.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {}
        )

    @patch('kiwi.storage.subformat.DiskFormatVhdx')
    def test_disk_format_vhdx(self, mock_vhdx):
        DiskFormat('vhdx', self.xml_state, 'root_dir', 'target_dir')
        mock_vhdx.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {}
        )

    @patch('kiwi.storage.subformat.DiskFormatVhdFixed')
    def test_disk_format_vhdfixed(self, mock_vhdfixed):
        self.xml_state.build_type.get_vhdfixedtag = Mock(
            return_value='disk-tag'
        )
        DiskFormat('vhd-fixed', self.xml_state, 'root_dir', 'target_dir')
        mock_vhdfixed.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {'--tag': 'disk-tag'}
        )

    @patch('kiwi.storage.subformat.DiskFormatGce')
    def test_disk_format_gce(self, mock_gce):
        self.xml_state.build_type.get_gcelicense = Mock(
            return_value='gce_license_tag'
        )
        DiskFormat('gce', self.xml_state, 'root_dir', 'target_dir')
        mock_gce.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir',
            {'--tag': 'gce_license_tag'}
        )

    @patch('kiwi.storage.subformat.DiskFormatVmdk')
    def test_disk_format_vmdk(self, mock_vmdk):
        vmdisk = Mock()
        vmdisk.get_controller = Mock(
            return_value='controller'
        )
        vmdisk.get_diskmode = Mock(
            return_value='disk-mode'
        )
        self.xml_state.get_build_type_vmdisk_section = Mock(
            return_value=vmdisk
        )
        DiskFormat('vmdk', self.xml_state, 'root_dir', 'target_dir')
        mock_vmdk.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir',
            {'adapter_type=controller': None, 'subformat=disk-mode': None}
        )

    @patch('kiwi.storage.subformat.DiskFormatOva')
    def test_disk_format_ova(self, mock_ova):
        vmdisk = Mock()
        vmdisk.get_controller = Mock(
            return_value='controller'
        )
        vmdisk.get_diskmode = Mock(
            return_value='disk-mode'
        )
        self.xml_state.get_build_type_vmdisk_section = Mock(
            return_value=vmdisk
        )
        DiskFormat('ova', self.xml_state, 'root_dir', 'target_dir')
        mock_ova.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir',
            {'adapter_type=controller': None, 'subformat=disk-mode': None}
        )

    @patch('kiwi.storage.subformat.DiskFormatVagrantVirtualBox')
    @patch('kiwi.storage.subformat.DiskFormatVagrantLibVirt')
    def test_disk_format_vagrant_libvirt(
        self, mock_vagrant_libvirt, mock_vagrant_virt_box
    ):
        for provider_name, provider_mock in (
                ('libvirt', mock_vagrant_libvirt),
                ('virtualbox', mock_vagrant_virt_box)
        ):
            vagrant_config = Mock()
            vagrant_config.get_provider = Mock(
                return_value=provider_name
            )
            self.xml_state.get_build_type_vagrant_config_section = Mock(
                return_value=vagrant_config
            )
            DiskFormat(
                'vagrant', self.xml_state, 'root_dir', 'target_dir'
            )
            provider_mock.assert_called_once_with(
                self.xml_state, 'root_dir', 'target_dir',
                {'vagrantconfig': vagrant_config}
            )

    @patch('kiwi.storage.subformat.DiskFormatBase')
    def test_disk_format_base(self, mock_base):
        DiskFormat('raw', self.xml_state, 'root_dir', 'target_dir')
        mock_base.assert_called_once_with(
            self.xml_state, 'root_dir', 'target_dir', {}
        )
