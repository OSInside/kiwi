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
import logging
import importlib
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.system.uri import Uri
from kiwi.exceptions import KiwiRootImportError

log = logging.getLogger('kiwi')


class RootImport(metaclass=ABCMeta):
    """
    Root import factory

    Attibutes

    * :attr:`root_dir`
        root directory path name

    * :attr:`image_uri`
        an instance of :class:`Uri` to an image containing a the root system

    * :attr:`image_type`
        type of the image to import
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(root_dir: str, image_uri: Uri, image_type: str):
        name_map = {
            'docker': 'OCI',
            'oci': 'OCI'
        }
        log.info(
            'Importing root from a {0} image type'.format(image_type)
        )
        (custom_args, module_namespace) = \
            RootImport._custom_args_for_root_import(image_type)
        try:
            rootimport = importlib.import_module(
                'kiwi.system.root_import.{0}'.format(module_namespace)
            )
            module_name = 'RootImport{0}'.format(name_map[module_namespace])
            return rootimport.__dict__[module_name](
                root_dir, image_uri, custom_args
            )
        except Exception as issue:
            raise KiwiRootImportError(
                'Support to import {0} images not implemented: {1}'.format(
                    image_type, issue
                )
            )

    @staticmethod
    def _custom_args_for_root_import(image_type: str):
        if image_type == 'docker':
            custom_args = {'archive_transport': 'docker-archive'}
        else:
            custom_args = {'archive_transport': 'oci-archive'}
        return [custom_args, 'oci']
