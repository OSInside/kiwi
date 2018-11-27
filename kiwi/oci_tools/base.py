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
from tempfile import mkdtemp
from datetime import datetime

# project
from kiwi.path import Path
from kiwi.utils.sync import DataSync


class OCIBase(object):
    """
    **Base Class for Open Container Interface operations**

    An initiative to formulate industry standards around container
    formats and runtime is available at https://www.opencontainers.org
    Different tools to implement the specifications had been
    created. The purpose of this class and its sub-classes is
    to provide a common interface in kiwi to allow using all
    tools such that the container support in kiwi covers every
    linux distribution no matter what tooling was preferred

    :param string container_tag: primary tag name
    """
    def __init__(self, container_tag, container_dir=None):
        self.container_tag = container_tag
        self.oci_root_dir = None
        if container_dir:
            self.oci_dir = None
            self.container_dir = container_dir
        else:
            self.oci_dir = mkdtemp(prefix='kiwi_oci_dir.')
            self.container_dir = os.sep.join(
                [self.oci_dir, 'oci_layout']
            )

        self.creation_date = datetime.utcnow().strftime(
            '%Y-%m-%dT%H:%M:%S+00:00'
        )

        self.post_init()

    def post_init(self):
        """
        Post initialization method

        Implementation in specialized OCI tool class if required
        """
        pass

    def init_layout(self, base_image=False):
        """
        Initialize a new container layout

        A new container layout can start with a non empty base root image.

        Implementation in specialized tool class

        :param string base_image: True|False
        """
        raise NotImplementedError

    def unpack(self):
        """
        Unpack current container root data

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def sync_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the image root with the rootfs of the container

        Implementation in specialized tool class

        :param string root_dir: root directory of the prepare step
        :param list exclude_list: list of paths to exclude
        """
        raise NotImplementedError

    def import_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the container rootfs with the root tree of the build

        Implementation in specialized tool class

        :param string root_dir: root directory used in prepare step
        :param list exclude_list: list of paths to exclude
        """
        raise NotImplementedError

    def repack(self):
        """
        Pack root data directory into container image

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def add_tag(self, tag_name):
        """
        Add additional tag name to the container

        Implementation in specialized tool class

        :param string tag_name: A name
        :param string container_name: custom container_dir:tag specifier
        """
        raise NotImplementedError

    def set_config(self, oci_config, base_image=False):
        """
        Set list of meta data information such as entry_point,
        maintainer, etc... to the container. The validation of
        the list content is handled by the underlaying toolkit

        Implementation in specialized tool class

        :param list oci_config: meta data list
        :param string container_name: custom container_dir:tag specifier
        """
        raise NotImplementedError

    def garbage_collect(self):
        """
        Cleanup unused data from operations

        Implementation in specialized tool class
        """
        raise NotImplementedError

    @classmethod
    def _sync_data(self, origin, destination, exclude_list=None, options=None):
        """
        Synchronizes the origin and destination paths to be equivalent

        :param string origin: the source path
        :param string destination: the destination path
        """
        sync = DataSync(origin, destination)
        sync.sync_data(
            options=options, exclude=exclude_list
        )

    def __del__(self):
        if self.oci_dir:
            Path.wipe(self.oci_dir)
