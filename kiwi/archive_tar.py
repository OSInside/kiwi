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
from command import Command


class ArchiveTar(object):
    """
        extraction/creation of tar archives
    """
    def __init__(self, filename, create_from_file_list=True):
        self.filename = filename
        self.create_from_file_list = create_from_file_list

    def create(self, source_dir, exclude=None, options=None):
        if not options:
            options = []
        Command.run(
            [
                'tar', '-C', source_dir
            ] + options + [
                '-c', '-f', self.filename
            ] + self.__get_archive_items(source_dir, exclude)
        )

    def create_xz_compressed(self, source_dir, exclude=None, options=None):
        if not options:
            options = []
        Command.run(
            [
                'tar', '-C', source_dir
            ] + options + [
                '-cJ', '-f', self.filename + '.xz'
            ] + self.__get_archive_items(source_dir, exclude)
        )

    def create_gnu_gzip_compressed(self, source_dir, exclude=None):
        Command.run(
            [
                'tar', '-C', source_dir,
                '--format=gnu', '-cSz', '-f', self.filename + '.gz'
            ] + self.__get_archive_items(source_dir, exclude)
        )

    def extract(self, dest_dir):
        Command.run(
            ['tar', '-C', dest_dir, '-x', '-v', '-f', self.filename]
        )

    def __get_archive_items(self, source_dir, exclude_list):
        if self.create_from_file_list:
            return self.__get_archive_content_list(source_dir, exclude_list)
        else:
            return ['.'] + self.__get_archive_exclude_list(exclude_list)

    def __get_archive_content_list(self, source_dir, exclude_list=None):
        archive_items = []
        for item in os.listdir(source_dir):
            if not exclude_list:
                archive_items.append(item)
            elif item not in exclude_list:
                archive_items.append(item)
        return archive_items

    def __get_archive_exclude_list(self, exclude_list):
        archive_items = []
        for exclude in exclude_list:
            archive_items.append('--exclude')
            archive_items.append('./' + exclude)
        return archive_items
