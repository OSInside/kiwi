from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown,
    KiwiUriOpenError
)

from kiwi.system.uri import Uri

import hashlib


class TestUri(object):
    def setup(self):
        self.mock_mkdtemp = mock.Mock()
        self.mock_manager = mock.Mock()
        self.runtime_config = mock.Mock()
        self.runtime_config.get_obs_download_server_url = mock.Mock(
            return_value='obs_server'
        )

    @raises(KiwiUriStyleUnknown)
    def test_is_remote_raises_style_error(self):
        uri = Uri('xxx', 'rpm-md')
        uri.is_remote()

    @raises(KiwiUriTypeUnknown)
    def test_is_remote_raises_type_error(self):
        uri = Uri('xtp://download.example.com', 'rpm-md')
        uri.is_remote()

    @raises(KiwiUriStyleUnknown)
    def test_translate_unknown_style(self):
        uri = Uri('xxx', 'rpm-md')
        uri.translate()

    @raises(KiwiUriStyleUnknown)
    def test_translate_unsupported_style(self):
        uri = Uri('ms://foo', 'rpm-md')
        uri.translate()

    @raises(KiwiUriStyleUnknown)
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_obsrepositories_outside_buildservice(
        self, mock_buildservice
    ):
        mock_buildservice.return_value = False
        uri = Uri('obsrepositories:/')
        uri.translate()

    @raises(KiwiUriOpenError)
    @patch('kiwi.system.uri.requests.get')
    def test_translate_obs_uri_not_found(mock_request_get, self):
        mock_request_get.side_effect = Exception
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        uri.runtime_config = self.runtime_config
        assert uri.translate()

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_translate_obs_uri_inside_buildservice(
            self, mock_buildservice, mock_warn
    ):
        mock_buildservice.return_value = True
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'rpm-md')
        uri.runtime_config = self.runtime_config
        assert uri.translate(False) == \
            'obs_server/openSUSE:/Leap:/42.2/standard'
        assert mock_warn.called

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
        uri = Uri('xxx', 'rpm-md')
        assert uri.is_public() is False
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.is_public() is True
        uri = Uri('obs://openSUSE:Leap:42.2/standard', 'yast2')
        self.runtime_config.is_obs_public = mock.Mock(
            return_value=False
        )
        uri.runtime_config = self.runtime_config
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

    def test_translate_http_path(self):
        uri = Uri('http://example.com/foo', 'rpm-md')
        assert uri.translate() == 'http://example.com/foo'

    def test_translate_https_path(self):
        uri = Uri('https://example.com/foo', 'rpm-md')
        assert uri.translate() == 'https://example.com/foo'

    def test_translate_ftp_path(self):
        uri = Uri('ftp://example.com/foo', 'rpm-md')
        assert uri.translate() == 'ftp://example.com/foo'

    @patch('kiwi.system.uri.MountManager')
    @patch('kiwi.system.uri.mkdtemp')
    def test_translate_iso_path(self, mock_mkdtemp, mock_manager):
        mock_mkdtemp.return_value = 'tmpdir'
        manager = mock.Mock()
        manager.mountpoint = mock_mkdtemp.return_value
        mock_manager.return_value = manager
        uri = Uri('iso:///image/CDs/openSUSE-13.2-DVD-x86_64.iso', 'yast2')
        result = uri.translate()
        mock_manager.assert_called_once_with(
            device='/image/CDs/openSUSE-13.2-DVD-x86_64.iso',
            mountpoint='tmpdir'
        )
        manager.mount.assert_called_once_with()
        assert result == 'tmpdir'
        uri.mount_stack = []

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

    @patch('kiwi.system.uri.MountManager')
    @patch('kiwi.system.uri.mkdtemp')
    @patch('kiwi.system.uri.Path.wipe')
    def test_destructor(self, mock_wipe, mock_mkdtemp, mock_manager):
        mock_mkdtemp.return_value = 'tmpdir'
        manager = mock.Mock()
        manager.mountpoint = mock_mkdtemp.return_value
        manager.is_mounted = mock.Mock(
            return_value=True
        )
        mock_manager.return_value = manager
        uri = Uri('iso:///image/CDs/openSUSE-13.2-DVD-x86_64.iso', 'yast2')
        uri.translate()
        uri.__del__()
        manager.umount.assert_called_once_with()
        mock_wipe.assert_called_once_with(manager.mountpoint)
