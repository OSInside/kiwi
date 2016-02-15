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
from partitioner_gpt import PartitionerGpt
from partitioner_msdos import PartitionerMsDos
from partitioner_dasd import PartitionerDasd

from exceptions import (
    KiwiPartitionerSetupError
)


class Partitioner(object):
    """
        Partitioner factory
    """
    def __new__(self, table_type, storage_provider):
        host_architecture = platform.machine()
        if host_architecture == 'x86_64' and table_type == 'gpt':
            return PartitionerGpt(storage_provider)
        elif host_architecture == 'x86_64' and table_type == 'msdos':
            return PartitionerMsDos(storage_provider)
        elif host_architecture == 'i686' and table_type == 'msdos':
            return PartitionerMsDos(storage_provider)
        elif host_architecture == 'i586' and table_type == 'msdos':
            return PartitionerMsDos(storage_provider)
        elif 's390' in host_architecture and table_type == 'dasd':
            return PartitionerDasd(storage_provider)
        elif 's390' in host_architecture and table_type == 'msdos':
            return PartitionerMsDos(storage_provider)
        else:
            raise KiwiPartitionerSetupError(
                'Support for partitioner on %s architecture not implemented' %
                host_architecture
            )
