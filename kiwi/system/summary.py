# Copyright (c) 2026 SUSE LLC.  All rights reserved.
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
import logging
from typing import Any, List, Optional, Tuple

# project
from kiwi.defaults import Defaults
from kiwi.firmware import FirmWare
from kiwi.system.uri import Uri
from kiwi.xml_state import XMLState

log: Any = logging.getLogger('kiwi')


class ImageSummary:
    """
    **Brief summary of the image to build**

    Provides what image type is built, from which repositories and
    which of the basic features of the image type are enabled

    :param XMLState xml_state: instance of :class:`XMLState`
    :param str description: path of the image description file
    :param str target_arch: architecture the image is built for
    """

    def __init__(
        self,
        xml_state: XMLState,
        description: str,
        target_arch: Optional[str] = None,
    ) -> None:
        self.xml_state = xml_state
        self.description = description
        self.arch = target_arch or Defaults.get_platform_name()
        self.build_type_name = xml_state.get_build_type_name()
        self.is_disk = self.build_type_name in Defaults.get_disk_image_types()
        self.is_live = self.build_type_name in Defaults.get_live_image_types()

    def print_summary(self) -> None:
        """
        Log the summary of the image
        """
        log.phase('Image summary')
        for key, value in self.get_information():
            log.item(key, value)
        for repository in self.get_repositories():
            log.item('Repositories', repository)
        for feature, enabled in self.get_features():
            log.item('Features', feature, checked=enabled)

    def get_information(self) -> List[Tuple[str, str]]:
        """
        Basic information about the image and its build type

        :return: list of name and value tuples

        :rtype: list
        """
        build_type = self.xml_state.build_type
        information = [
            (
                'Image',
                '{0} {1}'.format(
                    self.xml_state.xml_data.get_name(),
                    self.xml_state.get_image_version(),
                ),
            ),
            ('Description', self.description),
            ('Type', f'{self.build_type_name} ({self.arch})'),
        ]
        if self.xml_state.profiles:
            information.append(('Profiles', ', '.join(self.xml_state.profiles)))
        for uri in self.xml_state.get_derived_from_image_uri():
            information.append(('Base image', Uri.print_sensitive(uri.uri)))
        if build_type.get_filesystem():
            information.append(('Filesystem', build_type.get_filesystem()))
        if build_type.get_format():
            information.append(('Format', build_type.get_format()))
        if self.is_disk or self.is_live:
            information.append(
                ('Firmware', FirmWare(self.xml_state).firmware or 'default')
            )
            information.append(
                (
                    'Bootloader',
                    self.xml_state.get_build_type_bootloader_name(),
                )
            )
        information.append(
            ('Package manager', self.xml_state.get_package_manager())
        )
        return information

    def get_repositories(self) -> List[str]:
        """
        Repositories used to build the image

        :return: list of repository type and location

        :rtype: list
        """
        repositories = []
        for (
            repository
        ) in self.xml_state.get_repository_sections_used_for_build():
            location = Uri.print_sensitive(repository.get_source().get_path())
            repository_type = repository.get_type()
            repositories.append(
                f'{repository_type} {location}' if repository_type else location
            )
        return repositories

    def get_features(self) -> List[Tuple[str, bool]]:
        """
        Basic features of the image type and their state

        :return: list of feature name and enabled state tuples

        :rtype: list
        """
        build_type = self.xml_state.build_type
        features: List[Tuple[str, bool]] = []
        if self.is_disk or self.is_live:
            firmware = FirmWare(self.xml_state)
            features += [
                ('Secure boot', firmware.firmware == 'uefi'),
                ('Legacy BIOS boot', firmware.legacy_bios_mode()),
                (
                    'LUKS encryption',
                    self.xml_state.get_luks_credentials() is not None,
                ),
            ]
        if self.is_disk:
            features.append(
                ('LVM', self.xml_state.get_volume_management() == 'lvm')
            )
            if build_type.get_filesystem() == 'btrfs':
                features.append(
                    (
                        'Btrfs snapshots',
                        bool(build_type.get_btrfs_root_is_snapper_snapshot()),
                    )
                )
            features += [
                ('Software RAID', bool(build_type.get_mdraid())),
                ('Overlay root', bool(build_type.get_overlayroot())),
                ('dm-verity', bool(build_type.get_verity_blocks())),
                ('dm-integrity', bool(build_type.get_standalone_integrity())),
                (
                    'Swap partition',
                    bool(self.xml_state.get_oemconfig_swap_mbytes()),
                ),
                (
                    'Resize on first boot',
                    bool(self.xml_state.get_oemconfig_oem_resize()),
                ),
                ('Install ISO', bool(build_type.get_installiso())),
                ('Install PXE', bool(build_type.get_installpxe())),
            ]
        if self.is_live:
            features += [
                ('Persistent storage', bool(build_type.get_hybridpersistent())),
                ('Media check', bool(build_type.get_mediacheck())),
            ]
        features += [
            (
                'Package signature check',
                bool(self.xml_state.get_rpm_check_signatures()),
            ),
            (
                'Documentation excluded',
                bool(self.xml_state.get_rpm_excludedocs()),
            ),
        ]
        return features
