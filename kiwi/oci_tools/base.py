# Copyright (c) 2018 SUSE Linux GmbH.  All rights reserved.
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
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, List, Mapping, Optional, Type

# project
from kiwi.path import Path
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.utils.sync import DataSync


class OCIBase:
    """
    **Base Class for Open Container Interface operations**

    An initiative to formulate industry standards around container
    formats and runtime is available at https://www.opencontainers.org
    Different tools to implement the specifications had been
    created. The purpose of this class and its sub-classes is
    to provide a common interface in kiwi to allow using all
    tools such that the container support in kiwi covers every
    linux distribution no matter what tooling was preferred
    """

    def __init__(self) -> None:
        self.oci_root_dir: Optional[str] = None
        sde = os.environ.get('SOURCE_DATE_EPOCH')
        if sde:
            self.creation_date = datetime.fromtimestamp(
                int(sde), tz=timezone.utc
            ).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        else:
            self.creation_date = datetime.utcnow().strftime(
                '%Y-%m-%dT%H:%M:%S+00:00'
            )
        self.post_init()

    def __enter__(self) -> 'OCIBase':
        return self

    def post_init(self) -> None:
        """
        Post initialization method

        Implementation in specialized OCI tool class if required
        """
        pass

    def import_container_image(self, container_image_ref: str) -> None:
        """
        Imports container image reference to a working space

        Implementation in specialized tool class

        :param string container_image_ref: image reference to import
        """
        raise NotImplementedError

    def export_container_image(
        self,
        filename: str,
        transport: str,
        image_ref: str,
        additional_refs: Optional[List[str]] = None,
    ) -> None:
        """
        Exports the working container to a container image archive

        Implementation in specialized tool class

        :param str filename: The resulting filename
        :param str transport: The archive format
        :param str image_ref: Image reference of the exported image
        :param list additional_names: List of additional references
        """
        raise NotImplementedError

    def init_container(self) -> None:
        """
        Initialize a new container

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def unpack(self) -> None:
        """
        Unpack current container root data

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def sync_rootfs(
        self, root_dir: str, exclude_list: Optional[List[str]] = None
    ) -> None:
        """
        Synchronizes the image root with the rootfs of the container

        Implementation in specialized tool class

        :param string root_dir: root directory of the prepare step
        :param list exclude_list: list of paths to exclude
        """
        raise NotImplementedError

    def import_rootfs(
        self, root_dir: str, exclude_list: Optional[List[str]] = None
    ) -> None:
        """
        Synchronizes the container rootfs with the root tree of the build

        Implementation in specialized tool class

        :param string root_dir: root directory used in prepare step
        :param list exclude_list: list of paths to exclude
        """
        raise NotImplementedError

    def repack(self, oci_config: Mapping[str, Any]) -> None:
        """
        Pack root data directory into container image

        Implementation in specialized tool class

        :param list oci_config: meta data list
        """
        raise NotImplementedError

    def set_config(self, oci_config: Mapping[str, Any]) -> None:
        """
        Set list of meta data information such as entry_point,
        maintainer, etc... to the container. The validation of
        the list content is handled by the underlaying toolkit

        Implementation in specialized tool class

        :param list oci_config: meta data list
        """
        raise NotImplementedError

    def post_process(self) -> None:
        """
        Performs latest steps after the container layers is added and
        configured.

        Implementation in specialized tool class
        """
        raise NotImplementedError

    @staticmethod
    def _sync_data(
        origin: str,
        destination: str,
        exclude_list: Optional[List[str]] = None,
        options: Optional[List[str]] = None,
    ) -> None:
        """
        Synchronizes the origin and destination paths to be equivalent

        :param string origin: the source path
        :param string destination: the destination path
        """
        sync = DataSync(origin, destination)
        sync.sync_data(options=options, exclude=exclude_list)

    @staticmethod
    def _skopeo_provides_tmpdir_option() -> bool:
        """
        Check if skopeo provides the --tmpdir option
        Beginning with version >= 0.2 skopeo provides it.
        """
        tool = 'skopeo'
        expected_version = (0, 2, 0)
        if Path.which(filename=tool, access_mode=os.X_OK):
            if CommandCapabilities.check_version(
                tool, expected_version, raise_on_error=False
            ):
                return True
        return False

    # pragma: no cover
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        pass
