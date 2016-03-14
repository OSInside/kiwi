import sys
import mock

from mock import patch

import kiwi

from .test_helper import *

from kiwi.tasks.system_prepare import SystemPrepareTask


class TestSystemPrepareTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'system', 'prepare',
            '--description', '../data/description',
            '--root', '../data/root-dir'
        ]
        self.setup = mock.Mock()
        self.manager = mock.Mock()
        self.system_prepare = mock.Mock()
        self.profile = mock.Mock()
        kiwi.tasks.system_prepare.Privileges = mock.Mock()
        self.system_prepare.setup_repositories = mock.Mock(
            return_value=self.manager
        )
        kiwi.tasks.system_prepare.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )
        kiwi.tasks.system_prepare.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        kiwi.tasks.system_prepare.Profile = mock.Mock(
            return_value=self.profile
        )
        kiwi.tasks.system_prepare.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = SystemPrepareTask()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['prepare'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--root'] = '../data/root-dir'
        self.task.command_args['--allow-existing-root'] = False
        self.task.command_args['--set-repo'] = None
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--obs-repo-internal'] = False

    def test_process_system_prepare(self):
        self.__init_command_args()
        self.task.command_args['prepare'] = True
        self.task.process()
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

    @patch('kiwi.xml_state.XMLState.set_repository')
    def test_process_system_prepare_set_repo(self, mock_state):
        self.__init_command_args()
        self.task.command_args['--set-repo'] = 'http://example.com,yast2,alias'
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.add_repository')
    def test_process_system_prepare_add_repo(self, mock_state):
        self.__init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.translate_obs_to_ibs_repositories')
    def test_process_system_prepare_use_ibs_repos(self, mock_state):
        self.__init_command_args()
        self.task.command_args['--obs-repo-internal'] = True
        self.task.process()
        mock_state.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.translate_obs_to_suse_repositories')
    @patch('os.path.exists')
    def test_process_system_prepare_use_suse_repos(
        self, mock_exists, mock_suse_repos
    ):
        self.__init_command_args()
        mock_exists.return_value = True
        self.task.process()
        mock_suse_repos.assert_called_once_with()

    def test_process_system_prepare_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['prepare'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::system::prepare'
        )
