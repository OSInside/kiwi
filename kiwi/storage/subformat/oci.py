# Copyright (c) 2026 Marcus Schäfer.  All rights reserved.
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
from pathlib import Path

# project
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.utils.temporary import Temporary
from kiwi.system.root_init import RootInit
from kiwi.system.root_import import RootImport
from kiwi.system.result import Result
from kiwi.command import Command
from kiwi.storage.subformat import DiskFormat
from kiwi.defaults import Defaults
from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import KiwiContainerBuilderError
from kiwi.utils.checksum import Checksum
from kiwi.container import ContainerImage


class DiskFormatOci(DiskFormatBase):
    """
    **Create OCI container which includes the disk image**
    """
    def post_init(self, custom_args: dict) -> None:
        """
        oci disk format post initialization method

        :param dict custom_args: unused
        """
        self.runtime_config = RuntimeConfig()
        self.ensure_empty_tmpdirs = True
        self.image_format: str = 'oci'
        self.container_config = self.xml_state.get_container_config()
        self.bundle_format = self.xml_state.get_build_type_bundle_format()
        self.base_container_uris = self.xml_state.get_derived_from_image_uri()
        self.base_format = custom_args.get(
            'base_format', 'raw'
        )
        self.requested_container_type = custom_args.get(
            'container_format', 'docker'
        )
        self.special_needs = ['appx', 'wsl']
        self.filename = ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + self.xml_state.get_image_version(),
                '.', self.requested_container_type,
                '.tar' if self.requested_container_type not in
                self.special_needs else ''
            ]
        )

    def create_image_format(self) -> None:
        """
        Create oci container and store disk to it
        """
        base_image = None
        container_rootdir = Temporary(prefix='kiwi_container_root.').new_dir()
        container_root = container_rootdir.name
        if self.base_container_uris:
            root = RootInit(
                container_root, allow_existing=True
            )
            root.create()
            root_import = RootImport.new(
                container_root,
                self.base_container_uris,
                self.requested_container_type
            )
            root_import.sync_data()
            base_image = Defaults.get_imported_root_image(
                container_root
            )
            base_image_sha256 = ''.join([base_image, '.sha256'])

        # Create disk format and copy this format or the raw
        # disk to the imported container root dir.
        disk_target = os.sep.join([container_root, 'disk'])
        Path(disk_target).mkdir(parents=True, exist_ok=True)

        if self.bundle_format:
            result = Result(self.xml_state)
            result.add_bundle_format(
                self.xml_state.get_build_type_bundle_format()
            )
            if result.get_name_for_pattern():
                disk_target = '{}/{}.{}'.format(
                    disk_target,
                    result.get_name_for_pattern(),
                    self.base_format
                )

        if self.base_format != 'raw':
            with DiskFormat.new(
                self.base_format, self.xml_state,
                self.root_dir, self.target_dir
            ) as disk_format:
                disk_format.create_image_format()
                disk_format_file = disk_format.get_target_file_path_for_format(
                    self.base_format
                )
                disk_raw_file_stat = os.stat(self.diskname)
                os.chown(
                    disk_format_file,
                    disk_raw_file_stat.st_uid,
                    disk_raw_file_stat.st_gid
                )
                Command.run(
                    ['cp', '-a', disk_format_file, disk_target]
                )
        else:
            Command.run(
                ['cp', '-a', self.diskname, disk_target]
            )

        # build the container
        if base_image:
            checksum = Checksum(base_image)
            if not checksum.matches(checksum.sha256(), base_image_sha256):
                raise KiwiContainerBuilderError(
                    f'base image file {base_image} checksum validation failed'
                )
        container_image = ContainerImage.new(
            self.requested_container_type,
            container_root,
            self.container_config
        )
        self.filename = container_image.create(
            self.filename, base_image or '', self.ensure_empty_tmpdirs,
            self.runtime_config.get_container_compression()
            # appx containers already contains a compressed root
            # wsl containers recommends gzip and we default to it
            if self.requested_container_type not in
            self.special_needs else False
        )

    def store_to_result(self, result: Result) -> None:
        """
        Store result file of the format conversion into the
        provided result instance.

        In case of a oci format we store the result uncompressed
        Since the created container is already compressed

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.filename,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
