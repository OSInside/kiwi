from mock import (
    call, patch, Mock, MagicMock, mock_open
)

from textwrap import dedent
from collections import namedtuple

from kiwi.storage.subformat.vagrant_virtualbox import (
    DiskFormatVagrantVirtualBox
)
from kiwi.defaults import Defaults


class TestDiskFormatVagrantVirtualBox:
    def setup(self):
        with open("../data/vagrant_virtualbox.ovf", "r") as ovf_file:
            self.Leap_15_ovf = ovf_file.read(-1)

        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        self.xml_state = Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_root_filesystem_uuid = Mock(
            return_value='some-uuid'
        )
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.vagrantconfig = Mock()
        self.vagrantconfig.get_virtualsize = Mock(
            return_value=42
        )
        self.vagrantconfig.get_embedded_vagrantfile = Mock(
            return_value=None
        )
        self.disk_format = DiskFormatVagrantVirtualBox(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )

    @patch('kiwi.storage.subformat.vagrant_virtualbox.Command.run')
    @patch('kiwi.storage.subformat.vagrant_virtualbox.DiskFormatVmdk')
    def test_create_box_img(self, mock_vmdk, mock_command):
        vmdk = Mock()
        vmdk.image_format = 'vmdk'
        mock_vmdk.return_value = vmdk

        # override the box settings to match those from the extracted ovf file
        self.xml_state.xml_data.name = "OpenSUSE-Leap-15.0"
        self.xml_state.get_description_section = MagicMock()
        self.xml_state.get_description_section.return_value = \
            namedtuple(
                'description_type', ['author', 'contact', 'specification']
            )(
                author="not relevant",
                contact="not relevant",
                specification="OpenSUSE Leap 15.0"
            )

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            assert self.disk_format.create_box_img('tmpdir') == [
                'tmpdir/box.vmdk', 'tmpdir/box.ovf'
            ]
        vmdk.create_image_format.assert_called_once_with()
        mock_command.assert_called_once_with(
            [
                'mv', 'target_dir/some-disk-image.x86_64-1.2.3.vmdk',
                'tmpdir/box.vmdk'
            ]
        )
        m_open.assert_called_once_with('tmpdir/box.ovf', 'w')

        assert m_open.return_value.write.call_args_list[0] == call(self.Leap_15_ovf)

    @patch('kiwi.storage.subformat.vagrant_virtualbox.random.randrange')
    def test_get_additional_vagrant_config_settings(self, mock_rand):
        self.xml_state.get_vagrant_config_virtualbox_guest_additions \
            .return_value = None

        expected_res = dedent('''
            config.vm.base_mac = "00163E010101"
            config.vm.synced_folder ".", "/vagrant", type: "rsync"
        ''').strip()
        assert self.disk_format.get_additional_vagrant_config_settings() == \
            expected_res

    @patch('kiwi.storage.subformat.vagrant_base.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_virtualbox.random.randrange')
    @patch.object(DiskFormatVagrantVirtualBox, 'create_box_img')
    def test_create_image_format_with_and_without_guest_additions(
        self, mock_create_box_img, mock_rand,
        mock_mkdtemp, mock_command
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        mock_create_box_img.return_value = ['arbitrary']

        # without guest additions
        self.xml_state.get_vagrant_config_virtualbox_guest_additions \
            .return_value = \
            Defaults.get_vagrant_config_virtualbox_guest_additions()

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        vagrantfile = dedent('''
            Vagrant.configure("2") do |config|
              config.vm.base_mac = "00163E010101"
              config.vm.synced_folder ".", "/vagrant", type: "rsync"
            end
        ''').strip()
        assert m_open.return_value.write.call_args_list[1] == call(vagrantfile)

        # without guest additions
        self.xml_state.get_vagrant_config_virtualbox_guest_additions \
            .return_value = True
        vagrantfile = dedent('''
            Vagrant.configure("2") do |config|
              config.vm.base_mac = "00163E010101"
            end
        ''').strip()

        m_open.reset_mock()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        assert m_open.return_value.write.call_args_list[1] == call(vagrantfile)
