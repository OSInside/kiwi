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

# project
from kiwi.utils.checksum import Checksum
from kiwi.logger import log
from kiwi.exceptions import (
    KiwiRootImportError,
    KiwiUriTypeUnknown
)


class RootImportBase(object):
    """
    Imports the root system from an already packed image.

    * :attr:`root_dir`
        root directory path name

    * :attr:`image_uri`
        Uri object to store source location
    """
    def __init__(self, root_dir, image_uri):
        self.unknown_uri = None
        self.root_dir = root_dir
        try:
            if image_uri.is_remote():
                raise KiwiRootImportError(
                    'Only local imports are supported'
                )

            self.image_file = image_uri.translate()

            if not os.path.exists(self.image_file):
                raise KiwiRootImportError(
                    'Could not stat base image file: {0}'.format(
                        self.image_file
                    )
                )
        except KiwiUriTypeUnknown:
            # Let specialized class handle unknown uri schemes
            log.warning(
                'Unkown URI type for the base image: %s', image_uri.uri
            )
            self.unknown_uri = image_uri.uri
        finally:
            self.post_init(image_uri)

    def post_init(self, image_uri):
        """
        Post initalization method

        Implementation in specialized root import class
        """
        pass

    def sync_data(self):
        """
        Synchronizes the root system of `image_file` into the root_dir

        Implementation in specialized root import class
        """
        raise NotImplementedError

    def _make_checksum(self, image):
        checksum = Checksum(image)
        checksum.md5(''.join([image, '.md5']))
