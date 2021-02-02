import io
from mock import (
    patch, Mock, MagicMock, call
)
from pytest import (
    raises, fixture
)

from kiwi.obs import OBS
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiUriOpenError,
    KiwiOBSBuildInfoError,
    KiwiOBSProjectError,
    KiwiOBSSourceError
)


class TestOBS:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.obs.RuntimeConfig')
    def setup(self, mock_RuntimeConfig):
        runtime_config = Mock()
        runtime_config.get_obs_api_server_url.return_value = \
            Defaults.get_obs_api_server_url()
        mock_RuntimeConfig.return_value = runtime_config
        self.obs = OBS(
            'Virtualization:Appliances:SelfContained:suse/box',
            'bob', 'secret', ['Kernel'], None, None
        )

    @patch('kiwi.obs.RuntimeConfig')
    def test_init_raises_invalid_project_path(self, mock_RuntimeConfig):
        with raises(KiwiOBSProjectError):
            self.obs = OBS('OBS:Project', 'user', 'pwd', None, None, None)

    @patch.object(OBS, '_delete_obsrepositories_placeholder_repo')
    @patch.object(OBS, '_create_request')
    def test_fetch_obs_image_return_early(
        self, mock_create_request, mock_delete_obsrepositories_placeholder_repo
    ):
        mock_delete_obsrepositories_placeholder_repo.return_value = False
        # return early because obsrepositories flag is not used
        self.obs.add_obs_repositories(Mock())
        assert not mock_create_request.called

    @patch('requests.get')
    @patch('kiwi.obs.HTTPBasicAuth')
    @patch('kiwi.obs.NamedTemporaryFile')
    @patch('kiwi.obs.etree')
    @patch('os.path.exists')
    @patch('kiwi.obs.Command.run')
    def test_fetch_obs_image(
        self, mock_Command_run, mock_os_path_exists, mock_etree,
        mock_NamedTemporaryFile, mock_HTTPBasicAuth, mock_requests_get
    ):
        # check exception on existing checkout dir
        mock_os_path_exists.return_value = True
        with raises(KiwiOBSSourceError):
            self.obs.fetch_obs_image('checkout_dir')

        # check Exception on valid request but unexpected content
        mock_os_path_exists.return_value = False
        xml_root = MagicMock()
        xml_root.xpath.return_value = []
        buildinfo_xml_tree = MagicMock()
        buildinfo_xml_tree.getroot.return_value = xml_root
        mock_etree.parse.return_value = buildinfo_xml_tree
        with patch('builtins.open', create=True):
            with raises(KiwiOBSSourceError):
                self.obs.fetch_obs_image('checkout_dir')

        # check Exception on source service
        entry = Mock()
        entry.get.return_value = '_service'
        xml_root.xpath.return_value = [entry]
        with patch('builtins.open', create=True):
            with raises(KiwiOBSSourceError):
                self.obs.fetch_obs_image('checkout_dir')

        # check correct checkout of one source file
        mock_requests_get.reset_mock()
        entry.get.return_value = 'some_source_file'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            self.obs.fetch_obs_image('checkout_dir')
            mock_Command_run.assert_called_once_with(
                ['mkdir', '-p', 'checkout_dir']
            )
            assert mock_open.call_args_list == [
                call(mock_NamedTemporaryFile.return_value.name, 'wb'),
                call('checkout_dir/some_source_file', 'wb')
            ]

    @patch('requests.get')
    @patch('kiwi.obs.HTTPBasicAuth')
    @patch('kiwi.obs.NamedTemporaryFile')
    @patch('kiwi.obs.etree')
    @patch('kiwi.obs.SolverRepositoryBase')
    @patch('kiwi.obs.Uri')
    def test_add_obs_repositories(
        self, mock_Uri, mock_SolverRepositoryBase,
        mock_etree, mock_NamedTemporaryFile, mock_HTTPBasicAuth,
        mock_requests_get
    ):
        xml_state = MagicMock()
        repository_section_std = MagicMock()
        repository_section_std.get_source().get_path.return_value = \
            'http://foo'
        repository_section_obs = MagicMock()
        repository_section_obs.get_source().get_path.return_value = \
            'obsrepositories'

        xml_state.get_repository_sections.return_value = \
            [repository_section_std, repository_section_obs]

        # check Exception on request
        mock_requests_get.side_effect = Exception
        with raises(KiwiUriOpenError):
            self.obs.add_obs_repositories(xml_state)

        # check Exception on valid request but unexpected content
        mock_requests_get.side_effect = None
        xml_root = MagicMock()
        xml_root.xpath.return_value = []
        buildinfo_xml_tree = MagicMock()
        buildinfo_xml_tree.getroot.return_value = xml_root
        mock_etree.parse.return_value = buildinfo_xml_tree
        with patch('builtins.open', create=True):
            with raises(KiwiOBSBuildInfoError):
                self.obs.add_obs_repositories(xml_state)

        # check on unreachable repo
        repo_uri = Mock()
        mock_Uri.return_value = repo_uri
        repo_path = Mock()
        repo_path.get.return_value = 'some-repo-url'
        xml_root.xpath.return_value = [
            repo_path
        ]
        mock_requests_get.side_effect = [Mock(), Exception]
        with patch('builtins.open', create=True):
            self.obs.add_obs_repositories(xml_state)
            mock_Uri.assert_called_once_with('some-repo-url')
            assert not xml_state.add_repository.called

        # check on reachable repo with unknown repo type
        repo_path.get.side_effect = [
            None, 'project', 'repository'
        ]
        repo_check = Mock()
        repo_check.get_repo_type.return_value = None
        mock_SolverRepositoryBase.return_value = repo_check
        mock_requests_get.side_effect = None
        mock_Uri.reset_mock()
        with patch('builtins.open', create=True):
            self.obs.add_obs_repositories(xml_state)
            mock_Uri.assert_called_once_with('obs://project/repository')
            assert not xml_state.add_repository.called

        # check on valid processing of one repo
        repo_path.get.side_effect = None
        repo_check.get_repo_type.return_value = 'rpm-md'
        mock_requests_get.reset_mock()
        mock_HTTPBasicAuth.reset_mock()
        mock_Uri.reset_mock()
        with patch('builtins.open', create=True):
            self.obs.add_obs_repositories(xml_state)
            mock_HTTPBasicAuth.assert_called_once_with('bob', 'secret')

            assert mock_requests_get.call_args_list == [
                call(
                    'https://api.opensuse.org/build/Virtualization:'
                    'Appliances:SelfContained:suse/images/x86_64/'
                    'box:Kernel/_buildinfo',
                    auth=mock_HTTPBasicAuth.return_value),
                call(repo_uri.translate.return_value)
            ]

            # ascending priority starting at 1
            xml_state.add_repository.assert_called_once_with(
                repo_uri.translate.return_value, 'rpm-md', None, '1'
            )

            # descending priority starting at 500
            xml_state.add_repository.reset_mock()
            repo_check.get_repo_type.return_value = 'deb'
            self.obs.add_obs_repositories(xml_state)
            xml_state.add_repository.assert_called_once_with(
                repo_uri.translate.return_value, 'deb', None, '500'
            )
