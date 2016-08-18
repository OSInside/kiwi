import sys
import mock

from mock import patch

import kiwi

from .test_helper import *

from kiwi.tasks.system_build import SystemBuildTask
from kiwi.exceptions import *


class TestSystemBuildTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'build',
            '--description', '../data/description',
            '--target-dir', 'some-target'
        ]
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

        kiwi.tasks.system_build.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )

        self.setup = mock.Mock()
        kiwi.tasks.system_build.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.profile = mock.Mock()
        kiwi.tasks.system_build.Profile = mock.Mock(
            return_value=self.profile
        )

        self.result = mock.Mock()
        self.builder = mock.MagicMock()
        self.builder.create = mock.Mock(
            return_value=self.result
        )
        kiwi.tasks.system_build.ImageBuilder = mock.Mock(
            return_value=self.builder
        )

        self.task = SystemBuildTask()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['build'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--target-dir'] = 'some-target'
        self.task.command_args['--obs-repo-internal'] = None
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--add-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--ignore-repos'] = False

    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build(self, mock_log):
        self._init_command_args()
        self.task.command_args['build'] = True
        self.task.process()
        self.runtime_checker.check_image_include_repos_http_resolvable.assert_called_once_with()
        self.runtime_checker.check_target_directory_not_in_shared_cache.assert_called_once_with('some-target')
        self.runtime_checker.check_repositories_configured.assert_called_once_with()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.install_bootstrap.assert_called_once_with(
            self.manager
        )
        self.system_prepare.install_system.assert_called_once_with(
            self.manager
        )
        self.setup.import_shell_environment.assert_called_once_with(
            self.profile
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.import_overlay_files.assert_called_once_with()
        self.setup.import_repositories_marked_as_imageinclude.assert_called_once_with()
        self.setup.call_config_script.assert_called_once_with()
        self.setup.import_image_identifier.assert_called_once_with()
        self.setup.setup_groups.assert_called_once_with()
        self.setup.setup_users.assert_called_once_with()
        self.setup.setup_keyboard_map.assert_called_once_with()
        self.setup.setup_locale.assert_called_once_with()
        self.setup.setup_timezone.assert_called_once_with()
        self.system_prepare.pinch_system.assert_called_once_with(
            manager=self.manager, force=True
        )
        self.setup.call_image_script.assert_called_once_with()
        self.builder.create.assert_called_once_with()
        self.result.print_results.assert_called_once_with()
        self.result.dump.assert_called_once_with(
            'some-target/kiwi.result'
        )

    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_add_package(self, mock_log):
        self._init_command_args()
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.install_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_update_delete_package(self, mock_log):
        self._init_command_args()
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.delete_packages.assert_called_once_with(
            self.manager, ['vim']
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
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.logger.Logger.set_logfile')
    def test_process_system_build_prepare_stage_add_repo(
        self, mock_log, mock_add_repo
    ):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_add_repo.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.xml_state.XMLState.translate_obs_to_ibs_repositories')
    def test_process_system_prepare_use_ibs_repos(
        self, mock_ibs_repo, mock_log
    ):
        self._init_command_args()
        self.task.command_args['--obs-repo-internal'] = True
        self.task.process()
        mock_ibs_repo.assert_called_once_with()

    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.xml_state.XMLState.translate_obs_to_suse_repositories')
    @patch('os.path.exists')
    def test_process_system_prepare_use_suse_repos(
        self, mock_exists, mock_suse_repos, mock_log
    ):
        self._init_command_args()
        mock_exists.return_value = True
        self.task.process()
        mock_suse_repos.assert_called_once_with()

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
