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
import logging
import simplejson
import pickle
import os
from typing import (
    Dict, NamedTuple, TypeVar, Any
)

# project
from kiwi.xml_state import XMLState
from kiwi.exceptions import (
    KiwiResultError
)

log = logging.getLogger('kiwi')

# must be global to allow pickle to find it
result_file_type = NamedTuple(
    'result_file_type', [
        ('filename', str),
        ('use_for_bundle', bool),
        ('compress', bool),
        ('shasum', bool)
    ]
)
result_name_tags = NamedTuple(
    'result_name_tags', [
        ('N', str),  # image name
        ('P', str),  # concatenated profile name (_)
        ('A', str),  # architecture name
        ('I', str),  # custom ID setting
        ('T', str),  # image type name
        ('M', str),  # Major version number
        ('m', str),  # Minor version number
        ('p', str),  # Patch version number
        ('v', str)   # Version string
    ]
)

result_type = TypeVar('result_type', bound='Result')


class Result:
    """
    **Collect image building results**

    :param dict result_files: dict of result files
    :param object class_version: :class:`Result` class version
    :param object xml_state: instance of :class:`XMLState`
    """
    def __init__(self, xml_state: XMLState):
        self.result_files: Dict[str, Any] = {}

        # Instances of this class are stored as result reference.
        # In order to handle class format changes any instance
        # provides a version information
        self.class_version: int = 1

        self.xml_state = xml_state

    def add_bundle_format(self, pattern: str):
        version_string = self.xml_state.get_image_version()
        if '.' in version_string:
            (major, minor, patch) = version_string.split(sep='.', maxsplit=2)
        else:
            (major, minor, patch) = (version_string, '', '')
        self.name_tags = result_name_tags(
            N=self.xml_state.xml_data.get_name(),
            P='_'.join(
                self.xml_state.profiles
            ) if self.xml_state.profiles else '',
            A=self.xml_state.host_architecture,
            I='',
            T=self.xml_state.get_build_type_name(),
            M=major,
            m=minor,
            p=patch,
            v=version_string
        )
        self.result_files['bundle_format'] = {
            'pattern': pattern,
            'tags': self.name_tags
        }

    def add(
        self, key: str, filename: str, use_for_bundle: bool = True,
        compress: bool = False, shasum: bool = True
    ) -> None:
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

    def get_results(self) -> Dict[str, result_file_type]:
        """
        Current list of result tuples
        """
        return self.result_files

    def print_results(self) -> None:
        """
        Print results human readable
        """
        if self.result_files:
            log.info('Result files:')
            for key, value in sorted(list(self.result_files.items())):
                if key == 'bundle_format':
                    log.info('--> {0}: {1}'.format(key, value.get('pattern')))
                else:
                    log.info('--> {0}: {1}'.format(key, value.filename))

    def dump(self, filename: str, portable: bool = True) -> None:
        """
        Picke dump this instance to a file

        :param str filename: file path name
        :param bool portable:
            If set to true also create a .json formatted variant
            of the dump file which contains the elements of this
            instance that could be expressed in a portable json
            document. Default is set to: True

        :raises KiwiResultError: if pickle fails to dump :class:`Result`
            instance
        """
        try:
            with open(filename, 'wb') as result:
                pickle.dump(self, result)
            if portable:
                with open(filename + '.json', 'w') as result_portable:
                    result_portable.write(
                        simplejson.dumps(
                            self.result_files, sort_keys=True, indent=4
                        ) + os.linesep
                    )
        except Exception as e:
            raise KiwiResultError(
                'Failed to pickle dump results: %s' % format(e)
            )

    @staticmethod
    def load(filename: str) -> result_type:  # type: ignore
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

    @staticmethod
    def verify_image_size(size_limit: int, filename: str) -> None:
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
