from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.storage.subformat.ova import DiskFormatOva

import kiwi

from kiwi.exceptions import (
    KiwiCommandNotFound,
    KiwiFormatSetupError,
    KiwiTemplateError
)


class TestDiskFormatOva:
    @patch('kiwi.storage.subformat.ova.FirmWare')
    def setup(self, mock_FirmWare):
        self.firmware = Mock()
        self.firmware.efi_mode = Mock(
            return_value='uefi'
        )
        mock_FirmWare.return_value = self.firmware
        Defaults.set_platform_name('x86_64')
        self.context_manager_mock = Mock()
        self.file_mock = Mock()
        self.enter_mock = Mock()
        self.exit_mock = Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        xml_data.get_displayname = Mock(
            return_value=None
        )
        self.xml_state = Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )

        self.machine_setup = Mock()
        self.xml_state.get_build_type_machine_section = Mock(
            return_value=self.machine_setup
        )
        self.machine_setup.get_HWversion = Mock(
            return_value='42'
        )
        self.machine_setup.get_guestOS = Mock(
            return_value='suse'
        )
        self.machine_setup.get_memory = Mock(
            return_value='4096'
        )
        self.machine_setup.get_ncpus = Mock(
            return_value='2'
        )

        self.iso_setup = Mock()
        self.xml_state.get_build_type_vmdvd_section = Mock(
            return_value=self.iso_setup
        )
        self.xml_state.get_luks_credentials = Mock(
            return_value=None
        )
        self.iso_setup.get_controller = Mock(
            return_value='ide'
        )
        self.iso_setup.get_id = Mock(
            return_value='0'
        )

        self.network_setup = [Mock()]
        self.xml_state.get_build_type_vmnic_entries = Mock(
            return_value=self.network_setup
        )
        self.network_setup[0].get_interface = Mock(
            return_value='0'
        )
        self.network_setup[0].get_mac = Mock(
            return_value='98:90:96:a0:3c:58'
        )
        self.network_setup[0].get_mode = Mock(
            return_value='bridged'
        )
        self.network_setup[0].get_driver = Mock(
            return_value='e1000'
        )

        self.disk_setup = Mock()
        self.xml_state.get_build_type_vmdisk_section = Mock(
            return_value=self.disk_setup
        )
        self.disk_setup.get_controller = Mock(
            return_value='lsilogic'
        )
        self.disk_setup.get_id = Mock(
            return_value='0'
        )

        self.machine_setup.get_ovftype = Mock(
            return_value='vmware'
        )

        self.runtime_config = Mock()
        self.runtime_config.get_bundle_compression.return_value = False
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )

        self.disk_format = DiskFormatOva(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.storage.subformat.ova.FirmWare')
    def test_post_init(self, mock_FirmWare):
        self.disk_format.post_init({})

    def test_post_init_bad_ovftype(self):
        self.machine_setup.get_ovftype.return_value = 'foobar'
        with raises(KiwiFormatSetupError):
            self.disk_format.post_init({})

    def test_store_to_result(self):
        result = Mock()
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
    @patch('kiwi.storage.subformat.ova.DiskFormatVmdk.create_image_format')
    @patch('os.chdir')
    def test_create_image_format(
        self,
        mock_chdir,
        mock_create_image_format,
        mock_command,
        mock_which
    ):
        mock_which.return_value = 'ova-compose'
        with patch('builtins.open', create=True) as mock_open:
            self.disk_format.create_image_format()
            mock_open.assert_called_once_with(
                'target_dir/some-disk-image.x86_64-1.2.3.meta', 'w'
            )
            mock_command.assert_called_once_with(
                [
                    'ova-compose',
                    '--input-file',
                    'target_dir/some-disk-image.x86_64-1.2.3.meta',
                    '--output-file',
                    'target_dir/some-disk-image.x86_64-1.2.3.ova',
                    '--format', 'ova'
                ]
            )

    @patch('kiwi.storage.subformat.ova.DiskFormatVmdk.create_image_format')
    @patch('kiwi.storage.subformat.ova.OvaComposeTemplate.get_template')
    @patch('kiwi.storage.subformat.ova.Command.run')
    @patch('kiwi.storage.subformat.ova.Path.which')
    def test_create_image_format_template_error(
        self,
        mock_Path_which,
        mock_Command_run,
        mock_OvaComposeTemplate_get_template,
        mock_DiskFormatVmdk_create_image_format
    ):
        template = Mock()
        mock_Path_which.return_value = 'ova-compose'
        mock_OvaComposeTemplate_get_template.return_value = template
        template.substitute.side_effect = Exception
        with patch('builtins.open'):
            with raises(KiwiTemplateError):
                self.disk_format.create_image_format()

    @patch('kiwi.storage.subformat.ova.Path.which')
    def test_create_image_format_no_ova_compose(self, mock_Path_which):
        mock_Path_which.return_value = None
        with raises(KiwiCommandNotFound):
            self.disk_format.create_image_format()

    @patch('kiwi.storage.subformat.ova.OvaComposeTemplate.get_template')
    def test_create_ova_compose_meta_file_with_disk_controller(self, mock_get_template):
        """Test that disk controller and disk id are passed to OvaComposeTemplate"""
        self.disk_setup.get_controller.return_value = 'lsilogic'
        self.disk_setup.get_id.return_value = '7'
        template = Mock()
        mock_get_template.return_value = template
        template.substitute.return_value = 'meta_content'

        with patch('builtins.open', create=True):
            self.disk_format._create_ova_compose_meta_file()
            # Verify OvaComposeTemplate.get_template was called with disk setup
            mock_get_template.assert_called_once()
            call_args = mock_get_template.call_args
            assert call_args[1]['disk_controller'] == 'lsilogic'
            assert call_args[1]['disk_id'] == '7'

    @patch('kiwi.storage.subformat.ova.OvaComposeTemplate.get_template')
    def test_create_ova_compose_meta_file_with_nic_driver(self, mock_get_template):
        """Test that NIC settings are passed to OvaComposeTemplate"""
        self.network_setup[0].get_driver.return_value = 'e1000'
        self.network_setup[0].get_interface.return_value = '2'
        self.network_setup[0].get_mode.return_value = 'bridged'
        self.network_setup[0].get_mac.return_value = '00:11:22:33:44:55'
        template = Mock()
        mock_get_template.return_value = template
        template.substitute.return_value = 'meta_content'

        with patch('builtins.open', create=True):
            self.disk_format._create_ova_compose_meta_file()
            # Verify OvaComposeTemplate.get_template was called with network setup
            mock_get_template.assert_called_once()
            call_args = mock_get_template.call_args
            assert call_args[0][2] == {
                '2': {
                    'driver': 'e1000',
                    'connection_type': 'bridged',
                    'mac': '00:11:22:33:44:55'
                }
            }

    @patch('kiwi.storage.subformat.ova.OvaComposeTemplate.get_template')
    def test_create_ova_compose_meta_file_with_no_controllers(self, mock_get_template):
        """Test that defaults are used when no optional setup is configured"""
        self.disk_setup.get_controller.return_value = None
        self.disk_setup.get_id.return_value = None
        self.iso_setup.get_controller.return_value = None
        self.iso_setup.get_id.return_value = None
        self.network_setup = []
        self.xml_state.get_build_type_vmnic_entries.return_value = self.network_setup
        template = Mock()
        mock_get_template.return_value = template
        template.substitute.return_value = 'meta_content'

        with patch('builtins.open', create=True):
            self.disk_format._create_ova_compose_meta_file()
            # Verify OvaComposeTemplate.get_template was called with defaults
            mock_get_template.assert_called_once()
            call_args = mock_get_template.call_args
            assert call_args[1]['disk_controller'] is None
            assert call_args[1]['disk_id'] == '0'
            assert call_args[1]['iso_controller'] == 'ide'
            assert call_args[1]['iso_id'] == '0'
            assert call_args[0][2] == {}

    @patch('kiwi.storage.subformat.ova.OvaComposeTemplate.get_template')
    def test_create_ova_compose_meta_file_memory_cpu_extraction(self, mock_get_template):
        """Test that memory and CPU configuration are correctly extracted"""
        self.machine_setup.get_memory.return_value = '8192'
        self.machine_setup.get_ncpus.return_value = '4'
        self.machine_setup.get_guestOS.return_value = 'ubuntu64Guest'
        template = Mock()
        mock_get_template.return_value = template
        template.substitute.return_value = 'meta_content'

        with patch('builtins.open', create=True) as mock_open:
            self.disk_format._create_ova_compose_meta_file()
            # Verify template.substitute was called with correct values
            template.substitute.assert_called_once()
            call_args = template.substitute.call_args[0][0]
            assert call_args['memory_size'] == '8192'
            assert call_args['number_of_cpus'] == '4'
            assert call_args['guest_os'] == 'ubuntu64Guest'
            # Verify meta file was opened for writing
            mock_open.assert_called_once()
