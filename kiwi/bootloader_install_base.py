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


class BootLoaderInstallBase(object):
    """
        base class for bootloader installation on device
    """
    def __init__(self, root_dir, device_provider):
        self.root_dir = root_dir
        self.device_provider = device_provider

        self.device = self.device_provider.get_device()

        self.post_init()

    def post_init(self):
        pass

    def install(self):
        """
            install bootloader on self.device
        """
        raise NotImplementedError
