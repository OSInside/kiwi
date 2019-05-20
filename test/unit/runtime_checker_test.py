from mock import patch
import mock
from .test_helper import raises

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.runtime_checker import RuntimeChecker
from kiwi.exceptions import KiwiRuntimeError


class TestRuntimeChecker(object):
    def setup(self):
        self.description = XMLDescription(
            '../data/example_runtime_checker_config.xml'
        )
        self.xml_state = XMLState(
            self.description.load()
        )
        self.runtime_checker = RuntimeChecker(self.xml_state)

    @raises(KiwiRuntimeError)
    def test_check_image_include_repos_publicly_resolvable(self):
        self.runtime_checker.check_image_include_repos_publicly_resolvable()

    @raises(KiwiRuntimeError)
    def test_invalid_target_dir_pointing_to_shared_cache_1(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache//kiwi/foo'
        )

    @raises(KiwiRuntimeError)
    def test_invalid_target_dir_pointing_to_shared_cache_2(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache/kiwi'
        )

    @raises(KiwiRuntimeError)
    @patch('os.getcwd')
    def test_invalid_target_dir_pointing_to_shared_cache_3(self, mock_getcwd):
        mock_getcwd.return_value = '/'
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            'var/cache/kiwi'
        )

    @raises(KiwiRuntimeError)
    def test_invalid_target_dir_pointing_to_shared_cache_4(self):
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            '//var/cache//kiwi/foo'
        )

    def test_valid_target_dir_1(self):
        assert self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache/kiwi-fast-tmpsystemdir'
        ) is None

    def test_valid_target_dir_2(self):
        assert self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/foo/bar'
        ) is None

    @raises(KiwiRuntimeError)
    def test_check_repositories_configured(self):
        self.xml_state.delete_repository_sections()
        self.runtime_checker.check_repositories_configured()

    @raises(KiwiRuntimeError)
    def test_check_volume_setup_defines_multiple_fullsize_volumes(self):
        self.runtime_checker.\
            check_volume_setup_defines_multiple_fullsize_volumes()

    @raises(KiwiRuntimeError)
    def test_check_volume_setup_has_no_root_definition(self):
        self.runtime_checker.check_volume_setup_has_no_root_definition()

    @patch('kiwi.runtime_checker.Path.which')
    @raises(KiwiRuntimeError)
    def test_check_container_tool_chain_installed(self, mock_which):
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.RuntimeConfig.get_oci_archive_tool')
    @patch('kiwi.runtime_checker.Path.which')
    @raises(KiwiRuntimeError)
    def test_check_container_tool_chain_installed_unknown_tool(
        self, mock_which, mock_oci_tool
    ):
        mock_oci_tool.return_value = 'budah'
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.RuntimeConfig.get_oci_archive_tool')
    @patch('kiwi.runtime_checker.Path.which')
    @raises(KiwiRuntimeError)
    def test_check_container_tool_chain_installed_buildah(
        self, mock_which, mock_oci_tool
    ):
        mock_oci_tool.return_value = 'buildah'
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.Path.which')
    @patch('kiwi.runtime_checker.CommandCapabilities.check_version')
    @raises(KiwiRuntimeError)
    def test_check_container_tool_chain_installed_with_version(
        self, mock_cmdver, mock_which
    ):
        mock_which.return_value = True
        mock_cmdver.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.Path.which')
    @patch('kiwi.runtime_checker.CommandCapabilities.check_version')
    @patch('kiwi.runtime_checker.CommandCapabilities.has_option_in_help')
    @raises(KiwiRuntimeError)
    def test_check_container_tool_chain_installed_with_multitags(
        self, mock_cmdoptions, mock_cmdver, mock_which
    ):
        mock_which.return_value = True
        mock_cmdver.return_value = True
        mock_cmdoptions.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_container_tool_chain_installed()

    @raises(KiwiRuntimeError)
    @patch('platform.machine')
    @patch('kiwi.runtime_checker.Defaults.get_boot_image_description_path')
    def test_check_consistent_kernel_in_boot_and_system_image(
        self, mock_boot_path, mock_machine
    ):
        mock_boot_path.return_value = '../data'
        mock_machine.return_value = 'x86_64'
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_consistent_kernel_in_boot_and_system_image()

    @raises(KiwiRuntimeError)
    def test_check_boot_description_exists_no_boot_ref(self):
        description = XMLDescription(
            '../data/example_runtime_checker_no_boot_reference.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_boot_description_exists()

    @raises(KiwiRuntimeError)
    def test_check_boot_description_exists_does_not_exist(self):
        description = XMLDescription(
            '../data/example_runtime_checker_boot_desc_not_found.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_boot_description_exists()

    @raises(KiwiRuntimeError)
    def test_check_xen_uniquely_setup_as_server_or_guest_for_ec2(self):
        self.xml_state.build_type.get_firmware = mock.Mock(
            return_value='ec2'
        )
        self.xml_state.is_xen_server = mock.Mock(
            return_value=True
        )
        self.xml_state.is_xen_guest = mock.Mock(
            return_value=True
        )
        self.runtime_checker.check_xen_uniquely_setup_as_server_or_guest()

    @raises(KiwiRuntimeError)
    def test_check_xen_uniquely_setup_as_server_or_guest_for_xen(self):
        self.xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        self.xml_state.is_xen_server = mock.Mock(
            return_value=True
        )
        self.xml_state.is_xen_guest = mock.Mock(
            return_value=True
        )
        self.runtime_checker.check_xen_uniquely_setup_as_server_or_guest()

    @raises(KiwiRuntimeError)
    def test_check_dracut_module_for_disk_overlay_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        xml_state.build_type.get_overlayroot = mock.Mock(
            return_value=True
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_dracut_module_for_disk_overlay_in_package_list()

    @raises(KiwiRuntimeError)
    def test_check_efi_mode_for_disk_overlay_correctly_setup(self):
        self.xml_state.build_type.get_overlayroot = mock.Mock(
            return_value=True
        )
        self.xml_state.build_type.get_firmware = mock.Mock(
            return_value='uefi'
        )
        self.runtime_checker.check_efi_mode_for_disk_overlay_correctly_setup()

    @raises(KiwiRuntimeError)
    @patch('kiwi.runtime_checker.Path.which')
    def test_check_mediacheck_installed_tagmedia_missing(self, mock_which):
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_mediacheck_installed()

    @raises(KiwiRuntimeError)
    def test_check_dracut_module_for_live_iso_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_dracut_module_for_live_iso_in_package_list()

    @raises(KiwiRuntimeError)
    def test_check_dracut_module_for_disk_oem_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_dracut_module_for_disk_oem_in_package_list()

    @raises(KiwiRuntimeError)
    def test_check_dracut_module_for_oem_install_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_dracut_module_for_oem_install_in_package_list()

    @raises(KiwiRuntimeError)
    def test_check_volume_label_used_with_lvm(self):
        self.runtime_checker.check_volume_label_used_with_lvm()

    @raises(KiwiRuntimeError)
    def test_check_preferences_data_no_version(self):
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_minimal_required_preferences()

    @raises(KiwiRuntimeError)
    def test_check_preferences_data_no_packagemanager(self):
        xml_state = XMLState(
            self.description.load(), ['xenFlavour'], 'vmx'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_minimal_required_preferences()
