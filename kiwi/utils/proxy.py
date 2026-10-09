# Copyright (c) 2026 SUSE Software Solutions Germany GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import os
import re
import logging
from configparser import ConfigParser
from typing import (
    Dict, List, Optional
)

# project
import kiwi.defaults as defaults
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.sysconfig import SysConfig

log = logging.getLogger('kiwi')


class HostProxy:
    """
    **Provides the proxy setup of the host kiwi is called at**

    The proxy settings are taken from the environment of the
    kiwi process. Settings not present in the environment are
    completed from the host sysconfig proxy file if the proxy
    is enabled there. In addition the proxy setup of the host
    package manager configuration can be read for package managers
    which are called by kiwi with a custom configuration file

    :param str sysconfig_proxy:
        sysconfig proxy file path, defaults to HOST_SYSCONFIG_PROXY
    """
    proxy_names = ['http_proxy', 'https_proxy', 'ftp_proxy', 'no_proxy']

    def __init__(self, sysconfig_proxy: Optional[str] = None) -> None:
        self.proxy: Dict[str, str] = {}
        sysconfig = SysConfig(
            sysconfig_proxy or defaults.HOST_SYSCONFIG_PROXY
        )
        sysconfig_enabled = HostProxy._unquote(
            sysconfig.get('PROXY_ENABLED') or ''
        ) == 'yes'
        for name in HostProxy.proxy_names:
            value = os.environ.get(name) or os.environ.get(name.upper())
            if not value and sysconfig_enabled:
                value = HostProxy._unquote(sysconfig.get(name.upper()) or '')
            if value:
                self.proxy[name] = value

    def has_proxy(self) -> bool:
        """
        Check if a proxy server is configured on the host

        :return: True|False

        :rtype: bool
        """
        return any(
            name != 'no_proxy' for name in self.proxy.keys()
        )

    def get_env(self) -> Dict[str, str]:
        """
        Proxy environment variables in lower and upper case
        notation as different tools look for different variants

        :return: proxy environment variables

        :rtype: dict
        """
        proxy_env = {}
        for name, value in self.proxy.items():
            proxy_env[name] = value
            proxy_env[name.upper()] = value
        return proxy_env

    def get_sysconfig_data(self) -> str:
        """
        Proxy setup in sysconfig proxy file format as
        it is read e.g. by libzypp

        :return: sysconfig proxy file content

        :rtype: str
        """
        sysconfig_data = [
            '# kiwi generated proxy config file',
            'PROXY_ENABLED="{0}"'.format('yes' if self.has_proxy() else 'no')
        ]
        for name in HostProxy.proxy_names:
            sysconfig_data.append(
                '{0}="{1}"'.format(name.upper(), self.proxy.get(name, ''))
            )
        return os.linesep.join(sysconfig_data) + os.linesep

    @staticmethod
    def get_apt_config() -> List[str]:
        """
        Acquire::{http,https,ftp}::Proxy settings from the host
        apt configuration in apt.conf format

        :return: list of apt config lines

        :rtype: list
        """
        apt_proxy_config = []
        if Path.which('apt-config'):
            result = Command.run(
                ['apt-config', 'dump'], raise_on_error=False
            )
            if result.returncode == 0:
                for line in result.output.splitlines():
                    if re.match(
                        r'^Acquire::(http|https|ftp)::Proxy(::\S+)? ".*";$',
                        line
                    ):
                        apt_proxy_config.append(line)
        return apt_proxy_config

    @staticmethod
    def get_dnf_config(dnf_config: Optional[str] = None) -> Dict[str, str]:
        """
        proxy* settings from the main section of the host dnf
        configuration

        :param str dnf_config:
            dnf config file path, defaults to HOST_DNF_CONFIG

        :return: dnf proxy option names and values

        :rtype: dict
        """
        dnf_proxy_config: Dict[str, str] = {}
        dnf_config = dnf_config or defaults.HOST_DNF_CONFIG
        host_config = ConfigParser(interpolation=None, strict=False)
        try:
            host_config.read(dnf_config)
        except Exception as issue:
            log.warning(
                f'Failed to read proxy setup from {dnf_config}: {issue}'
            )
            return dnf_proxy_config
        if host_config.has_section('main'):
            for name, value in host_config.items('main'):
                if name.startswith('proxy'):
                    dnf_proxy_config[name] = value
        return dnf_proxy_config

    @staticmethod
    def _unquote(value: str) -> str:
        return value.strip().strip('"\'')
