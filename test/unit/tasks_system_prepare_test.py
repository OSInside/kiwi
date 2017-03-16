import sys
import mock

from mock import patch

import kiwi

from .test_helper import argv_kiwi_tests

from kiwi.tasks.system_prepare import SystemPrepareTask


class TestSystemPrepareTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'prepare',
            '--description', '../data/description',
            '--root', '../data/root-dir'
        ]
        kiwi.tasks.system_prepare.Privileges = mock.Mock()

        self.runtime_checker = mock.Mock()
        kiwi.tasks.base.RuntimeChecker = mock.Mock(
            return_value=self.runtime_checker
        )

        self.system_prepare = mock.Mock()
        kiwi.tasks.system_prepare.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )

        self.manager = mock.Mock()
        self.system_prepare.setup_repositories = mock.Mock(
            return_value=self.manager
        )

        self.setup = mock.Mock()
        kiwi.tasks.system_prepare.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        self.profile = mock.Mock()
        kiwi.tasks.system_prepare.Profile = mock.Mock(
            return_value=self.profile
        )

        kiwi.tasks.system_prepare.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = SystemPrepareTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['prepare'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--allow-existing-root'] = False
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--obs-repo-internal'] = False
        self.task.command_args['--add-package'] = []
        self.task.command_args['--delete-package'] = []
        self.task.command_args['--ignore-repos'] = False

    def test_process_system_prepare(self):
        self._init_command_args()
        self.task.command_args['prepare'] = True
        self.task.process()
        self.runtime_checker.check_docker_tool_chain_installed.assert_called_once_with()
        self.runtime_checker.check_image_include_repos_http_resolvable.assert_called_once_with()
        self.runtime_checker.check_target_directory_not_in_shared_cache.assert_called_once_with('../data/root-dir')
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

    def test_process_system_prepare_add_package(self):
        self._init_command_args()
        self.task.command_args['--add-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.install_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    def test_process_system_prepare_delete_package(self):
        self._init_command_args()
        self.task.command_args['--delete-package'] = ['vim']
        self.task.process()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.delete_packages.assert_called_once_with(
            self.manager, ['vim']
        )

    @patch('kiwi.xml_state.XMLState.set_repository')
    def test_process_system_prepare_set_repo(self, mock_state):
        self._init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    def test_process_system_prepare_add_repo(self, mock_state):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.translate_obs_to_ibs_repositories')
    def test_process_system_prepare_use_ibs_repos(self, mock_state):
        self._init_command_args()
        self.task.command_args['--obs-repo-internal'] = True
        self.task.process()
        mock_state.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.translate_obs_to_suse_repositories')
    @patch('os.path.exists')
    def test_process_system_prepare_use_suse_repos(
        self, mock_exists, mock_suse_repos
    ):
        self._init_command_args()
        mock_exists.return_value = True
        self.task.process()
        mock_suse_repos.assert_called_once_with()

    def test_process_system_prepare_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['prepare'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::prepare'
        )

    @patch('kiwi.xml_state.XMLState.delete_repository_sections')
    def test_process_system_prepare_delete_repos(self, mock_delete_repos):
        self._init_command_args()
        self.task.command_args['--ignore-repos'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()
