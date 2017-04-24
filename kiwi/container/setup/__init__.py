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
from kiwi.container.setup.docker import ContainerSetupDocker
from kiwi.container.setup.oci import ContainerSetupOCI

from kiwi.exceptions import (
    KiwiContainerSetupError
)


class ContainerSetup(object):
    """
        container setup factory
    """
    def __new__(self, name, root_dir, custom_args=None):
        if name == 'docker':
            return ContainerSetupDocker(root_dir, custom_args)
        elif name == 'oci':
            return ContainerSetupOCI(root_dir, custom_args)
        else:
            raise KiwiContainerSetupError(
                'Support for %s container not implemented' % name
            )
