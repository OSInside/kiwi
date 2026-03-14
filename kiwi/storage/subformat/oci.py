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

# project
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.utils.temporary import Temporary
from kiwi.system.root_init import RootInit
from kiwi.system.root_import import RootImport
from kiwi.system.result import Result


class DiskFormatOci(DiskFormatBase):
    """
    **Create OCI container which includes the disk image**
    """
    def post_init(self, custom_args: dict) -> None:
        """
        oci disk format post initialization method

        :param dict custom_args: unused
        """
        self.image_format: str = 'oci'
        self.base_container_uri = custom_args.get('base_container_uri')

    def create_image_format(self) -> None:
        """
        Create oci container and store disk to it
        """
        container_rootdir = Temporary(
            prefix='kiwi_container_root.'
        ).new_dir()
        root = RootInit(
            container_rootdir.name, allow_existing=True
        )
        root.create()
        root_import = RootImport.new(
            container_rootdir.name, self.base_container_uri, self.image_format
        )
        root_import.sync_data()
        # TODO: copy disk image to container root dir: self.diskname
        # TODO: create container: self.get_target_file_path_for_format(self.image_format)

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
            filename=self.get_target_file_path_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=self.runtime_config.get_bundle_compression(
                default=False
            ),
            shasum=True
        )
