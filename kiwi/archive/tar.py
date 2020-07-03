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
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.utils.command_capabilities import CommandCapabilities


class ArchiveTar:
    """
    **Extraction/Creation of tar archives**

    The tarfile python module is not used by that class,
    since it does not provide support for some relevant features
    in comparison to the GNU tar command (e.g. numeric-owner).
    Moreover tarfile lacks support for xz compression under
    Python v2.7.

    :param string filename:
        filename to use for archive extraction or creation
    :param bool create_from_file_list:
        use file list not entire directory to create the archive
    :param list file_list:
        list of files and directorie names to archive
    """
    def __init__(self, filename, create_from_file_list=True, file_list=None):
        self.filename = filename
        self.create_from_file_list = create_from_file_list
        self.file_list = file_list

        if CommandCapabilities.check_version('tar', (1, 27)):
            self.xattrs_options = [
                '--xattrs', '--xattrs-include=*'
            ]
        else:
            self.xattrs_options = []

    def create(self, source_dir, exclude=None, options=None):
        """
        Create uncompressed tar archive

        :param string source_dir: data source directory
        :param list exclude: list of excluded items
        :param list options: custom creation options
        """
        if not options:
            options = []
        Command.run(
            [
                'tar', '-C', source_dir
            ] + options + self.xattrs_options + [
                '-c', '-f', self.filename
            ] + self._get_archive_items(source_dir, exclude)
        )
        return self.filename

    def append_files(self, source_dir, files_to_append, options=None):
        """
        Append files to an already existing uncompressed tar archive

        :param string source_dir: data source directory
        :param list files_to_append: list of items to append
        :param list options: custom options
        """
        if not options:
            options = []
        Command.run(
            [
                'tar', '-C', source_dir, '-r',
                '--file=' + self.filename
            ] + options + self.xattrs_options + files_to_append
        )
        return self.filename

    def create_xz_compressed(
        self, source_dir, exclude=None, options=None, xz_options=None
    ):
        """
        Create XZ compressed tar archive

        :param string source_dir: data source directory
        :param list exclude: list of excluded items
        :param list options: custom tar creation options
        :param list xz_options: custom xz compression options
        """
        if not options:
            options = []
        if not xz_options:
            xz_options = Defaults.get_xz_compression_options()
        bash_command = [
            'tar', '-C', source_dir
        ] + options + self.xattrs_options + [
            '-c', '--to-stdout'
        ] + self._get_archive_items(source_dir, exclude) + [
            '|', 'xz', '-f'
        ] + xz_options + [
            '>', self.filename + '.xz'
        ]
        Command.run(['bash', '-c', ' '.join(bash_command)])
        return self.filename + '.xz'

    def create_gnu_gzip_compressed(self, source_dir, exclude=None):
        """
        Create gzip compressed tar archive

        :param string source_dir: data source directory
        :param list exclude: list of excluded items
        """
        Command.run(
            [
                'tar', '-C', source_dir,
                '--format=gnu', '-cSz', '-f', self.filename + '.gz'
            ] + self._get_archive_items(source_dir, exclude)
        )
        return self.filename + '.gz'

    def extract(self, dest_dir):
        """
        Extract tar archive contents

        :param string dest_dir: target data directory
        """
        Command.run(
            ['tar', '-C', dest_dir, '-x', '-v', '-f', self.filename]
        )

    def _get_archive_items(self, source_dir, exclude_list):
        if self.create_from_file_list:
            return self._get_archive_content_list(
                source_dir, exclude_list, self.file_list
            )
        else:
            return self._get_archive_exclude_list(exclude_list) + ['.']

    def _get_archive_content_list(
        self, source_dir, exclude_list=None, file_list=None
    ):
        final_archive_contents = []
        archive_contents = file_list
        if not archive_contents:
            archive_contents = sorted(os.listdir(source_dir))

        for item in archive_contents:
            if not exclude_list:
                final_archive_contents.append(item)
            elif item not in exclude_list:
                final_archive_contents.append(item)

        return final_archive_contents

    def _get_archive_exclude_list(self, exclude_list):
        archive_items = []
        for exclude in exclude_list:
            archive_items.append('--exclude')
            archive_items.append('./' + exclude)
        return archive_items
