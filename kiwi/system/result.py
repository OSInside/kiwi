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
from collections import namedtuple
import logging
import pickle
import os

# project
from kiwi.exceptions import (
    KiwiResultError
)

log = logging.getLogger('kiwi')

# must be global to allow pickle to find it
result_file_type = namedtuple(
    'result_file_type', ['filename', 'use_for_bundle', 'compress', 'shasum']
)


class Result:
    """
    **Collect image building results**

    :param list result_files: list of result files
    :param object class_version: :class:`Result` class version
    :param object xml_state: instance of :class:`XMLState`
    """
    def __init__(self, xml_state):
        self.result_files = {}

        # Instances of this class are stored as result reference.
        # In order to handle class format changes any instance
        # provides a version information
        self.class_version = 1

        self.xml_state = xml_state

    def add(
        self, key, filename, use_for_bundle=True, compress=False, shasum=True
    ):
        """
        Add result tuple to result_files list

        :param str key: name
        :param str filename: file path name
        :param bool use_for_bundle: use when bundling results true|false
        :param bool compress: compress when bundling true|false
        :param bool shasum: create shasum when bundling true|false
        """
        if key and filename:
            self.result_files[key] = result_file_type(
                filename=filename,
                use_for_bundle=use_for_bundle,
                compress=compress,
                shasum=shasum
            )

    def get_results(self):
        """
        Current list of result tuples
        """
        return self.result_files

    def print_results(self):
        """
        Print results human readable
        """
        if self.result_files:
            log.info('Result files:')
            for key, value in sorted(list(self.result_files.items())):
                log.info('--> %s: %s', key, value.filename)

    def dump(self, filename):
        """
        Picke dump this instance to a file

        :param str filename: file path name

        :raises KiwiResultError: if pickle fails to dump :class:`Result`
            instance
        """
        try:
            with open(filename, 'wb') as result:
                pickle.dump(self, result)
        except Exception as e:
            raise KiwiResultError(
                'Failed to pickle dump results: %s' % format(e)
            )

    @staticmethod
    def load(filename):
        """
        Load pickle dumped filename into a Result instance

        :param str filename: file path name

        :raises KiwiResultError: if filename does not exist or pickle fails
            to load filename
        """
        if not os.path.exists(filename):
            raise KiwiResultError(
                'No result information %s found' % filename
            )
        try:
            with open(filename, 'rb') as result:
                return pickle.load(result)
        except Exception as e:
            raise KiwiResultError(
                'Failed to pickle load results: %s' % type(e).__name__
            )

    def verify_image_size(self, size_limit, filename):
        """
        Verifies the given image file does not exceed the size limit.
        Throws an exception if the limit is exceeded. If the size limit
        is set to None no verification is done.

        :param int size_limit: The size limit for filename in bytes.
        :param str filename: File to verify.

        :raises KiwiResultError: if filename exceeds the size limit
        """
        if size_limit is not None:
            if os.path.getsize(filename) > size_limit:
                raise KiwiResultError(
                    'Build constraint failed: {0} is bigger than {1}'
                    .format(filename, size_limit)
                )
