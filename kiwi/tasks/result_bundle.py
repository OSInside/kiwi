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
"""
usage: kiwi result bundle -h | --help
       kiwi result bundle --target-dir=<directory> --id=<bundle_id> --bundle-dir=<directory>
       kiwi result bundle help

commands:
    bundle
        create result bundle from the image build results in the
        specified target directory. Each result image will contain
        the specified bundle identifier as part of its filename.
        Uncompressed image files will also become xz compressed
        and a sha sum will be created from every result image.

options:
    --bundle-dir=<directory>
        directory to store the bundle results

    --id=<bundle_id>
        the bundle id. A free form text appended to the version
        information of the result image filename

    --target-dir=<directory>
        the target directory to expect image build results
"""
from collections import OrderedDict
import os

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.system.result import Result
from kiwi.logger import log
from kiwi.path import Path
from kiwi.utils.compress import Compress
from kiwi.utils.checksum import Checksum
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiBundleError
)


class ResultBundleTask(CliTask):
    """
    Implements result bundler

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Create result bundle from the image build results in the
        specified target directory. Each result image will contain
        the specified bundle identifier as part of its filename.
        Uncompressed image files will also become xz compressed
        and a sha sum will be created from every result image
        """
        self.manual = Help()
        if self._help():
            return

        # load serialized result object from target directory
        result_directory = os.path.normpath(self.command_args['--target-dir'])
        bundle_directory = os.path.normpath(self.command_args['--bundle-dir'])
        if result_directory == bundle_directory:
            raise KiwiBundleError(
                'Bundle directory must be different from target directory'
            )

        log.info(
            'Bundle build results from %s', result_directory
        )
        result = Result.load(
            result_directory + '/kiwi.result'
        )
        image_version = result.xml_state.get_image_version()
        ordered_results = OrderedDict(sorted(result.get_results().items()))

        # hard link bundle files, compress and build checksum
        if not os.path.exists(bundle_directory):
            Path.create(bundle_directory)
        for result_file in list(ordered_results.values()):
            if result_file.use_for_bundle:
                bundle_file_basename = os.path.basename(result_file.filename)
                # The bundle id is only taken into account for image results
                # which contains the image version in its nane
                bundle_file_basename = bundle_file_basename.replace(
                    image_version,
                    image_version + '-' + self.command_args['--id']
                )
                log.info('Creating %s', bundle_file_basename)
                bundle_file = ''.join(
                    [bundle_directory, '/', bundle_file_basename]
                )
                checksum_file = ''.join(
                    [bundle_directory, '/', bundle_file_basename, '.sha256']
                )
                Command.run(
                    [
                        'cp', result_file.filename, bundle_file
                    ]
                )
                if result_file.compress:
                    log.info('--> XZ compressing')
                    compress = Compress(bundle_file)
                    compress.xz()
                    bundle_file = compress.compressed_filename
                    checksum_file = compress.compressed_filename + '.sha256'
                if result_file.shasum:
                    log.info('--> Creating SHA 256 sum')
                    checksum = Checksum(bundle_file)
                    with open(checksum_file, 'w') as shasum:
                        shasum.write(checksum.sha256())

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::result::bundle')
        else:
            return False
        return self.manual
