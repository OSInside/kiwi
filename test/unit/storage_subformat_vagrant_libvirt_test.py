import io
from textwrap import dedent
from mock import (
    patch, Mock, MagicMock, call
)

from .test_helper import patch_open

from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt


class TestDiskFormatVagrantLibVirt(object):
    def setup(self):
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        self.xml_state = Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.vagrantconfig = Mock()
        self.vagrantconfig.get_virtualsize = Mock(
            return_value=42
        )
        self.disk_format = DiskFormatVagrantLibVirt(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )
        assert self.disk_format.image_format == 'vagrant.libvirt.box'
        assert self.disk_format.provider == 'libvirt'

    @patch('kiwi.storage.subformat.vagrant_libvirt.Command.run')
    @patch('kiwi.storage.subformat.vagrant_libvirt.DiskFormatQcow2')
    def test_create_box_img(
        self, mock_qcow, mock_command
    ):
        qcow = Mock()
        qcow.image_format = 'qcow2'
        mock_qcow.return_value = qcow
        assert self.disk_format.create_box_img('tmpdir') == [
            'tmpdir/box.img'
        ]
        qcow.create_image_format.assert_called_once_with()
        mock_command.assert_called_once_with(
            [
                'mv', 'target_dir/some-disk-image.x86_64-1.2.3.qcow2',
                'tmpdir/box.img'
            ]
        )

    def test_get_additional_metadata(self):
        assert self.disk_format.get_additional_metadata() == {
            'format': 'qcow2', 'virtual_size': '42'
        }

    def test_get_additional_vagrant_config_settings(self):
        assert self.disk_format.get_additional_vagrant_config_settings() == \
            dedent('''
                config.vm.synced_folder ".", "/vagrant", type: "rsync"
                config.vm.provider :libvirt do |libvirt|
                  libvirt.driver = "kvm"
                end
            ''').strip()

    @patch('kiwi.storage.subformat.vagrant_base.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_base.random.randrange')
    @patch.object(DiskFormatVagrantLibVirt, 'create_box_img')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_create_box_img, mock_rand,
        mock_mkdtemp, mock_command
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        mock_create_box_img.return_value = ['arbitrary']
        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value
        self.disk_format.create_image_format()
        assert file_handle.write.call_args_list[1] == call(
            dedent('''
                Vagrant.configure("2") do |config|
                  config.vm.base_mac = "00163E010101"
                  config.vm.synced_folder ".", "/vagrant", type: "rsync"
                  config.vm.provider :libvirt do |libvirt|
                    libvirt.driver = "kvm"
                  end
                end
            ''').strip()
        )
