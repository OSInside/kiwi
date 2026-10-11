import os
from unittest.mock import (
    patch, Mock
)
from pytest import (
    fixture, mark
)

from kiwi.utils.proxy import HostProxy


@mark.no_host_proxy_mock
class TestHostProxy:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog, monkeypatch):
        self._caplog = caplog
        for name in HostProxy.proxy_names:
            monkeypatch.delenv(name, raising=False)
            monkeypatch.delenv(name.upper(), raising=False)
        self.monkeypatch = monkeypatch

    def test_no_proxy(self):
        host_proxy = HostProxy('../data/nonexisting')
        assert host_proxy.has_proxy() is False
        assert host_proxy.get_env() == {}
        assert host_proxy.get_sysconfig_data() == os.linesep.join([
            '# kiwi generated proxy config file',
            'PROXY_ENABLED="no"',
            'HTTP_PROXY=""',
            'HTTPS_PROXY=""',
            'FTP_PROXY=""',
            'NO_PROXY=""'
        ]) + os.linesep

    def test_no_proxy_server(self):
        self.monkeypatch.setenv('no_proxy', 'localhost')
        assert HostProxy('../data/nonexisting').has_proxy() is False

    def test_proxy_from_env(self):
        self.monkeypatch.setenv('http_proxy', 'http://proxy:3128')
        self.monkeypatch.setenv('HTTPS_PROXY', 'http://proxy:3129')
        host_proxy = HostProxy('../data/nonexisting')
        assert host_proxy.has_proxy() is True
        assert host_proxy.get_env() == {
            'http_proxy': 'http://proxy:3128',
            'HTTP_PROXY': 'http://proxy:3128',
            'https_proxy': 'http://proxy:3129',
            'HTTPS_PROXY': 'http://proxy:3129'
        }

    def test_proxy_from_sysconfig(self):
        host_proxy = HostProxy('../data/sysconfig_proxy')
        assert host_proxy.has_proxy() is True
        assert host_proxy.get_env() == {
            'http_proxy': 'http://sysconfig-proxy:3128',
            'HTTP_PROXY': 'http://sysconfig-proxy:3128',
            'https_proxy': 'http://sysconfig-proxy:3129',
            'HTTPS_PROXY': 'http://sysconfig-proxy:3129',
            'no_proxy': 'localhost, 127.0.0.1',
            'NO_PROXY': 'localhost, 127.0.0.1'
        }

    def test_proxy_from_default_sysconfig(self):
        self.monkeypatch.setattr(
            'kiwi.defaults.HOST_SYSCONFIG_PROXY', '../data/sysconfig_proxy'
        )
        assert HostProxy().proxy['http_proxy'] == \
            'http://sysconfig-proxy:3128'

    def test_proxy_env_precedes_sysconfig(self):
        self.monkeypatch.setenv('http_proxy', 'http://proxy:3128')
        host_proxy = HostProxy('../data/sysconfig_proxy')
        assert host_proxy.proxy['http_proxy'] == 'http://proxy:3128'
        assert host_proxy.proxy['https_proxy'] == \
            'http://sysconfig-proxy:3129'

    def test_proxy_sysconfig_disabled(self):
        host_proxy = HostProxy('../data/sysconfig_proxy_disabled')
        assert host_proxy.has_proxy() is False

    @patch('kiwi.utils.proxy.Command.run')
    @patch('kiwi.utils.proxy.Path.which')
    def test_get_apt_config(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/apt-config'
        mock_run.return_value = Mock(
            returncode=0, output=os.linesep.join([
                'APT "";',
                'Acquire "";',
                'Acquire::http "";',
                'Acquire::http::Proxy "http://proxy:3128/";',
                'Acquire::http::Proxy::deb.example.com "DIRECT";',
                'Acquire::http::Proxy-Auto-Detect "/usr/bin/detect";',
                'Acquire::https::Proxy "http://proxy:3129/";',
                'Acquire::Retries "3";'
            ])
        )
        assert HostProxy.get_apt_config() == [
            'Acquire::http::Proxy "http://proxy:3128/";',
            'Acquire::http::Proxy::deb.example.com "DIRECT";',
            'Acquire::https::Proxy "http://proxy:3129/";'
        ]
        mock_run.assert_called_once_with(
            ['apt-config', 'dump'], raise_on_error=False
        )

    @patch('kiwi.utils.proxy.Command.run')
    @patch('kiwi.utils.proxy.Path.which')
    def test_get_apt_config_failed(self, mock_which, mock_run):
        mock_which.return_value = '/usr/bin/apt-config'
        mock_run.return_value = Mock(returncode=1, output='')
        assert HostProxy.get_apt_config() == []

    @patch('kiwi.utils.proxy.Path.which')
    def test_get_apt_config_no_apt(self, mock_which):
        mock_which.return_value = None
        assert HostProxy.get_apt_config() == []

    def test_get_dnf_config(self):
        assert HostProxy.get_dnf_config('../data/dnf_proxy.conf') == {
            'proxy': 'http://dnf-proxy:3128',
            'proxy_username': 'user',
            'proxy_password': 'secret'
        }

    def test_get_dnf_config_default(self):
        self.monkeypatch.setattr(
            'kiwi.defaults.HOST_DNF_CONFIG', '../data/dnf_proxy.conf'
        )
        assert HostProxy.get_dnf_config()['proxy'] == 'http://dnf-proxy:3128'

    def test_get_dnf_config_no_config(self):
        assert HostProxy.get_dnf_config('../data/nonexisting') == {}

    def test_get_dnf_config_broken(self):
        assert HostProxy.get_dnf_config('../data/dnf_broken.conf') == {}
        assert 'Failed to read proxy setup from' in self._caplog.text
