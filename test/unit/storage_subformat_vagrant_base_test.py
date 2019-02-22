import io
from pytest import raises
from mock import call, patch
from mock import (
    Mock, MagicMock
)

from .test_helper import patch_open

from kiwi.exceptions import KiwiFormatSetupError
from kiwi.storage.subformat.vagrant_base import DiskFormatVagrantBase

from textwrap import dedent


class TestDiskFormatVagrantBase(object):
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
        self.disk_format = DiskFormatVagrantBase(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )
        assert self.disk_format.image_format is None
        assert self.disk_format.provider is None

    def test_create_box_img_not_implemented(self):
        with raises(NotImplementedError):
            self.disk_format.create_box_img('arbitrary')

    def test_post_init_missing_custom_arguments(self):
        with raises(KiwiFormatSetupError):
            self.disk_format.post_init(custom_args=None)

    def test_post_init_missing_vagrantconfig(self):
        with raises(KiwiFormatSetupError):
            self.disk_format.post_init({'vagrantconfig': None})

    def test_create_image_format_missing_provider_setup(self):
        with raises(NotImplementedError):
            self.disk_format.create_image_format()

    def test_store_to_result_missing_provider_setup(self):
        with raises(NotImplementedError):
            self.disk_format.store_to_result(Mock())

    @patch('kiwi.storage.subformat.vagrant_base.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_base.random.randrange')
    @patch.object(DiskFormatVagrantBase, 'create_box_img')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_create_box_img, mock_rand,
        mock_mkdtemp, mock_command
    ):
        # select an example provider
        self.disk_format.image_format = 'vagrant.libvirt.box'
        self.disk_format.provider = 'libvirt'

        metadata_json = dedent('''
            {
              "provider": "libvirt"
            }
        ''').strip()

        expected_vagrantfile = dedent('''
            Vagrant.configure("2") do |config|
              config.vm.base_mac = "00163E0A0A0A"
            end
        ''').strip()

        mock_rand.return_value = 0xa
        mock_mkdtemp.return_value = 'tmpdir'

        mock_open.return_value = MagicMock(spec=io.IOBase)
        file_handle = mock_open.return_value.__enter__.return_value

        self.disk_format.create_image_format()

        assert mock_open.call_args_list == [
            call('tmpdir/metadata.json', 'w'),
            call('tmpdir/Vagrantfile', 'w')
        ]
        assert file_handle.write.call_args_list == [
            call(metadata_json), call(expected_vagrantfile)
        ]
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'tmpdir', '-czf',
                'target_dir/some-disk-image.x86_64-1.2.3.vagrant.libvirt.box',
                'metadata.json', 'Vagrantfile'
            ]
        )

    def test_get_additional_vagrant_config_settings(self):
        assert self.disk_format.get_additional_vagrant_config_settings() is None

    def test_store_to_result(self):
        # select an example provider
        self.disk_format.image_format = 'vagrant.libvirt.box'
        result = Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/'
            'some-disk-image.x86_64-1.2.3.vagrant.libvirt.box',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )
