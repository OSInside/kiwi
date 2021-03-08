import logging
import os
from mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)
import hashlib
import mock

from kiwi.system.uri import Uri

import kiwi

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown,
    KiwiUriOpenError
)


class TestUri:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.mock_mkdtemp = mock.Mock()
        self.mock_manager = mock.Mock()
        self.runtime_config = Mock()
        self.runtime_config.get_obs_download_server_url = mock.Mock(
            return_value='obs_server'
        )
        kiwi.system.uri.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )

    def test_is_remote_raises_style_error(self):
        uri = Uri('xxx', 'rpm-md')
        with raises(KiwiUriStyleUnknown):
            uri.is_remote()

    def test_is_remote_raises_type_error(self):
        uri = Uri('xtp://download.example.com', 'rpm-md')
        with raises(KiwiUriTypeUnknown):
            uri.is_remote()

    def test_translate_unknown_style(self):
        uri = Uri('xxx', 'rpm-md')
        with raises(KiwiUriStyleUnknown):
            uri.translate()

    def test_translate_unsupported_style(self):
        uri = Uri('ms://foo', 'rpm-md')
        with raises(KiwiUriStyleUnknown):
            uri.translate()

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_obsrepositories_outside_buildservice(
        self, mock_buildservice
    ):
        mock_buildservice.return_value = False
        uri = Uri('obsrepositories:/')
        with raises(KiwiUriStyleUnknown):
            uri.translate()

    @patch('kiwi.system.uri.requests.get')
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_obs_uri_not_found(
        mock_buildservice, mock_request_get, self
    ):
        mock_buildservice.return_value = False
        mock_request_get.side_effect = Exception('error')
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        self.runtime_config.get_obs_download_server_url = mock.Mock(
            return_value='http://obs_server'
        )
        uri.runtime_config = self.runtime_config
        with raises(KiwiUriOpenError) as exception_info:
            uri.translate(check_build_environment=False)
        assert f'{exception_info.value}' == \
            'http://obs_server/openSUSE:/Leap:/42.2/standard: error'

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_obs_uri_inside_buildservice(
        self, mock_buildservice
    ):
        mock_buildservice.return_value = True
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'rpm-md')
        uri.runtime_config = self.runtime_config
        with self._caplog.at_level(logging.WARNING):
            assert uri.translate(False) == \
                'obs_server/openSUSE:/Leap:/42.2/standard'

    def test_get_fragment(self):
        uri = Uri('file:///myimage.tar#tag')
        assert uri.get_fragment() == 'tag'
        uri = Uri('file:///myimage.tar')
        assert uri.get_fragment() == ''

    def test_is_remote(self):
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.is_remote() is True
        uri = Uri('dir:///path/to/repo', 'rpm-md')
        assert uri.is_remote() is False
        uri = Uri('/path/to/repo')
        assert uri.is_remote() is False

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_is_remote_in_buildservice(
        self, mock_buildservice
    ):
        mock_buildservice.return_value = True
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        assert uri.is_remote() is False

    @patch('kiwi.system.uri.requests')
    def test_is_public(self, mock_request):
        # unknown uri schema is considered not public
        uri = Uri('xxx', 'rpm-md')
        assert uri.is_public() is False

        # https is public
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.is_public() is True

        # obs is private with obs_public set to false in config
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        self.runtime_config.is_obs_public = mock.Mock(
            return_value=False
        )
        uri.runtime_config = self.runtime_config
        assert uri.is_public() is False

        # unknown uri type considered not public
        uri = Uri('httpx://example.com', 'rpm-md')
        assert uri.is_public() is False

    def test_alias(self):
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.alias() == hashlib.md5(
            'https://example.com'.encode()).hexdigest(
        )

    def test_credentials_file_name(self):
        uri = Uri(
            'http://example.com/foo?credentials=my_credentials&x=2',
            'rpm-md'
        )
        assert uri.credentials_file_name() == 'my_credentials'

    def test_credentials_default_file_name(self):
        uri = Uri(
            'http://example.com/foo',
            'rpm-md'
        )
        assert uri.credentials_file_name() == 'kiwiRepoCredentials'

    def test_translate_http_path_with_token(self):
        uri = Uri(
            'http://foo.bar/baz?asdf',
            'rpm-md'
        )
        assert uri.translate() == 'http://foo.bar/baz?asdf'

    def test_translate_http_path_with_credentials(self):
        uri = Uri(
            'http://example.com/foo?credentials=kiwiRepoCredentials',
            'rpm-md'
        )
        assert uri.translate() == 'http://example.com/foo'

    @patch('kiwi.system.uri.requests.get')
    def test_translate_obs_project(self, mock_request_get):
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        uri.runtime_config = self.runtime_config
        uri.translate()
        mock_request_get.assert_called_once_with(
            'obs_server/openSUSE:/Leap:/42.2/standard'
        )

    def test_translate_dir_path(self):
        uri = Uri('dir:///some/path', 'rpm-md')
        assert uri.translate() == '/some/path'

    @patch('os.path.abspath')
    def test_translate_dir_relative_path(self, mock_abspath):
        mock_abspath.side_effect = lambda path: os.sep.join(
            ['/current/dir', path]
        )
        uri = Uri('dir:some/path', 'rpm-md')
        assert uri.translate() == '/current/dir/some/path'

    def test_translate_http_path(self):
        uri = Uri('http://example.com/foo', 'rpm-md')
        assert uri.translate() == 'http://example.com/foo'

    def test_translate_https_path(self):
        uri = Uri('https://example.com/foo', 'rpm-md')
        assert uri.translate() == 'https://example.com/foo'

    def test_translate_ftp_path(self):
        uri = Uri('ftp://example.com/foo', 'rpm-md')
        assert uri.translate() == 'ftp://example.com/foo'

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_buildservice_path(self, mock_buildservice):
        mock_buildservice.return_value = True
        uri = Uri('obs://openSUSE:13.2/standard', 'yast2')
        assert uri.translate() == \
            '/usr/src/packages/SOURCES/repos/openSUSE:13.2/standard'

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_buildservice_project(self, mock_buildservice):
        mock_buildservice.return_value = True
        uri = Uri('obs://Virtualization:/Appliances/CentOS_7', 'rpm-md')
        assert uri.translate() == \
            '/usr/src/packages/SOURCES/repos/Virtualization:Appliances/CentOS_7'

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_buildservice_container_path(self, mock_buildservice):
        mock_buildservice.return_value = True
        uri = Uri('obs://project/repo/container#latest', 'container')
        assert uri.translate() == \
            '/usr/src/packages/SOURCES/containers/project/repo/container#latest'

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_buildservice_obsrepositories_container_path(
        self, mock_buildservice
    ):
        mock_buildservice.return_value = True
        uri = Uri('obsrepositories:/container#latest', 'container')
        assert uri.translate() == ''.join(
            [
                '/usr/src/packages/SOURCES/containers/',
                '_obsrepositories/container#latest'
            ]
        )

    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_buildservice_obsrepositories(self, mock_buildservice):
        mock_buildservice.return_value = True
        uri = Uri('obsrepositories:/')
        assert uri.translate() == '/usr/src/packages/SOURCES/repos'
