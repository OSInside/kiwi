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
from kiwi.container.oci import ContainerImageOCI
from kiwi.container.appx import ContainerImageAppx

from kiwi.exceptions import (
    KiwiContainerImageSetupError
)


class ContainerImage:
    """
    **Container Image factory**

    :param string name: container system name
    :param string root_dir: root directory path name
    :param dict custom_args: custom arguments
    """
    def __new__(self, name, root_dir, custom_args=None):
        if name == 'docker':
            return ContainerImageOCI(
                root_dir, 'docker-archive', custom_args=custom_args
            )
        elif name == 'oci':
            return ContainerImageOCI(
                root_dir, 'oci-archive', custom_args=custom_args
            )
        elif name == 'appx':
            return ContainerImageAppx(
                root_dir, custom_args=custom_args
            )
        else:
            raise KiwiContainerImageSetupError(
                'Support for {0} container not implemented'.format(name)
            )
