import io
from pytest import raises
from unittest.mock import (
    call, patch, mock_open
)
from unittest.mock import (
    Mock, MagicMock
)

import kiwi

from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiFormatSetupError
from kiwi.storage.subformat.vagrant_base import DiskFormatVagrantBase

from textwrap import dedent


class TestDiskFormatVagrantBase:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        xml_data.description_dir = './'
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
        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = False
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.disk_format = DiskFormatVagrantBase(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )
        assert self.disk_format.image_format == ''
        assert self.disk_format.provider is None

    def setup_method(self, cls):
        self.setup()

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
    @patch('kiwi.storage.subformat.vagrant_base.Temporary')
    @patch.object(DiskFormatVagrantBase, 'create_box_img')
    def test_create_image_format(
        self, mock_create_box_img, mock_Temporary, mock_command
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
            end
        ''').strip()

        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'

        with patch('builtins.open', create=True) as mock_file:
            mock_file.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_file.return_value.__enter__.return_value

            self.disk_format.create_image_format()

            assert mock_file.call_args_list == [
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

    @patch('kiwi.storage.subformat.vagrant_base.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.Temporary')
    @patch.object(DiskFormatVagrantBase, 'create_box_img')
    def test_user_provided_vagrantfile(
        self, mock_create_box_img, mock_Temporary, mock_cmd_run
    ):
        # select an example provider
        self.disk_format.image_format = 'vagrant.virtualbox.box'
        self.disk_format.provider = 'virtualbox'

        # deterministic tempdir:
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'

        self.vagrantconfig.get_embedded_vagrantfile = Mock(
            return_value='example_Vagrantfile'
        )

        expected_vagrantfile = r"it's something"

        with patch(
            'builtins.open', mock_open(read_data=expected_vagrantfile)
        ) as mock_file:
            self.disk_format.create_image_format()
            file_handle = mock_file.return_value.__enter__.return_value

            assert mock_file.call_args_list == [
                call('tmpdir/metadata.json', 'w'),
                call('tmpdir/Vagrantfile', 'w'),
                call('./example_Vagrantfile', 'r')
            ]
            assert file_handle.write.call_args_list[1] == call(
                expected_vagrantfile
            )

    def test_get_additional_vagrant_config_settings(self):
        assert self.disk_format.get_additional_vagrant_config_settings() == ''

    def test_get_additional_metadata(self):
        assert self.disk_format.get_additional_metadata() == {}

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
