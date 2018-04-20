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
from kiwi.repository.zypper import RepositoryZypper
from kiwi.repository.yum import RepositoryYum
from kiwi.repository.apt import RepositoryApt
from kiwi.repository.dnf import RepositoryDnf

from kiwi.exceptions import (
    KiwiRepositorySetupError
)


class Repository(object):
    """
    **Repository factory**

    :param object root_bind: instance of RootBind
    :param str package_manager: package manager name
    :param list custom_args: list of custom package manager arguments
        to setup the repository

    :raises KiwiRepositorySetupError: if package_manager is not supported
    """
    def __new__(self, root_bind, package_manager, custom_args=None):
        if package_manager == 'zypper':
            return RepositoryZypper(root_bind, custom_args)
        elif package_manager == 'yum':
            return RepositoryYum(root_bind, custom_args)
        elif package_manager == 'dnf':
            return RepositoryDnf(root_bind, custom_args)
        elif package_manager == 'apt-get':
            return RepositoryApt(root_bind, custom_args)
        else:
            raise KiwiRepositorySetupError(
                'Support for %s repository manager not implemented' %
                package_manager
            )
