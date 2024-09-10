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
import importlib
from typing import Dict
from abc import (
    ABCMeta, abstractmethod
)
from kiwi.defaults import Defaults
from kiwi.xml_state import XMLState

from kiwi.exceptions import KiwiRequestedTypeError


class ImageBuilder(metaclass=ABCMeta):
    """
    Image builder factory
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        xml_state: XMLState, target_dir: str,
        root_dir: str, custom_args: Dict = None
    ):
        image_type = xml_state.get_build_type_name()
        if image_type in Defaults.get_filesystem_image_types():
            name_token = ('filesystem', 'FileSystemBuilder')
        elif image_type in Defaults.get_disk_image_types():
            name_token = ('disk', 'DiskBuilder')
        elif image_type in Defaults.get_live_image_types():
            name_token = ('live', 'LiveImageBuilder')
        elif image_type in Defaults.get_kis_image_types():
            name_token = ('kis', 'KisBuilder')
        elif image_type in Defaults.get_enclaves_image_types():
            name_token = ('enclave', 'EnclaveBuilder')
        elif image_type in Defaults.get_archive_image_types():
            name_token = ('archive', 'ArchiveBuilder')
        elif image_type in Defaults.get_container_image_types():
            name_token = ('container', 'ContainerBuilder')
        else:
            name_token = ('None', 'None')
        try:
            (builder_namespace, builder_name) = name_token
            builder = importlib.import_module(
                'kiwi.builder.{0}'.format(builder_namespace)
            )
            return builder.__dict__[builder_name](
                xml_state, target_dir, root_dir, custom_args
            )
        except Exception as issue:
            raise KiwiRequestedTypeError(
                f'Requested image type {image_type} not supported: {issue}'
            )
