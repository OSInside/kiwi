from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.system.uri import Uri

import hashlib


class TestUri(object):
    @classmethod
    def setup_class(self):
        self.mock_mkdtemp = mock.Mock()
        self.mock_manager = mock.Mock()

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

    def test_is_remote(self):
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.is_remote() is True
        uri = Uri('dir:///path/to/repo', 'rpm-md')
        assert uri.is_remote() is False

    def test_alias(self):
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.alias() == hashlib.md5(
            'https://example.com'.encode()).hexdigest(
        )

    def test_translate_ibs_project(self):
        uri = Uri('ibs://Devel:PubCloud/SLE_12_GA', 'rpm-md')
        assert uri.translate() == \
            'http://download.suse.de/ibs/Devel:/PubCloud/SLE_12_GA'

    def test_translate_obs_distro(self):
        uri = Uri('obs://13.2/repo/oss', 'yast2')
        assert uri.translate() == \
            'http://download.opensuse.org/distribution/13.2/repo/oss'

    def test_translate_obs_project(self):
        uri = Uri('obs://Virt:Appliances/SLE_12', 'rpm-md')
        assert uri.translate() == \
            'http://download.opensuse.org/repositories/Virt:Appliances/SLE_12'

    def test_translate_dir_path(self):
        uri = Uri('dir:///some/path', 'rpm-md')
        assert uri.translate() == '/some/path'

    def test_translate_http_path(self):
        uri = Uri('http://example.com/foo', 'rpm-md')
        assert uri.translate() == 'http://example.com/foo'

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

    def test_translate_suse_buildservice_path(self):
        uri = Uri('suse://openSUSE:13.2/standard', 'yast2')
        assert uri.translate() == \
            '/usr/src/packages/SOURCES/repos/openSUSE:13.2/standard'

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
        result = uri.translate()
        uri.__del__()
        manager.umount.assert_called_once_with()
        mock_wipe.assert_called_once_with(manager.mountpoint)
