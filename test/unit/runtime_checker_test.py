import sys
from mock import (
    patch, Mock
)
from pytest import raises

from .test_helper import argv_kiwi_tests

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.runtime_checker import RuntimeChecker
from kiwi.exceptions import KiwiRuntimeError


class TestRuntimeChecker:
    def setup(self):
        self.description = XMLDescription(
            '../data/example_runtime_checker_config.xml'
        )
        self.xml_state = XMLState(
            self.description.load()
        )
        self.runtime_checker = RuntimeChecker(self.xml_state)

    def test_check_image_include_repos_publicly_resolvable(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_image_include_repos_publicly_resolvable()

    def test_invalid_target_dir_pointing_to_shared_cache_1(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_target_directory_not_in_shared_cache(
                '/var/cache//kiwi/foo'
            )

    def test_invalid_target_dir_pointing_to_shared_cache_2(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_target_directory_not_in_shared_cache(
                '/var/cache/kiwi'
            )

    @patch('os.getcwd')
    def test_invalid_target_dir_pointing_to_shared_cache_3(self, mock_getcwd):
        mock_getcwd.return_value = '/'
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_target_directory_not_in_shared_cache(
                'var/cache/kiwi'
            )

    def test_invalid_target_dir_pointing_to_shared_cache_4(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_target_directory_not_in_shared_cache(
                '//var/cache//kiwi/foo'
            )

    @patch('os.path.isdir')
    def test_check_dracut_module_versions_compatible_to_kiwi_no_dracut(
        self, mock_os_path_isdir
    ):
        mock_os_path_isdir.return_value = False
        self.runtime_checker.\
            check_dracut_module_versions_compatible_to_kiwi('root_dir')
        # does not raise if no dracut is installed

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('kiwi.runtime_checker.Command.run')
    def test_check_dracut_module_versions_compatible_to_kiwi(
        self, mock_Command_run, mock_os_path_isdir, mock_os_listdir
    ):
        mock_os_path_isdir.return_value = True
        command = Mock()
        command.output = '1.2.3-1.2'
        mock_Command_run.return_value = command
        mock_os_listdir.return_value = ['90kiwi-dump']
        package_manager = Mock()
        package_manager.return_value = 'zypper'
        self.xml_state.get_package_manager = package_manager
        with raises(KiwiRuntimeError) as exception_data:
            self.runtime_checker.\
                check_dracut_module_versions_compatible_to_kiwi('root_dir')
        assert "'dracut-kiwi-oem-dump': 'got:1.2.3, need:>=9.20.1'" in str(
            exception_data.value
        )
        mock_Command_run.assert_called_once_with(
            [
                'rpm', '--root', 'root_dir', '-q',
                '--qf', '%{VERSION}', 'dracut-kiwi-oem-dump'
            ]
        )
        package_manager.return_value = 'apt-get'
        mock_Command_run.reset_mock()
        with raises(KiwiRuntimeError) as exception_data:
            self.runtime_checker.\
                check_dracut_module_versions_compatible_to_kiwi('root_dir')
        assert "'dracut-kiwi-oem-dump': 'got:1.2.3, need:>=9.20.1'" in str(
            exception_data.value
        )
        mock_Command_run.assert_called_once_with(
            [
                'dpkg-query', '--admindir', 'root_dir/var/lib/dpkg',
                '-W', '-f', '${Version}', 'dracut-kiwi-oem-dump'
            ]
        )

    def test_valid_target_dir_1(self):
        assert self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/var/cache/kiwi-fast-tmpsystemdir'
        ) is None

    def test_valid_target_dir_2(self):
        assert self.runtime_checker.check_target_directory_not_in_shared_cache(
            '/foo/bar'
        ) is None

    def test_check_repositories_configured(self):
        self.xml_state.delete_repository_sections()
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_repositories_configured()

    def test_check_volume_setup_defines_reserved_labels(self):
        xml_state = XMLState(
            self.description.load(), ['vmxSimpleFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_volume_setup_defines_reserved_labels()

    def test_appx_invalid_name(self):
        xml_state = XMLState(
            self.description.load(), ['wsl_launcher'], 'appx'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_appx_naming_conventions_valid()

    def test_appx_invalid_id(self):
        xml_state = XMLState(
            self.description.load(), ['wsl_id'], 'appx'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_appx_naming_conventions_valid()

    def test_check_volume_setup_defines_multiple_fullsize_volumes(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.\
                check_volume_setup_defines_multiple_fullsize_volumes()

    def test_check_volume_setup_has_no_root_definition(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_volume_setup_has_no_root_definition()

    @patch('kiwi.runtime_checker.Path.which')
    def test_check_container_tool_chain_installed(self, mock_which):
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.RuntimeConfig.get_oci_archive_tool')
    @patch('kiwi.runtime_checker.Path.which')
    def test_check_container_tool_chain_installed_unknown_tool(
        self, mock_which, mock_oci_tool
    ):
        mock_oci_tool.return_value = 'budah'
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.RuntimeConfig.get_oci_archive_tool')
    @patch('kiwi.runtime_checker.Path.which')
    def test_check_container_tool_chain_installed_buildah(
        self, mock_which, mock_oci_tool
    ):
        mock_oci_tool.return_value = 'buildah'
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.Path.which')
    @patch('kiwi.runtime_checker.CommandCapabilities.check_version')
    def test_check_container_tool_chain_installed_with_version(
        self, mock_cmdver, mock_which
    ):
        mock_which.return_value = True
        mock_cmdver.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_container_tool_chain_installed()

    @patch('kiwi.runtime_checker.Path.which')
    @patch('kiwi.runtime_checker.CommandCapabilities.check_version')
    @patch('kiwi.runtime_checker.CommandCapabilities.has_option_in_help')
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
        with raises(KiwiRuntimeError):
            runtime_checker.check_container_tool_chain_installed()

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
        with raises(KiwiRuntimeError):
            runtime_checker.check_consistent_kernel_in_boot_and_system_image()

    def test_check_initrd_selection_required(self):
        description = XMLDescription(
            '../data/example_runtime_checker_no_initrd_system_reference.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_initrd_selection_required()

    def test_check_boot_description_exists_no_boot_ref(self):
        description = XMLDescription(
            '../data/example_runtime_checker_no_boot_reference.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_boot_description_exists()

    def test_check_boot_description_exists_does_not_exist(self):
        description = XMLDescription(
            '../data/example_runtime_checker_boot_desc_not_found.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_boot_description_exists()

    def test_check_xen_uniquely_setup_as_server_or_guest_for_ec2(self):
        self.xml_state.build_type.get_firmware = Mock(
            return_value='ec2'
        )
        self.xml_state.is_xen_server = Mock(
            return_value=True
        )
        self.xml_state.is_xen_guest = Mock(
            return_value=True
        )
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_xen_uniquely_setup_as_server_or_guest()

    def test_check_xen_uniquely_setup_as_server_or_guest_for_xen(self):
        self.xml_state.build_type.get_firmware = Mock(
            return_value=None
        )
        self.xml_state.is_xen_server = Mock(
            return_value=True
        )
        self.xml_state.is_xen_guest = Mock(
            return_value=True
        )
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_xen_uniquely_setup_as_server_or_guest()

    def test_check_dracut_module_for_disk_overlay_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        xml_state.build_type.get_overlayroot = Mock(
            return_value=True
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.\
                check_dracut_module_for_disk_overlay_in_package_list()

    def test_check_efi_mode_for_disk_overlay_correctly_setup(self):
        self.xml_state.build_type.get_overlayroot = Mock(
            return_value=True
        )
        self.xml_state.build_type.get_firmware = Mock(
            return_value='uefi'
        )
        with raises(KiwiRuntimeError):
            self.runtime_checker.\
                check_efi_mode_for_disk_overlay_correctly_setup()

    @patch('kiwi.runtime_checker.Path.which')
    def test_check_mediacheck_installed_tagmedia_missing(self, mock_which):
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_mediacheck_installed()

    def test_check_dracut_module_for_live_iso_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_dracut_module_for_live_iso_in_package_list()

    def test_check_dracut_module_for_disk_oem_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_dracut_module_for_disk_oem_in_package_list()

    def test_check_dracut_module_for_oem_install_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.\
                check_dracut_module_for_oem_install_in_package_list()

    def test_check_volume_label_used_with_lvm(self):
        with raises(KiwiRuntimeError):
            self.runtime_checker.check_volume_label_used_with_lvm()

    def test_check_swap_name_used_with_lvm(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_swap_name_used_with_lvm()

    def test_check_preferences_data_no_version(self):
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_image_version_provided()

    @patch('platform.machine')
    def test_check_architecture_supports_iso_firmware_setup(
        self, mock_machine
    ):
        mock_machine.return_value = 'aarch64'
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_architecture_supports_iso_firmware_setup()
        xml_state = XMLState(
            self.description.load(), ['xenDom0Flavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_architecture_supports_iso_firmware_setup()

    @patch('platform.machine')
    @patch('kiwi.runtime_checker.Path.which')
    def test_check_syslinux_installed_if_isolinux_is_used(
        self, mock_Path_which, mock_machine
    ):
        mock_Path_which.return_value = None
        mock_machine.return_value = 'x86_64'
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_syslinux_installed_if_isolinux_is_used()
        xml_state = XMLState(
            self.description.load(), ['xenDom0Flavour'], 'oem'
        )
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_syslinux_installed_if_isolinux_is_used()

    def test_check_image_type_unique(self):
        description = XMLDescription(
            '../data/example_runtime_checker_conflicting_types.xml'
        )
        xml_state = XMLState(description.load())
        runtime_checker = RuntimeChecker(xml_state)
        with raises(KiwiRuntimeError):
            runtime_checker.check_image_type_unique()

    def teardown(self):
        sys.argv = argv_kiwi_tests
