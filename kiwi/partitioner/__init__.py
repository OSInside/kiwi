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
import importlib
from abc import (
    ABCMeta,
    abstractmethod
)
import logging

# project
from kiwi.exceptions import KiwiPartitionerSetupError

log = logging.getLogger('kiwi')


class Partitioner(metaclass=ABCMeta):
    """
    **Partitioner factory**

    :param string table_type: Table type name
    :param object storage_provider: Instance of class based on DeviceProvider
    :param int start_sector: sector number
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        table_type: str, storage_provider: object,
        start_sector: int=None  # noqa: E252
    ):
        name_map = {
            'msdos': 'MsDos',
            'gpt': 'Gpt',
            'dasd': 'Dasd'
        }
        try:
            partitioner = importlib.import_module(
                'kiwi.partitioner.{0}'.format(table_type)
            )
            module_name = 'Partitioner{0}'.format(name_map[table_type])
            if table_type == 'dasd' and start_sector:
                log.warning(
                    'disk start_sector value is ignored for dasd partitions'
                )
                start_sector = None
            return partitioner.__dict__[module_name](
                storage_provider, start_sector
            )
        except Exception as issue:
            raise KiwiPartitionerSetupError(
                'Support for {0} partitioner not implemented: {1}'.format(
                    table_type, issue
                )
            )
