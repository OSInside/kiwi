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
import platform
import os

# project
from kiwi.container import ContainerImage
from kiwi.container.setup import ContainerSetup
from kiwi.system.setup import SystemSetup
from kiwi.logger import log
from kiwi.system.result import Result
from kiwi.utils.checksum import Checksum
from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiContainerBuilderError
from kiwi.runtime_config import RuntimeConfig


class ContainerBuilder(object):
    """
    **Container image builder**

    :param object xml_state: Instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: root directory path name
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * xz_options: string of XZ compression parameters
    """
    def __init__(self, xml_state, target_dir, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.container_config = xml_state.get_container_config()
        self.requested_container_type = xml_state.get_build_type_name()
        self.base_image = None
        self.base_image_md5 = None

        self.container_config['xz_options'] = custom_args['xz_options'] \
            if custom_args and 'xz_options' in custom_args else None

        if xml_state.get_derived_from_image_uri():
            # The base image is expected to be unpacked by the kiwi
            # prepare step and stored inside of the root_dir/image directory.
            # In addition a md5 file of the image is expected too
            self.base_image = Defaults.get_imported_root_image(
                self.root_dir
            )
            self.base_image_md5 = ''.join([self.base_image, '.md5'])

            if not os.path.exists(self.base_image):
                raise KiwiContainerBuilderError(
                    'Unpacked Base image {0} not found'.format(
                        self.base_image
                    )
                )
            if not os.path.exists(self.base_image_md5):
                raise KiwiContainerBuilderError(
                    'Base image MD5 sum {0} not found at'.format(
                        self.base_image_md5
                    )
                )

        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
                '.', self.requested_container_type, '.tar'
            ]
        )
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self):
        """
        Builds a container image which is usually a tarball including
        container specific metadata.

        Image types which triggers this builder are:

        * image="docker"

        :return: result

        :rtype: instance of :class:`Result`
        """
        if not self.base_image:
            log.info(
                'Setting up %s container', self.requested_container_type
            )
            container_setup = ContainerSetup(
                self.requested_container_type, self.root_dir,
                self.container_config
            )
            container_setup.setup()
        else:
            checksum = Checksum(self.base_image)
            if not checksum.matches(checksum.md5(), self.base_image_md5):
                raise KiwiContainerBuilderError(
                    'base image file {0} checksum validation failed'.format(
                        self.base_image
                    )
                )

        log.info(
            '--> Creating container image'
        )
        container_image = ContainerImage(
            self.requested_container_type, self.root_dir, self.container_config
        )
        self.filename = container_image.create(
            self.filename, self.base_image
        )
        self.result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.filename
        )
        self.result.add(
            key='container',
            filename=self.filename,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result
