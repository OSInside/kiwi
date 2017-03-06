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

# project
from kiwi.container import ContainerImage
from kiwi.container.setup import ContainerSetup
from kiwi.system.setup import SystemSetup
from kiwi.logger import log
from kiwi.system.result import Result


class ContainerBuilder(object):
    """
    Container image builder

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`target_dir`
        target directory path name

    * :attr:`container_config`
        Instance of xml_parse::containerconfig

    * :attr:`requested_container_type`
        Configured container type

    * :attr:`system_setup`
        Instance of SystemSetup

    * :attr:`filename`
        File name of the container image

    * :attr:`result`
        Instance of Result
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.container_config = xml_state.get_container_config()
        self.requested_container_type = xml_state.get_build_type_name()
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
                '.', self.requested_container_type, '.tar.xz'
            ]
        )
        self.result = Result(xml_state)

    def create(self):
        """
        Builds a container image which is usually a tarball including
        container specific metadata.

        Image types which triggers this builder are:

        * image="docker"
        """
        log.info(
            'Setting up %s container', self.requested_container_type
        )
        container_setup = ContainerSetup(
            self.requested_container_type, self.root_dir, self.container_config
        )
        container_setup.setup()

        log.info(
            '--> Creating container image'
        )
        container_image = ContainerImage(
            self.requested_container_type, self.root_dir, self.container_config
        )
        container_image.create(
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
            filename=self.system_setup.export_rpm_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_rpm_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result
