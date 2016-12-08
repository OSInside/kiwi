from mock import call, patch
import mock

from .test_helper import patch_open, raises

from kiwi.exceptions import KiwiFormatSetupError
from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt

from textwrap import dedent


class TestDiskFormatVagrantLibVirt(object):
    def setup(self):
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.vagrantconfig = mock.Mock()
        self.vagrantconfig.get_virtualsize = mock.Mock(
            return_value=42
        )
        self.disk_format = DiskFormatVagrantLibVirt(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )

    @raises(KiwiFormatSetupError)
    def test_post_init_missing_custom_arguments(self):
        self.disk_format.post_init(custom_args=None)

    @raises(KiwiFormatSetupError)
    def test_post_init_missing_vagrantconfig(self):
        self.disk_format.post_init({'vagrantconfig': None})

    @patch('kiwi.storage.subformat.vagrant_libvirt.Command.run')
    @patch('kiwi.storage.subformat.vagrant_libvirt.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_libvirt.DiskFormatQcow2')
    @patch('kiwi.storage.subformat.vagrant_libvirt.random.randrange')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_rand, mock_qcow, mock_mkdtemp, mock_command
    ):
        mock_rand.return_value = 0xa
        mock_mkdtemp.return_value = 'tmpdir'
        qcow = mock.Mock()
        qcow.image_format = 'qcow2'
        mock_qcow.return_value = qcow
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        metadata_json = dedent('''
            {
              "format": "qcow2",
              "provider": "libvirt",
              "virtual_size": "42"
            }
        ''').strip()
        vagrantfile = dedent('''
            Vagrant::Config.run do |config|
              config.vm.base_mac = "00163E0A0A0A"
            end
            include_vagrantfile = File.expand_path(
              "../include/_Vagrantfile", __FILE__
            )
            load include_vagrantfile if File.exist?(include_vagrantfile)
        ''').strip()

        self.disk_format.create_image_format()

        qcow.create_image_format.assert_called_once_with()

        assert file_mock.write.call_args_list == [
            call(metadata_json), call(vagrantfile)
        ]

        assert mock_command.call_args_list == [
            call([
                'mv', 'target_dir/some-disk-image.x86_64-1.2.3.qcow2',
                'tmpdir/box.img'
            ]),
            call([
                'tar', '-C', 'tmpdir', '-czf',
                'target_dir/some-disk-image.x86_64-1.2.3.vagrant.libvirt.box',
                'box.img', 'metadata.json', 'Vagrantfile'
            ])
        ]
