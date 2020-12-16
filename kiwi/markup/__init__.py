# Copyright (c) 2020 SUSE LLC.  All rights reserved.
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
from kiwi.exceptions import KiwiAnyMarkupPluginError

log = logging.getLogger('kiwi')


class Markup(metaclass=ABCMeta):
    """
    **Markup factory**

    :param str description: path to description file
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(description: str, name: str='any'):  # noqa: E252
        try:
            markup = Markup._load_markup_by_name(name, description)
            log.info('Support for multiple markup descriptions available')
        except KiwiAnyMarkupPluginError:
            markup = Markup._load_markup_by_name('xml', description)
            log.info('Support for XML markup available')
        return markup

    @staticmethod
    def _load_markup_by_name(name, description):
        name_map = {
            'any': 'Any',
            'xml': 'XML'
        }
        markup = importlib.import_module('kiwi.markup.{0}'.format(name))
        return markup.__dict__['Markup{0}'.format(name_map[name])](
            description
        )
