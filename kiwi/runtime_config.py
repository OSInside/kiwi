# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
import logging
import yaml

# project
import kiwi.defaults as defaults

from kiwi.defaults import Defaults
from kiwi.utils.size import StringToSize
from kiwi.exceptions import (
    KiwiRuntimeConfigFormatError,
    KiwiRuntimeConfigFileError
)

log = logging.getLogger('kiwi')

RUNTIME_CONFIG = None


class RuntimeConfig:
    """
    **Implements reading of runtime configuration file:**

    1. Check for --config provided from the CLI
    2. ~/.config/kiwi/config.yml
    3. /etc/kiwi.yml

    The KIWI runtime configuration file is a yaml formatted file
    containing information to control the behavior of the tools
    used by KIWI.

    :param bool reread: reread runtime config
    """
    def __init__(self, reread=False):
        global RUNTIME_CONFIG

        if RUNTIME_CONFIG is None or reread:
            config_file = None
            custom_config_file = defaults.CUSTOM_RUNTIME_CONFIG_FILE

            if custom_config_file:
                config_file = custom_config_file
                if not os.path.isfile(config_file):
                    raise KiwiRuntimeConfigFileError(
                        f'Custom config file {config_file!r} not found'
                    )
            elif self._home_path():
                config_file = os.sep.join(
                    [self._home_path(), '.config', 'kiwi', 'config.yml']
                )
            if not config_file or not os.path.exists(config_file):
                config_file = '/etc/kiwi.yml'
            if os.path.exists(config_file):
                log.info(
                    f'Reading runtime config file: {config_file!r}'
                )
                with open(config_file, 'r') as config:
                    RUNTIME_CONFIG = yaml.safe_load(config) or {}

    def get_credentials_verification_metadata_signing_key_file(self):
        """
        Return verification metadata signing key file, used for
        signature creation of rootfs verification metadata:

        credentials:
          - verification_metadata_signing_key_file: ...

        There is no default value for this setting available

        :return: file path name or ''

        :rtype: str
        """
        signing_key_file = self._get_attribute(
            element='credentials',
            attribute='verification_metadata_signing_key_file'
        )
        return signing_key_file if signing_key_file else ''

    def get_obs_download_server_url(self):
        """
        Return URL of buildservice download server in:

        obs:
          - download_url: ...

        if no configuration exists the downloadserver from
        the Defaults class is returned

        :return: URL type data

        :rtype: str
        """
        obs_download_server_url = self._get_attribute(
            element='obs', attribute='download_url'
        )
        return obs_download_server_url if obs_download_server_url else \
            Defaults.get_obs_download_server_url()

    def get_obs_api_server_url(self):
        """
        Return URL of buildservice API server in:

        obs:
          - api_url: ...

        if no configuration exists the API server from
        the Defaults class is returned

        :return: URL type data

        :rtype: str
        """
        obs_api_server_url = self._get_attribute(
            element='obs', attribute='api_url'
        )
        return obs_api_server_url if obs_api_server_url else \
            Defaults.get_obs_api_server_url()

    def get_obs_api_credentials(self):
        """
        Return OBS API credentials if configured:

        obs:
          - user:
              - user_name: user_credentials

        :return: List of Dicts with credentials per user

        :rtype: list
        """
        obs_users = self._get_attribute(element='obs', attribute='user') or []
        if obs_users:
            return obs_users

    def is_obs_public(self):
        """
        Check if the buildservice configuration is public or private in:

        obs:
          - public: true|false

        if no configuration exists we assume to be public

        :return: True or False

        :rtype: bool
        """
        obs_public = self._get_attribute(element='obs', attribute='public')
        if obs_public is None:
            # if the privacy attribute is not set we assume to be public
            obs_public = True
        return bool(obs_public)

    def get_package_changes(self, default=True):
        """
        Return boolean value to express if the image build and bundle
        should contain a .changes file. The .changes file contains
        the package changelog information from all packages installed
        into the image.

        bundle:
          - has_package_changes: true|false

        By default the creation is switched on.
        When building in the Open Build Service the default is
        switched off because obs provides a .report file containing
        the same information.

        :param bool default: Default value

        :return: True or False

        :rtype: bool
        """
        bundle_package_changes = self._get_attribute(
            element='bundle', attribute='has_package_changes'
        )
        if bundle_package_changes is None:
            if Defaults.is_buildservice_worker():
                bundle_package_changes = False
            else:
                bundle_package_changes = default
        return bool(bundle_package_changes)

    def get_bundle_compression(self, default=True):
        """
        Return boolean value to express if the image bundle should
        contain XZ compressed image results or not.

        bundle:
          - compress: true|false

        If compression of image build results is activated the size
        of the bundle is smaller and the download speed increases.
        However the image must be uncompressed before use

        If no compression is explicitly configured, the provided
        default value applies

        :param bool default: Default value

        :return: True or False

        :rtype: bool
        """
        bundle_compress = self._get_attribute(
            element='bundle', attribute='compress'
        )
        if bundle_compress is None:
            bundle_compress = default
        return bool(bundle_compress)

    def get_xz_options(self):
        """
        Return list of XZ compression options in:

        xz:
          - options: ...

        if no configuration exists None is returned

        :return:
            Contains list of options

            .. code:: python

                ['--option=value']

        :rtype: list
        """
        xz_options = self._get_attribute(element='xz', attribute='options')
        return xz_options.split() if xz_options else None

    def get_container_compression(self):
        """
        Return compression for container images

        container:
          - compress: xz|none|true|false

        if no or invalid configuration data is provided, the default
        compression from the Defaults class is returned

        :return: True or False

        :rtype: bool
        """
        container_compression = self._get_attribute(
            element='container', attribute='compress'
        )
        if container_compression is None:
            return Defaults.get_container_compression()
        elif 'xz' == container_compression or container_compression is True:
            return True
        elif 'none' == container_compression or container_compression is False:
            return False
        else:
            log.warning(
                'Skipping invalid container compression: {0}'.format(
                    container_compression
                )
            )
            return Defaults.get_container_compression()

    def get_iso_tool_category(self):
        """
        Return tool category which should be used to build iso images

        iso:
          - tool_category: xorriso

        if no or invalid configuration exists the default tool category
        from the Defaults class is returned

        :return: A name

        :rtype: str
        """
        iso_tool_category = self._get_attribute(
            element='iso', attribute='tool_category'
        )
        if not iso_tool_category:
            return Defaults.get_iso_tool_category()
        elif 'xorriso' in iso_tool_category:
            return iso_tool_category
        else:
            log.warning(
                'Skipping invalid iso tool category: {0}'.format(
                    iso_tool_category
                )
            )
            return Defaults.get_iso_tool_category()

    def get_oci_archive_tool(self):
        """
        Return OCI archive tool which should be used on creation of
        container archives for OCI compliant images, e.g docker

        oci:
          - archive_tool: umoci

        if no configuration exists the default tool from the
        Defaults class is returned

        :return: A name

        :rtype: str
        """
        oci_archive_tool = self._get_attribute(
            element='oci', attribute='archive_tool'
        )
        return oci_archive_tool or Defaults.get_oci_archive_tool()

    def get_max_size_constraint(self):
        """
        Returns the maximum allowed size of the built image. The value is
        returned in bytes and it is specified in build_constraints element
        with the max_size attribute. The value can be specified in bytes or
        it can be specified with m=MB or g=GB.

        build_constraints:
          - max_size: 700m

        if no configuration exists None is returned

        :return: byte value or None

        :rtype: int
        """
        max_size = self._get_attribute(
            element='build_constraints', attribute='max_size'
        )
        return StringToSize.to_bytes(max_size) if max_size else None

    def get_disabled_runtime_checks(self):
        """
        Returns disabled runtime checks. Checks can be disabled with:

        runtime_checks:
            - disable: check_container_tool_chain_installed

        if the provided string does not match any RuntimeChecker method it is
        just ignored.
        """
        disabled_checks = self._get_attribute(
            element='runtime_checks', attribute='disable'
        )
        return disabled_checks or ''

    def _get_attribute(self, element, attribute):
        if RUNTIME_CONFIG:
            try:
                if element in RUNTIME_CONFIG:
                    for attribute_dict in RUNTIME_CONFIG[element]:
                        if attribute in attribute_dict:
                            return attribute_dict[attribute]
            except Exception as issue:
                raise KiwiRuntimeConfigFormatError(
                    f'{type(issue).__name__}: {issue}'
                )

    def _home_path(self):
        return os.environ.get('HOME')
