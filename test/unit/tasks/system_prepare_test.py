import logging
import sys
import os
from pytest import fixture
from unittest.mock import (
    patch, call, Mock, MagicMock
)

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.system_prepare import SystemPrepareTask


class TestSystemPrepareTask:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'prepare',
            '--description', '../data/description',
            '--root', '../data/root-dir'
        ]

        self.abs_root_dir = os.path.abspath('../data/root-dir')

        self.command = Mock()
        kiwi.tasks.system_prepare.Command = self.command

        kiwi.tasks.system_prepare.Privileges = Mock()

        self.runtime_checker = Mock()
        kiwi.tasks.base.RuntimeChecker = Mock(
            return_value=self.runtime_checker
        )

        self.setup = Mock()
        kiwi.tasks.system_prepare.SystemSetup = Mock(
            return_value=self.setup
        )

        self.profile = Mock()
        self.profile.dot_profile = dict()
        kiwi.tasks.system_prepare.Profile = Mock(
            return_value=self.profile
        )

        kiwi.tasks.system_prepare.Help = Mock(
            return_value=Mock()
        )
        self.task = SystemPrepareTask()
        self.task.runtime_config = MagicMock()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['prepare'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--set-type-attr'] = ['volid=some']
        self.task.command_args['--set-release-version'] = '99'
        self.task.command_args['--allow-existing-root'] = False
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--set-repo-credentials'] = None
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--add-repo-credentials'] = []
        self.task.command_args['--add-package'] = []
        self.task.command_args['--add-bootstrap-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--ignore-repos'] = False
        self.task.command_args['--ignore-repos-used-for-build'] = False
        self.task.command_args['--clear-cache'] = False
        self.task.command_args['--set-container-derived-from'] = None
        self.task.command_args['--set-container-tag'] = None
        self.task.command_args['--add-container-label'] = []
        self.task.command_args['--signing-key'] = []

    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare(self, mock_SystemPrepare, mock_keys):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['prepare'] = True
        self.task.command_args['--clear-cache'] = True
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
            check_volume_setup_has_no_root_definition.assert_called_once_with()
        self.runtime_checker.\
            check_volume_label_used_with_lvm.assert_called_once_with()
        self.runtime_checker.\
            check_swap_name_used_with_lvm.assert_called_once_with()
        self.runtime_checker.\
            check_xen_uniquely_setup_as_server_or_guest.\
            assert_called_once_with()
        self.runtime_checker.\
            check_target_directory_not_in_shared_cache.assert_called_once_with(
                self.abs_root_dir
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
        system_prepare.setup_repositories.assert_called_once_with(
            True, ['some_key', 'some_other_key'], None
        )
        system_prepare.install_bootstrap.assert_called_once_with(
            manager.__enter__.return_value, []
        )
        system_prepare.install_system.assert_called_once_with(
            manager.__enter__.return_value
        )
        self.profile.create.assert_called_once_with(
            self.abs_root_dir + '/.profile'
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
        self.setup.import_files.assert_called_once_with()
        self.setup.setup_selinux_file_contexts.assert_called_once_with()

        system_prepare.pinch_system.assert_has_calls(
            [call(force=False), call(force=True)]
        )
        assert system_prepare.clean_package_manager_leftovers.called

    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_add_package(
        self, mock_SystemPrepare, mock_keys
    ):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        system_prepare.setup_repositories.assert_called_once_with(
            False, ['some_key', 'some_other_key'], None
        )
        system_prepare.install_packages.assert_called_once_with(
            manager.__enter__.return_value, ['vim']
        )

    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_delete_package(
        self, mock_SystemPrepare, mock_keys
    ):
        manager = MagicMock()
        system_prepare = Mock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        mock_keys.return_value = ['some_key', 'some_other_key']
        self._init_command_args()
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        system_prepare.setup_repositories.assert_called_once_with(
            False, ['some_key', 'some_other_key'], None
        )
        system_prepare.delete_packages.assert_called_once_with(
            manager.__enter__.return_value, ['vim']
        )

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_build_invalid_type_attribute(
        self, mock_SystemPrepare, mock_log
    ):
        self._init_command_args()
        self.task.command_args['--set-type-attr'] = [
            'bogus=value'
        ]
        with self._caplog.at_level(logging.ERROR):
            self.task.process()
        assert 'Failed to set type attribute' in self._caplog.text

    @patch('kiwi.xml_state.XMLState.get_repositories_signing_keys')
    @patch('kiwi.xml_state.XMLState.get_preferences_sections')
    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_build_release_version_no_overwrite(
        self, mock_SystemPrepare, mock_logger,
        mock_get_preferences_sections, mock_get_repositories_signing_keys
    ):
        preferences = MagicMock()
        preferences.get_release_version.return_value = None
        mock_get_preferences_sections.return_value = [preferences]
        self._init_command_args()
        self.task.command_args['--set-release-version'] = '42'
        self.task.process()
        preferences.add_release_version.assert_called_once_with('42')

    @patch('kiwi.xml_state.XMLState.set_container_config_tag')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_set_container_tag(
        self, mock_SystemPrepare, mock_set_container_tag
    ):
        self._init_command_args()
        self.task.command_args['--set-container-tag'] = 'new_tag'
        self.task.process()
        mock_set_container_tag.assert_called_once_with(
            'new_tag'
        )

    @patch('kiwi.xml_state.XMLState.add_container_config_label')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_add_container_label(
        self, mock_SystemPrepare, mock_add_container_label
    ):
        self._init_command_args()
        self.task.command_args['--add-container-label'] = ['newLabel=value']
        self.task.process()
        mock_add_container_label.assert_called_once_with(
            'newLabel', 'value'
        )

    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_add_container_label_invalid_format(
        self, mock_SystemPrepare
    ):
        self._init_command_args()
        self.task.command_args['--add-container-label'] = ['newLabel:value']
        with self._caplog.at_level(logging.WARNING):
            self.task.process()

    @patch('kiwi.xml_state.XMLState.set_derived_from_image_uri')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_set_derived_from_uri(
        self, mock_SystemPrepare, mock_set_derived_from_uri
    ):
        self._init_command_args()
        self.task.command_args['--set-container-derived-from'] = 'file:///new'
        self.task.process()
        mock_set_derived_from_uri.assert_called_once_with(
            'file:///new'
        )

    @patch('kiwi.xml_state.XMLState.set_repository')
    @patch('os.path.isfile')
    @patch('os.unlink')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_set_repo(
        self, mock_SystemPrepare, mock_os_unlink,
        mock_os_path_is_file, mock_set_repo
    ):
        mock_os_path_is_file.return_value = False
        self._init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias',
            None, None, None, [], None, None, None
        )
        self.task.command_args['--set-repo-credentials'] = 'user:pass'
        mock_set_repo.reset_mock()
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://user:pass@example.com', 'yast2', 'alias',
            None, None, None, [], None, None, None
        )
        self.task.command_args['--set-repo-credentials'] = '../data/credentials'
        mock_os_path_is_file.return_value = True
        mock_set_repo.reset_mock()
        self.task.process()
        mock_set_repo.assert_called_once_with(
            'http://user:pass@example.com', 'yast2', 'alias',
            None, None, None, [], None, None, None
        )
        mock_os_unlink.assert_called_once_with('../data/credentials')

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_add_repo(
        self, mock_SystemPrepare, mock_add_repo
    ):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example1.com,yast2,alias,99,true',
            'http://example2.com,yast2,alias,99,false,true',
            'http://example3.com,yast2,alias,99,false,true'
        ]
        self.task.process()
        assert mock_add_repo.call_args_list == [
            call(
                'http://example1.com', 'yast2', 'alias', '99',
                True, None, [], None, None, None
            ),
            call(
                'http://example2.com', 'yast2', 'alias', '99',
                False, True, [], None, None, None
            ),
            call(
                'http://example3.com', 'yast2', 'alias', '99',
                False, True, [], None, None, None
            )
        ]
        self.task.command_args['--add-repo-credentials'] = [
            'user1:pass1',
            'user2:pass2'
        ]
        mock_add_repo.reset_mock()
        self.task.process()
        assert mock_add_repo.call_args_list == [
            call(
                'http://user1:pass1@example1.com', 'yast2', 'alias', '99',
                True, None, [], None, None, None
            ),
            call(
                'http://user2:pass2@example2.com', 'yast2', 'alias', '99',
                False, True, [], None, None, None
            ),
            call(
                'http://example3.com', 'yast2', 'alias', '99',
                False, True, [], None, None, None
            )
        ]

    def test_process_system_prepare_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['prepare'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::prepare'
        )

    @patch('kiwi.xml_state.XMLState.delete_repository_sections')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_delete_repos(
        self, mock_SystemPrepare, mock_delete_repos
    ):
        self._init_command_args()
        self.task.command_args['--ignore-repos'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.delete_repository_sections_used_for_build')
    @patch('kiwi.tasks.system_prepare.SystemPrepare')
    def test_process_system_prepare_delete_repos_used_for_build(
        self, mock_SystemPrepare, mock_delete_repos
    ):
        self._init_command_args()
        self.task.command_args['--ignore-repos-used-for-build'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()
