# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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

# project
from kiwi.container.setup.base import ContainerSetupBase
from kiwi.exceptions import KiwiContainerSetupError


class ContainerSetupWsl(ContainerSetupBase):
    """
    WSL new tar setup
    """
    def setup(self):
        """
        Setup container metadata
        """
        # It's expected that the container metadata for the
        # new WSL format is provided by a package or via overlay
        # data. Thus this setup routine only checks for the
        # presence of the data and fails when missing
        distribution_conf = os.path.normpath(
            os.sep.join([self.root_dir, 'etc', 'wsl-distribution.conf'])
        )
        wsl_conf = os.path.normpath(
            os.sep.join([self.root_dir, 'etc', 'wsl.conf'])
        )
        if not os.path.exists(distribution_conf):
            raise KiwiContainerSetupError(
                f'Mandatory WSL {distribution_conf} not found in root tree'
            )
        if not os.path.exists(wsl_conf):
            raise KiwiContainerSetupError(
                f'Mandatory WSL {wsl_conf} not found in root tree'
            )
