from mock import patch, call
import os
import mock

from lxml import etree

from .test_helper import raises, patch_open

from kiwi.solver.repository.base import SolverRepositoryBase
from kiwi.exceptions import KiwiUriOpenError


class TestSolverRepositoryBase(object):
    def setup(self):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.uri = mock.Mock()

        self.solver = SolverRepositoryBase(self.uri)

    @raises(NotImplementedError)
    def test__setup_repository_metadata(self):
        self.solver._setup_repository_metadata()

    def test__get_repomd_xpath(self):
        xml_data = etree.parse('../data/repomd.xml')
        assert self.solver._get_repomd_xpath(
            xml_data, 'repo:data[@type="primary"]/repo:location'
        )[0].get('href') == 'repodata/55f95a93-primary.xml.gz'

    @patch('kiwi.solver.repository.base.NamedTemporaryFile')
    @patch.object(SolverRepositoryBase, 'download_from_repository')
    @patch('lxml.etree.parse')
    def test__get_repomd_xml(self, mock_parse, mock_download, mock_tmpfile):
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        xml_data = mock.Mock()
        mock_parse.return_value = xml_data
        mock_tmpfile.return_value = tmpfile
        assert self.solver._get_repomd_xml() == xml_data
        mock_download.assert_called_once_with(
            'repodata/repomd.xml', 'tmpfile'
        )
        mock_parse.assert_called_once_with('tmpfile')

    @patch('kiwi.solver.repository.base.mkdtemp')
    def test__create_temporary_metadata_dir(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
        self.solver._create_temporary_metadata_dir()
        assert self.solver.repository_metadata_dirs == ['tmpdir']
        mock_mkdtemp.assert_called_once_with(prefix='metadata_dir.')

    @patch_open
    @patch('os.path.exists')
    def test_is_uptodate_static_time(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = 'static'
        self.uri.alias.return_value = 'repo-alias'
        assert self.solver.is_uptodate() is False
        mock_open.assert_called_once_with(
            '/var/tmp/kiwi/satsolver/repo-alias.timestamp'
        )

    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.solver.repository.base.SolverRepositoryBase.timestamp')
    def test_is_uptodate_some_time(
        self, mock_timestamp, mock_exists, mock_open
    ):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.return_value = 'some-time'
        mock_timestamp.return_value = 'some-time'
        self.uri.alias.return_value = 'repo-alias'
        assert self.solver.is_uptodate() is True
        mock_open.assert_called_once_with(
            '/var/tmp/kiwi/satsolver/repo-alias.timestamp'
        )

    def test_timestamp(self):
        assert self.solver.timestamp() == 'static'

    @patch('kiwi.solver.repository.base.urlopen')
    @patch('kiwi.solver.repository.base.Request')
    @patch_open
    def test_download_from_repository_with_credentials(
        self, mock_open, mock_request, mock_urlopen
    ):
        request = mock.Mock()
        mock_request.return_value = request
        location = mock.Mock()
        location.read.return_value = 'data-from-network'
        mock_urlopen.return_value = location
        mock_open.return_value = self.context_manager_mock
        self.uri.is_remote.return_value = True
        self.uri.translate.return_value = 'http://myrepo/file'
        self.solver.user = 'user'
        self.solver.secret = 'secret'
        self.solver.download_from_repository(
            'repodata/file', 'target-file'
        )
        mock_urlopen.assert_called_once_with(request)
        mock_request.assert_called_once_with(
            'http://myrepo/file/repodata/file'
        )
        request.add_header.assert_called_once_with(
            'Authorization', b'Basic dXNlcjpzZWNyZXQ='
        )
        mock_open.assert_called_once_with(
            'target-file', 'wb'
        )
        self.file_mock.write.assert_called_once_with(
            'data-from-network'
        )

    @patch('kiwi.solver.repository.base.urlopen')
    @patch('kiwi.solver.repository.base.Request')
    @patch_open
    def test_download_from_repository_remote(
        self, mock_open, mock_request, mock_urlopen
    ):
        request = mock.Mock()
        mock_request.return_value = request
        location = mock.Mock()
        location.read.return_value = 'data-from-network'
        mock_urlopen.return_value = location
        mock_open.return_value = self.context_manager_mock
        self.uri.is_remote.return_value = True
        self.uri.translate.return_value = 'http://myrepo/file'
        self.solver.download_from_repository('repodata/file', 'target-file')
        mock_urlopen.assert_called_once_with(request)
        mock_request.assert_called_once_with(
            'http://myrepo/file/repodata/file'
        )
        mock_open.assert_called_once_with(
            'target-file', 'wb'
        )
        self.file_mock.write.assert_called_once_with(
            'data-from-network'
        )

    @patch('kiwi.solver.repository.base.urlopen')
    @patch('kiwi.solver.repository.base.Request')
    @patch_open
    def test_download_from_repository_local(
        self, mock_open, mock_request, mock_urlopen
    ):
        request = mock.Mock()
        mock_request.return_value = request
        location = mock.Mock()
        location.read.return_value = 'data'
        mock_urlopen.return_value = location
        mock_open.return_value = self.context_manager_mock
        self.uri.is_remote.return_value = False
        self.uri.translate.return_value = '/my_local_repo/file'
        self.solver.download_from_repository('repodata/file', 'target-file')
        mock_urlopen.assert_called_once_with(request)
        mock_request.assert_called_once_with(
            'file:///my_local_repo/file/repodata/file'
        )
        mock_open.assert_called_once_with(
            'target-file', 'wb'
        )
        self.file_mock.write.assert_called_once_with(
            'data'
        )

    @patch('kiwi.solver.repository.base.urlopen')
    @raises(KiwiUriOpenError)
    def test_download_from_repository_raises(self, mock_urlopen):
        self.uri.is_remote.return_value = False
        self.uri.translate.return_value = '/my_local_repo/file'
        mock_urlopen.side_effect = Exception
        self.solver.download_from_repository('repodata/file', 'target-file')

    @patch('kiwi.solver.repository.base.mkdtemp')
    @patch('kiwi.solver.repository.base.random.randrange')
    @patch('kiwi.solver.repository.base.Command.run')
    def test__create_solvables_rpms2_solv(
        self, mock_command, mock_rand, mock_mkdtemp
    ):
        mock_rand.return_value = 0xfe
        self.solver.repository_metadata_dirs = ['metadata_dir.XXXX']
        mock_mkdtemp.return_value = 'solv_dir.XX'
        self.solver._create_solvables('meta_dir.XX', 'rpms2solv')
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                'rpms2solv meta_dir.XX/*.rpm > solv_dir.XX/solvable-fefefefe'
            ]
        )

    @patch('kiwi.solver.repository.base.mkdtemp')
    @patch('kiwi.solver.repository.base.random.randrange')
    @patch('kiwi.solver.repository.base.Command.run')
    @patch('kiwi.solver.repository.base.glob.iglob')
    def test__create_solvables_rpmmd2_solv(
        self, mock_glob, mock_command, mock_rand, mock_mkdtemp
    ):
        mock_glob.return_value = ['some-solv-data-file']
        mock_rand.return_value = 0xfe
        self.solver.repository_metadata_dirs = ['metadata_dir.XXXX']
        mock_mkdtemp.return_value = 'solv_dir.XX'
        self.solver._create_solvables('meta_dir.XX', 'rpmmd2solv')
        mock_glob.assert_called_once_with('meta_dir.XX/*')
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                ' '.join([
                    'gzip -cd --force some-solv-data-file',
                    '|',
                    'rpmmd2solv > solv_dir.XX/solvable-fefefefe'
                ])
            ]
        )

    @patch('kiwi.solver.repository.base.Command.run')
    @patch('kiwi.solver.repository.base.Path.wipe')
    @patch('kiwi.solver.repository.base.Path.create')
    @patch('kiwi.solver.repository.base.SolverRepositoryBase.is_uptodate')
    @patch.object(SolverRepositoryBase, '_setup_repository_metadata')
    @patch_open
    def test_create_repository_solvable(
        self, mock_open, mock_setup_repository_metadata, mock_is_uptodate,
        mock_path_create, mock_path_wipe, mock_command
    ):
        mock_is_uptodate.return_value = False
        mock_open.return_value = self.context_manager_mock
        self.solver.repository_solvable_dir = 'solvable_dir.XX'
        self.uri.alias.return_value = 'repo-alias'
        self.uri.uri = 'repo-uri'
        assert self.solver.create_repository_solvable('target_dir') == \
            'target_dir/repo-alias'
        mock_is_uptodate.assert_called_once_with('target_dir')
        mock_setup_repository_metadata.assert_called_once_with()
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                'mergesolv solvable_dir.XX/* > target_dir/repo-alias'
            ]
        )
        assert mock_open.call_args_list == [
            call('target_dir/repo-alias.info', 'w'),
            call('target_dir/repo-alias.timestamp', 'w')
        ]
        assert self.file_mock.write.call_args_list == [
            call(''.join(['repo-uri', os.linesep])),
            call('static')
        ]

    @patch('kiwi.solver.repository.base.Path.wipe')
    def test_destructor(self, mock_wipe):
        self.solver.repository_metadata_dirs = ['meta_dir.XX']
        self.solver.repository_solvable_dir = 'solv_dir.XX'
        self.solver.__del__()
        assert mock_wipe.call_args_list == [
            call('meta_dir.XX'), call('solv_dir.XX')
        ]
