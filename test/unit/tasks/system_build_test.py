import logging
import sys
import mock
import os
from pytest import fixture
from mock import patch, call

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.system_build import SystemBuildTask


class TestSystemBuildTask:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'build',
            '--description', '../data/description',
            '--target-dir', 'some-target'
        ]
        self.abs_target_dir = os.path.abspath('some-target')

        kiwi.tasks.system_build.Privileges = mock.Mock()
        kiwi.tasks.system_build.Path = mock.Mock()

        kiwi.tasks.system_build.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.manager = mock.Mock()
        self.system_prepare = mock.Mock()
        self.system_prepare.setup_repositories = mock.Mock(
            return_value=self.manager
        )

        self.runtime_checker = mock.Mock()
        kiwi.tasks.base.RuntimeChecker = mock.Mock(
            return_value=self.runtime_checker
        )

        self.runtime_config = mock.Mock()
        self.runtime_config.get_disabled_runtime_checks.return_value = []
        kiwi.tasks.base.RuntimeConfig = mock.Mock(
            return_value=self.runtime_config
        )

        kiwi.tasks.system_build.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )

        self.setup = mock.Mock()
        kiwi.tasks.system_build.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.profile = mock.Mock()
        self.profile.dot_profile = dict()
        kiwi.tasks.system_build.Profile = mock.Mock(
            return_value=self.profile
        )

        self.result = mock.Mock()
        self.builder = mock.MagicMock()
        self.builder.create = mock.Mock(
            return_value=self.result
        )
        kiwi.tasks.system_build.ImageBuilder.new = mock.Mock(
            return_value=self.builder
        )

        self.task = SystemBuildTask()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['build'] = False
        self.task.command_args['--allow-existing-root'] = True
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--target-dir'] = 'some-target'
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--add-package'] = []
        self.task.command_args['--add-bootstrap-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--ignore-repos'] = False
        self.task.command_args['--ignore-repos-used-for-build'] = False
        self.task.command_args['--set-container-derived-from'] = None
        self.task.command_args['--set-container-tag'] = None
        self.task.command_args['--add-container-label'] = []
        self.task.command_args['--clear-cache'] = False
        self.task.command_args['--signing-key'] = []

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    def test_process_system_build(self, mock_keys, mock_log):
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.runtime_checker.\
            check_boot_description_exists.assert_called_once_with()
        self.runtime_checker.\
            check_initrd_selection_required.assert_called_once_with()
        self.runtime_checker.\
            check_consistent_kernel_in_boot_and_system_image.\
            assert_called_once_with()
        self.runtime_checker.\
            check_container_tool_chain_installed.assert_called_once_with()
        self.runtime_checker.\
            check_volume_setup_defines_multiple_fullsize_volumes.\
            assert_called_once_with()
        self.runtime_checker.\
            check_volume_setup_has_no_root_definition.\
            assert_called_once_with()
        self.runtime_checker.\
            check_volume_label_used_with_lvm.assert_called_once_with()
        self.runtime_checker.\
            check_swap_name_used_with_lvm.assert_called_once_with()
        self.runtime_checker.\
            check_xen_uniquely_setup_as_server_or_guest.\
            assert_called_once_with()
        self.runtime_checker.\
            check_target_directory_not_in_shared_cache.\
            assert_called_once_with(self.abs_target_dir)
        self.runtime_checker.\
            check_dracut_module_versions_compatible_to_kiwi.\
            assert_called_once_with(
                self.abs_target_dir + '/build/image-root'
            )
        self.runtime_checker.\
            check_mediacheck_installed.assert_called_once_with()
        self.runtime_checker.\
            check_dracut_module_for_live_iso_in_package_list.\
            assert_called_once_with()
        self.runtime_checker.\
            check_repositories_configured.assert_called_once_with()
        self.runtime_checker.\
            check_dracut_module_for_disk_overlay_in_package_list.\
            assert_called_once_with()
        self.runtime_checker.\
            check_dracut_module_for_disk_oem_in_package_list.\
            assert_called_once_with()
        self.runtime_checker.\
            check_dracut_module_for_oem_install_in_package_list.\
            assert_called_once_with()
        self.runtime_checker.\
            check_efi_mode_for_disk_overlay_correctly_setup.\
            assert_called_once_with()
        self.runtime_checker.\
            check_architecture_supports_iso_firmware_setup.\
            assert_called_once_with()
        self.system_prepare.setup_repositories.assert_called_once_with(
            False, ['some_key', 'some_other_key'], None
        )
        self.system_prepare.install_bootstrap.assert_called_once_with(
            self.manager, []
        )
        self.system_prepare.install_system.assert_called_once_with(
            self.manager
        )
        self.profile.create.assert_called_once_with(
            self.abs_target_dir + '/build/image-root/.profile'
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.import_overlay_files.assert_called_once_with()
        self.setup.import_repositories_marked_as_imageinclude.\
            assert_called_once_with()
        self.setup.call_post_bootstrap_script.assert_called_once_with()
        self.setup.call_config_script.assert_called_once_with()
        self.setup.import_image_identifier.assert_called_once_with()
        self.setup.setup_groups.assert_called_once_with()
        self.setup.setup_users.assert_called_once_with()
        self.setup.setup_keyboard_map.assert_called_once_with()
        self.setup.setup_locale.assert_called_once_with()
        self.setup.setup_plymouth_splash.assert_called_once_with()
        self.setup.setup_timezone.assert_called_once_with()
        self.setup.setup_permissions.assert_called_once_with()
        self.setup.setup_selinux_file_contexts.assert_called_once_with()
        self.system_prepare.pinch_system.assert_has_calls(
            [call(force=False), call(force=True)]
        )
        assert self.system_prepare.clean_package_manager_leftovers.called
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            os.sep.join([self.abs_target_dir, 'kiwi.result'])
        )

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    def test_process_system_build_add_package(self, mock_keys, mock_log):
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with(
            False, ['some_key', 'some_other_key'], None
        )
        self.system_prepare.install_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    def test_process_system_update_delete_package(self, mock_keys, mock_log):
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with(
            False, ['some_key', 'some_other_key'], None
        )
        self.system_prepare.delete_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    @patch('kiwi.xml_state.XMLState.set_container_config_tag')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_set_container_tag(
        self, mock_log, mock_set_container_tag
    ):
        self._init_command_args()
        self.task.command_args['--set-container-tag'] = 'new_tag'
        self.task.process()
        mock_set_container_tag.assert_called_once_with(
            'new_tag'
        )

    @patch('kiwi.xml_state.XMLState.add_container_config_label')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_add_container_label(
        self, mock_log, mock_add_container_label
    ):
        self._init_command_args()
        self.task.command_args['--add-container-label'] = [
            'newLabel=value', 'anotherLabel=my=crazy value'
        ]
        self.task.process()
        mock_add_container_label.assert_has_calls([
            call('newLabel', 'value'),
            call('anotherLabel', 'my=crazy value')
        ])

    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_add_container_label_invalid_format(
        self, mock_logger
    ):
        self._init_command_args()
        self.task.command_args['--add-container-label'] = ['newLabel:value']
        with self._caplog.at_level(logging.WARNING):
            self.task.process()

    @patch('kiwi.xml_state.XMLState.set_derived_from_image_uri')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_set_derived_from_uri(
        self, mock_log, mock_set_derived_from_uri
    ):
        self._init_command_args()
        self.task.command_args['--set-container-derived-from'] = 'file:///new'
        self.task.process()
        mock_set_derived_from_uri.assert_called_once_with(
            'file:///new'
        )

    @patch('kiwi.xml_state.XMLState.set_repository')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_set_repo(
        self, mock_log, mock_set_repo
    ):
        self._init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias',
            None, None, None, [], None, None, None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_add_repo(
        self, mock_log, mock_add_repo
    ):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias,99,false,true'
        ]
        self.task.process()
        mock_add_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', '99',
            False, True, [], None, None, None
        )

    def test_process_system_build_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['build'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::build'
        )

    @patch('kiwi.xml_state.XMLState.delete_repository_sections')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_prepare_ignore_repos(
        self, mock_log, mock_delete_repos
    ):
        self._init_command_args()
        self.task.command_args['--ignore-repos'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.delete_repository_sections_used_for_build')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_prepare_ignore_repos_used_for_build(
        self, mock_log, mock_delete_repos
    ):
        self._init_command_args()
        self.task.command_args['--ignore-repos-used-for-build'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()
