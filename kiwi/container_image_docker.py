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
from .command import Command
from .archive_tar import ArchiveTar


class ContainerImageDocker(object):
    """
        Create docker container from a root directory
    """
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def create(self, filename):
        exclude_list = [
            'image', '.profile', '.kconfig', 'var/cache/kiwi', 'boot'
        ]
        # replace potential suffix from filename because
        # it is added by the archive creation call
        archive = ArchiveTar(
            filename.replace('.xz', '')
        )
        archive.create_xz_compressed(
            source_dir=self.root_dir, exclude=exclude_list
        )
