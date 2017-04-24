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
from kiwi.system.root_import.docker import RootImportDocker
from kiwi.system.root_import.oci import RootImportOCI
from kiwi.exceptions import KiwiRootImportError
from kiwi.logger import log


class RootImport(object):
    """
    Root import factory

    Attibutes

    * :attr:`root_dir`
        root directory path name

    * :attr:`image_uri`
        a uri to an image containing a the root system

    * :attr:`image_type`
        type of the image to import
    """
    def __new__(self, root_dir, image_uri, image_type):
        log.info(
            'Importing root from a {0} image type'.format(image_type)
        )
        if image_type == 'docker':
            root_import = RootImportDocker(root_dir, image_uri)
        elif image_type == 'oci':
            root_import = RootImportOCI(root_dir, image_uri)
        else:
            raise KiwiRootImportError(
                'Support to import {0} images not implemented'.format(
                    image_type
                )
            )
        return root_import
