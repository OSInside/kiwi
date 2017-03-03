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

import os
import shutil

# project
from .uri import Uri
from ..container import ContainerImage
from ..path import Path
from ..exceptions import KiwiRootImportError


class RootImport(object):
    """
    Imports the root system from an already packed image.

    * :attr:`xml_state`

    * :attr:`root_dir`
        root directory path name

    * :attr:`base_image`
        packed image that contains the root system to be imported

    * :attr:`image_type`
        type of the image to import, currently only docker is supported
    
    """
    def __init__(self, xml_state, root_dir, image_uri, image_type='docker'):
        base_image = None

        uri = Uri(image_uri, 'images')
        if uri.is_remote():
            raise KiwiRootImportError(
                'Only local imports are supported'
            )
        else:
            base_image = uri.translate()
            if not os.path.exists(base_image):
                raise KiwiRootImportError(
                    'Could not stat base image file: {0}'.format(base_image)
                )

        self.root_dir = root_dir
        self.base_image = base_image
        self.image_type = image_type
        self.xml_state = xml_state

    def sync_data(self):
        """
        Synchronizes the root system of `base_image` into the root_dir
        and keep the original `base_image` file into the `root_dir/image`
        folder for later use.
        """
        image = ContainerImage(
            self.image_type, self.root_dir
        )
        image.unpack_to_root_dir(self.base_image)

        # Keep base image so it can be used in later steps
        dest_dir = os.sep.join([self.root_dir, 'image'])
        Path.create(dest_dir)
        shutil.copy(self.base_image, dest_dir)

        # Update the xml state so the base image will always be local
        # in later steps
        self.xml_state.build_type.set_derived_from(
            'file://image/{0}'.format(os.path.basename(self.base_image))
        )
