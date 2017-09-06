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
    def test_check_volume_setup_has_no_root_definition(self):
        self.runtime_checker.check_volume_setup_has_no_root_definition()

    @patch('kiwi.runtime_checker.Path.which')
    @raises(KiwiRuntimeError)
    def test_check_docker_tool_chain_installed(self, mock_which):
        mock_which.return_value = False
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_docker_tool_chain_installed()

    @patch('kiwi.runtime_checker.Path.which')
    @patch('kiwi.runtime_checker.Command.run')
    @raises(KiwiRuntimeError)
    def test_check_docker_tool_chain_installed_with_version(
        self, mock_command, mock_which
    ):
        tool_version_call = mock.Mock()
        tool_version_call.output = 'umoci version 2.2.3'
        mock_which.return_value = True
        mock_command.return_value = tool_version_call
        xml_state = XMLState(
            self.description.load(), ['docker'], 'docker'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_docker_tool_chain_installed()

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
    @patch('platform.machine')
    def test_check_mediacheck_only_for_x86_arch(
        self, mock_machine
    ):
        mock_machine.return_value = 'aarch64'
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_mediacheck_only_for_x86_arch()

    @raises(KiwiRuntimeError)
    def test_check_dracut_module_for_live_iso_in_package_list(self):
        xml_state = XMLState(
            self.description.load(), ['vmxFlavour'], 'iso'
        )
        runtime_checker = RuntimeChecker(xml_state)
        runtime_checker.check_dracut_module_for_live_iso_in_package_list()
