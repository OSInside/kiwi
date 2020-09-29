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
from kiwi.exceptions import (
    KiwiRequestedTypeError
)


class ImageBuilder(metaclass=ABCMeta):
    """
    Image builder factory
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        xml_state: object, target_dir: str,
        root_dir: str, custom_args: Dict=None  # noqa: E252
    ):
        image_type = xml_state.get_build_type_name()
        name_map = {
            'filesystem':
                'FileSystemBuilder' if
                image_type in Defaults.get_filesystem_image_types() else None,
            'disk':
                'DiskBuilder' if
                image_type in Defaults.get_disk_image_types() else None,
            'live':
                'LiveImageBuilder' if
                image_type in Defaults.get_live_image_types() else None,
            'kis':
                'KisBuilder' if
                image_type in Defaults.get_kis_image_types() else None,
            'archive':
                'ArchiveBuilder' if
                image_type in Defaults.get_archive_image_types() else None,
            'container':
                'ContainerBuilder' if
                image_type in Defaults.get_container_image_types() else None
        }
        for builder_namespace, builder_name in list(name_map.items()):
            if builder_name:
                break
        try:
            builder = importlib.import_module(
                'kiwi.builder.{0}'.format(builder_namespace)
            )
            return builder.__dict__[builder_name](
                xml_state, target_dir, root_dir, custom_args
            )
        except Exception as issue:
            raise KiwiRequestedTypeError(
                'Requested image type {0} not supported: {1}'.format(
                    image_type, issue
                )
            )
