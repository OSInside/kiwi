from textwrap import dedent
from mock import (
    patch, Mock, call, mock_open
)

from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt


class TestDiskFormatVagrantLibVirt:
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
        self.vagrantconfig.get_embedded_vagrantfile = Mock(
            return_value=None
        )
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
            'format': 'qcow2', 'virtual_size': 42
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
    @patch.object(DiskFormatVagrantLibVirt, 'create_box_img')
    def test_create_image_format(
        self, mock_create_box_img, mock_mkdtemp, mock_command
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        mock_create_box_img.return_value = ['arbitrary']

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        assert m_open.return_value.write.call_args_list[1] == call(
            dedent('''
                Vagrant.configure("2") do |config|
                  config.vm.synced_folder ".", "/vagrant", type: "rsync"
                  config.vm.provider :libvirt do |libvirt|
                    libvirt.driver = "kvm"
                  end
                end
            ''').strip()
        )
