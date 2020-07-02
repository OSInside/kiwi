# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import logging
from tempfile import NamedTemporaryFile

# project
from kiwi.archive.tar import ArchiveTar
from kiwi.defaults import Defaults
from kiwi.utils.compress import Compress
from kiwi.runtime_config import RuntimeConfig
from kiwi.command import Command

from kiwi.exceptions import KiwiContainerSetupError

log = logging.getLogger('kiwi')


class ContainerImageAppx:
    """
    Create Appx container from a root directory for
    WSL(Windows Subsystem Linux)

    :param string root_dir: root directory path name
    :param dict custom_args:

    Custom processing arguments defined as hash keys:

    Example

    .. code:: python

        {
            'metadata_path': 'directory'
        }
    """
    def __init__(self, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.wsl_config = custom_args or {}
        self.runtime_config = RuntimeConfig()

        self.meta_data_path = self.wsl_config.get('metadata_path')

        if not self.meta_data_path:
            raise KiwiContainerSetupError(
                'No metadata path specified to build appx container'
            )

        if not os.path.exists(self.meta_data_path):
            raise KiwiContainerSetupError(
                'Specified metadata path {0} does not exist'.format(
                    self.meta_data_path
                )
            )

    def create(self, filename, base_image=None):
        """
        Create WSL/Appx archive

        :param string filename: archive file name
        :param string base_image: not-supported
        """
        exclude_list = Defaults.get_exclude_list_for_root_data_sync()
        exclude_list.append('boot')
        exclude_list.append('dev')
        exclude_list.append('sys')
        exclude_list.append('proc')

        # The C code of WSL-DistroLauncher harcodes the name for the
        # root tarball to be install.tar.gz. Thus we have to use this
        # name for the root tarball
        archive_file_name = os.sep.join(
            [self.meta_data_path, 'install.tar']
        )
        archive = ArchiveTar(
            archive_file_name
        )
        archive_file_name = archive.create(
            self.root_dir, exclude=exclude_list
        )
        compressor = Compress(archive_file_name)
        archive_file_name = compressor.gzip()

        filemap_file = NamedTemporaryFile()
        with open(filemap_file.name, 'w') as filemap:
            filemap.write('[Files]{0}'.format(os.linesep))
            for topdir, dirs, files in sorted(os.walk(self.meta_data_path)):
                for entry in sorted(dirs + files):
                    if entry in files:
                        mapfile = os.sep.join([topdir, entry])
                        log.info(
                            'Adding {0} to Appx filemap'.format(mapfile)
                        )
                        filemap.write(
                            '"{0}" "{1}"{2}'.format(
                                mapfile, os.path.basename(mapfile), os.linesep
                            )
                        )

        Command.run(
            ['appx', '-o', filename, '-f', filemap_file.name]
        )
        return filename
