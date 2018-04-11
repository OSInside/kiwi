from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiCommandNotFound,
    KiwiFormatSetupError
)

from kiwi.storage.subformat.ova import DiskFormatOva


class TestDiskFormatOva(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        mock_machine.return_value = 'x86_64'
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        xml_data.get_displayname = mock.Mock(
            return_value=None
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )

        self.machine_setup = mock.Mock()
        self.xml_state.get_build_type_machine_section = mock.Mock(
            return_value=self.machine_setup
        )
        self.machine_setup.get_HWversion = mock.Mock(
            return_value='42'
        )
        self.machine_setup.get_guestOS = mock.Mock(
            return_value='suse'
        )
        self.machine_setup.get_memory = mock.Mock(
            return_value='4096'
        )
        self.machine_setup.get_ncpus = mock.Mock(
            return_value='2'
        )

        self.machine_setup.get_ovftype = mock.Mock(
            return_value='vmware'
        )

        self.disk_format = DiskFormatOva(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({})

    @raises(KiwiFormatSetupError)
    def test_post_init_bad_ovftype(self):
        self.machine_setup.get_ovftype.return_value = 'foobar'
        self.disk_format.post_init({})

    def test_store_to_result(self):
        result = mock.Mock()
        self.disk_format.store_to_result(result)
        assert result.add.call_args_list == [
            call(
                compress=False,
                filename='target_dir/some-disk-image.x86_64-1.2.3.ova',
                key='disk_format_image',
                shasum=True,
                use_for_bundle=True
            )
        ]

    @patch('kiwi.storage.subformat.ova.Path.which')
    @patch('kiwi.storage.subformat.ova.Command.run')
    @patch('kiwi.storage.subformat.vmdk.DiskFormatVmdk.create_image_format')
    @patch('kiwi.storage.subformat.ova.CommandCapabilities.has_option_in_help')
    @patch('os.stat')
    @patch('os.chmod')
    def test_create_image_format(
        self, mock_chmod, mock_stat, mock_has_option_in_help,
        mock_create_image_format, mock_command, mock_which
    ):
        mock_has_option_in_help.return_value = True
        mock_which.return_value = 'ovftool'
        mock_stat.return_value = mock.Mock(st_mode=0o644)
        self.disk_format.create_image_format()
        mock_command.assert_called_once_with(
            [
                'ovftool', '--shaAlgorithm=SHA1',
                'target_dir/some-disk-image.x86_64-1.2.3.vmx',
                'target_dir/some-disk-image.x86_64-1.2.3.ova'
            ]
        )

    @patch('kiwi.storage.subformat.ova.Path.which')
    @raises(KiwiCommandNotFound)
    def test_create_image_format_no_ovftool(self, mock_which):
        mock_which.return_value = None
        self.disk_format.create_image_format()
