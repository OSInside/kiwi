# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from lxml import etree
from xml.dom import minidom

# project
from kiwi.container.setup.base import ContainerSetupBase
from kiwi.exceptions import KiwiContainerSetupError
from kiwi.defaults import Defaults


class ContainerSetupAppx(ContainerSetupBase):
    """
    WSL/Appx container setup
    """
    def setup(self):
        """
        Setup container metadata
        """
        self.appx_at_microsoft = 'http://schemas.microsoft.com/appx'
        self.appx_manifest_file = os.sep.join(
            [self.custom_args.get('metadata_path'), 'AppxManifest.xml']
        )
        self.appx_namespace_map = dict(
            wsl='{0}/manifest/foundation/windows10'.format(
                self.appx_at_microsoft
            ),
            uap='{0}/manifest/uap/windows10'.format(
                self.appx_at_microsoft
            ),
            desktop='{0}/manifest/desktop/windows10'.format(
                self.appx_at_microsoft
            ),
            uap3='{0}/manifest/uap/windows10/3'.format(
                self.appx_at_microsoft
            ),
            mp='{0}/2014/phone/manifest'.format(
                self.appx_at_microsoft
            )
        )
        if not os.path.exists(self.appx_manifest_file):
            raise KiwiContainerSetupError(
                'Appx Manifest not found at: {0}'.format(
                    self.appx_manifest_file
                )
            )
        try:
            self.appx_manifest = etree.parse(
                self.appx_manifest_file
            )
            self._update_identity()
            self._update_desktop_visual()
            self._update_application_metadata()
            xml_data_unformatted = etree.tostring(
                self.appx_manifest.getroot()
            )
            xml_data_domtree = minidom.parseString(xml_data_unformatted)
            xml_data_raw = xml_data_domtree.toprettyxml(
                indent='    ', encoding="utf-8"
            )
            with open(self.appx_manifest_file, 'wb') as appx_manifest:
                for line in xml_data_raw.split(b'\n'):
                    if line.split():
                        appx_manifest.write(line + b'\n')
        except Exception as issue:
            raise KiwiContainerSetupError(
                'Failed to update Appx Manifest: {0}'.format(issue)
            )

    def _update_identity(self):
        identities = self._get_xpath('//wsl:Identity')
        history = self.custom_args.get('history') or {}
        for identity in identities:
            if self._get_microsoft_processor_architecture():
                identity.set(
                    'ProcessorArchitecture',
                    self._get_microsoft_processor_architecture()
                )
            if history.get('package_version'):
                identity.set('Version', history.get('package_version'))
            if history.get('created_by'):
                identity.set('Publisher', history.get('created_by'))

    def _update_desktop_visual(self):
        history = self.custom_args.get('history') or {}
        visuals = self._get_xpath(
            '//wsl:Applications/wsl:Application/uap:VisualElements'
        )
        for visual in visuals:
            if history.get('comment'):
                visual.set('Description', history.get('comment'))

    def _update_application_metadata(self):
        history = self.custom_args.get('history') or {}
        applications = self._get_xpath('//wsl:Applications/wsl:Application')
        extensions = self._get_xpath(
            '//wsl:Applications/wsl:Application/'
            'wsl:Extensions/uap3:Extension'
        )
        aliases = self._get_xpath(
            '//wsl:Applications/wsl:Application/'
            'wsl:Extensions/uap3:Extension/uap3:AppExecutionAlias/'
            'desktop:ExecutionAlias'
        )
        for application in applications:
            if history.get('application_id'):
                application.set('Id', history.get('application_id'))
            if history.get('launcher'):
                application.set('Executable', history.get('launcher'))
        for extension in extensions:
            if history.get('launcher'):
                extension.set('Executable', history.get('launcher'))
        for alias in aliases:
            if history.get('launcher'):
                alias.set('Alias', history.get('launcher'))

    def _get_xpath(self, expression):
        return self.appx_manifest.getroot().xpath(
            expression, namespaces=self.appx_namespace_map
        )

    def _get_microsoft_processor_architecture(self):
        windows = {
            'x86_64': 'x64'
        }
        return windows.get(Defaults.get_platform_name())
