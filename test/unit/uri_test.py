from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown
)

from kiwi.uri import Uri

import hashlib


class TestUri(object):
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
        assert uri.is_remote() == True
        uri = Uri('dir:///path/to/repo', 'rpm-md')
        assert uri.is_remote() == False

    def test_alias(self):
        uri = Uri('https://example.com', 'rpm-md')
        assert uri.alias() == hashlib.md5('https://example.com').hexdigest()

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

    @patch('kiwi.command.Command.run')
    @patch('kiwi.uri.mkdtemp')
    def test_translate_iso_path(self, mock_mkdtemp, mock_command):
        mock_mkdtemp.return_value = '/tmp/foo'
        uri = Uri('iso:///image/CDs/openSUSE-13.2-DVD-x86_64.iso', 'yast2')
        result = uri.translate()
        mock_command.assert_called_once_with(
            ['mount', '/image/CDs/openSUSE-13.2-DVD-x86_64.iso', '/tmp/foo']
        )
        assert result == '/tmp/foo'

    @patch('kiwi.command.Command.run')
    @patch('kiwi.uri.mkdtemp')
    def test_destructor(self, mock_mkdtemp, mock_command):
        mock_mkdtemp.return_value = '/tmp/foo'
        uri = Uri('iso:///image/CDs/openSUSE-13.2-DVD-x86_64.iso', 'yast2')
        result = uri.translate()
        mock_command.side_effect = KeyError
        del uri
