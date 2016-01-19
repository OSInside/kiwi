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
# project
from container_image import ContainerImage
from container_setup import ContainerSetup
from logger import log
from result import Result


class ContainerBuilder(object):
    """
        container image builder
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.root_dir = root_dir
        self.requested_container_name = xml_state.build_type.get_container()
        self.requested_container_type = xml_state.get_build_type_name()
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(), '.tar.xz'
            ]
        )
        self.result = Result()

    def create(self):
        setup_options = {}
        if self.requested_container_name:
            setup_options['container_name'] = self.requested_container_name

        container_setup = ContainerSetup(
            self.requested_container_type, self.root_dir, setup_options
        )
        log.info('Setting up %s container', self.requested_container_type)
        log.info(
            '--> Container name: %s', container_setup.get_container_name()
        )
        container_setup.setup()

        log.info(
            '--> Creating container archive'
        )
        container_image = ContainerImage(self.root_dir)
        container_image.create(
            self.filename
        )
        self.result.add(
            'container', self.filename
        )
        return self.result
