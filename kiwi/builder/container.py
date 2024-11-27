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
import logging
import os
from typing import Dict

# project
from kiwi.container import ContainerImage
from kiwi.container.setup import ContainerSetup
from kiwi.system.setup import SystemSetup
from kiwi.system.result import Result
from kiwi.utils.checksum import Checksum
from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiContainerBuilderError
from kiwi.runtime_config import RuntimeConfig
from kiwi.xml_state import XMLState

log = logging.getLogger('kiwi')


class ContainerBuilder:
    """
    **Container image builder**

    :param object xml_state: Instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: root directory path name
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * xz_options: string of XZ compression parameters
    """
    def __init__(
        self, xml_state: XMLState, target_dir: str,
        root_dir: str, custom_args: Dict = None
    ):
        self.custom_args = custom_args or {}
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.bundle_format = xml_state.get_build_type_bundle_format()
        self.container_config = xml_state.get_container_config()
        self.requested_container_type = xml_state.get_build_type_name()
        self.delta_root = xml_state.build_type.get_delta_root()
        self.base_image = None
        self.base_image_md5 = None
        self.ensure_empty_tmpdirs = True

        self.container_config['xz_options'] = \
            self.custom_args.get('xz_options')

        self.container_config['metadata_path'] = \
            xml_state.build_type.get_metadata_path()

        if xml_state.get_derived_from_image_uri() and not self.delta_root:
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

        if xml_state.build_type.get_ensure_empty_tmpdirs() is False:
            self.ensure_empty_tmpdirs = False

        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + xml_state.get_image_version(),
                '.', self.requested_container_type,
                '.tar' if self.requested_container_type != 'appx' else ''
            ]
        )
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self) -> Result:
        """
        Builds a container image which is usually a data archive
        including container specific metadata.

        Image types which triggers this builder are:

        * image="docker"
        * image="oci"
        * image="appx"

        :return: result

        :rtype: instance of :class:`Result`
        """
        if not self.base_image:
            log.info(
                'Setting up %s container', self.requested_container_type
            )
            container_setup = ContainerSetup.new(
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
        container_image = ContainerImage.new(
            self.requested_container_type, self.root_dir, self.container_config
        )
        self.filename = container_image.create(
            self.filename, self.base_image or '', self.ensure_empty_tmpdirs,
            self.runtime_config.get_container_compression()
            # appx containers already contains a compressed root
            if self.requested_container_type != 'appx' else False
        )
        Result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.filename
        )
        if self.bundle_format:
            self.result.add_bundle_format(self.bundle_format)
        self.result.add(
            key='container',
            filename=self.filename,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        if not self.delta_root:
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
                key='image_changes',
                filename=self.system_setup.export_package_changes(
                    self.target_dir
                ),
                use_for_bundle=True,
                compress=True,
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
