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
usage: kiwi-ng result bundle -h | --help
       kiwi-ng result bundle --target-dir=<directory> --id=<bundle_id> --bundle-dir=<directory>
           [--bundle-format=<format>]
           [--zsync-source=<download_location>]
           [--package-as-rpm]
       kiwi-ng result bundle help

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
    --zsync-source=<download_location>
        specify the download location from which the bundle file(s)
        can be fetched from. The information is effective if zsync is
        used to sync the bundle. The zsync control file is only created
        for those bundle files which are marked for compression because
        in a kiwi build only those are meaningful for a partial binary
        file download. It is expected that all files from a bundle
        are placed to the same download location
    --package-as-rpm
        Take all result files and create an rpm package out of it
    --bundle-format=<format>
        specify the bundle format to create the bundle.
        If provided this setting will overwrite an eventually
        provided bundle_format attribute from the main
        image description
"""
from collections import OrderedDict
from textwrap import dedent
from typing import List
import logging
import glob
import os

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.system.result import (
    Result, result_file_type
)
from kiwi.path import Path
from kiwi.utils.compress import Compress
from kiwi.utils.checksum import Checksum
from kiwi.privileges import Privileges
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiBundleError
)

log = logging.getLogger('kiwi')


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

        if self.command_args['--package-as-rpm']:
            Privileges.check_for_root_permissions()

        # load serialized result object from target directory
        result_directory = os.path.abspath(self.command_args['--target-dir'])
        bundle_directory = os.path.abspath(self.command_args['--bundle-dir'])
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

        if self.command_args['--bundle-format']:
            result.add_bundle_format(self.command_args['--bundle-format'])

        image_version = result.xml_state.get_image_version()
        image_name = result.xml_state.xml_data.get_name()
        image_description = result.xml_state.get_description_section()
        ordered_results = OrderedDict(sorted(result.get_results().items()))

        # hard link bundle files, compress and build checksum
        if self.command_args['--package-as-rpm']:
            Path.wipe(bundle_directory)
        if not os.path.exists(bundle_directory):
            Path.create(bundle_directory)

        bundle_file_format_name = ''
        if 'bundle_format' in ordered_results:
            bundle_format = ordered_results['bundle_format']
            tags = bundle_format['tags']
            bundle_file_format_name = bundle_format['pattern']
            # Insert image name
            bundle_file_format_name = bundle_file_format_name.replace(
                '%N', tags.N
            )
            # Insert Concatenated profile name (_)
            bundle_file_format_name = bundle_file_format_name.replace(
                '%P', tags.P
            )
            # Insert Architecture name
            bundle_file_format_name = bundle_file_format_name.replace(
                '%A', tags.A
            )
            # Insert Image build type name
            bundle_file_format_name = bundle_file_format_name.replace(
                '%T', tags.T
            )
            # Insert Image Major version number
            bundle_file_format_name = bundle_file_format_name.replace(
                '%M', format(tags.M)
            )
            # Insert Image Minor version number
            bundle_file_format_name = bundle_file_format_name.replace(
                '%m', format(tags.m)
            )
            # Insert Image Patch version number
            bundle_file_format_name = bundle_file_format_name.replace(
                '%p', format(tags.p)
            )
            # Insert Version string
            bundle_file_format_name = bundle_file_format_name.replace(
                '%v', format(tags.v)
            )
            # Insert Bundle ID
            bundle_file_format_name = bundle_file_format_name.replace(
                '%I', self.command_args['--id']
            )
            del ordered_results['bundle_format']

        # copy result files
        origin_files = []
        copied_files = []
        for result_file in list(ordered_results.values()):
            if result_file.use_for_bundle:
                bundle_file_basename = self._get_bundle_file_basename(
                    result, result_file, bundle_file_format_name
                )
                log.info('Creating %s', bundle_file_basename)
                bundle_file = ''.join(
                    [bundle_directory, '/', bundle_file_basename]
                )
                Command.run(
                    [
                        'cp', result_file.filename, bundle_file
                    ]
                )
                copied_files.append(bundle_file)
                result_file_basename = os.path.basename(result_file.filename)
                if result_file_basename != bundle_file_basename:
                    symlink_orignal_name = f'{bundle_directory}/{result_file_basename}'
                    if os.path.islink(symlink_orignal_name):
                        os.unlink(symlink_orignal_name)
                    os.symlink(bundle_file, symlink_orignal_name)
                    origin_files.append(symlink_orignal_name)

        # check and fix file references due to possible bundle_format renames
        for origin_file in origin_files:
            origin_file_basename = os.path.basename(origin_file)
            bundle_file_basename = os.path.basename(os.readlink(origin_file))
            log.info(f'Checking file references for {origin_file_basename}')
            for result_file in copied_files:
                if 'text' in Command.run(['file', result_file]).output:
                    log.info(f'--> {result_file}')
                    Command.run(
                        [
                            'sed', '-ie',
                            f's/{origin_file_basename}/{bundle_file_basename}/g',
                            result_file
                        ]
                    )
                    os.unlink(f'{result_file}e')
            os.unlink(origin_file)

        # finalize result data, checksums, compressions
        for result_file in list(ordered_results.values()):
            if result_file.use_for_bundle:
                bundle_file_basename = self._get_bundle_file_basename(
                    result, result_file, bundle_file_format_name
                )
                log.info(f'Finalizing {bundle_file_basename}')
                bundle_file = ''.join(
                    [bundle_directory, '/', bundle_file_basename]
                )
                if result_file.compress:
                    log.info('--> Compressing')
                    compress = Compress(bundle_file)
                    bundle_file = compress.xz(self.runtime_config.get_xz_options())

                if self.command_args['--zsync-source'] and result_file.shasum:
                    # Files with a checksum are considered to be image files
                    # and are therefore eligible to be provided via the
                    # requested Partial/differential file download based on
                    # zsync
                    zsyncmake = Path.which('zsyncmake', access_mode=os.X_OK)
                    if zsyncmake:
                        log.info('--> Creating zsync control file')
                        Command.run(
                            [
                                zsyncmake, '-e', '-u', os.sep.join(
                                    [
                                        self.command_args['--zsync-source'],
                                        os.path.basename(bundle_file)
                                    ]
                                ), '-o', bundle_file + '.zsync', bundle_file
                            ]
                        )
                    else:
                        log.warning(
                            '--> zsyncmake missing, zsync setup skipped'
                        )

                if result_file.shasum:
                    log.info('--> Creating SHA 256 sum')
                    checksum = Checksum(bundle_file)
                    with open(bundle_file + '.sha256', 'w') as shasum:
                        shasum.write(
                            '{0}  {1}{2}'.format(
                                checksum.sha256(),
                                os.path.basename(bundle_file),
                                os.linesep
                            )
                        )

        if self.command_args['--package-as-rpm']:
            ResultBundleTask._build_rpm_package(
                bundle_directory,
                bundle_file_format_name or image_name,
                image_version,
                image_description.specification,
                list(glob.iglob(f'{bundle_directory}/*'))
            )

    def _get_bundle_file_basename(
        self, result: Result, result_file: result_file_type,
        bundle_file_format_name: str
    ) -> str:
        image_version = result.xml_state.get_image_version()
        image_name = result.xml_state.xml_data.get_name()
        if '.tar.' in result_file.filename:
            extension = f'tar.{result_file.filename.split(".").pop()}'
        elif '.vagrant.' in result_file.filename:
            extension = f'vagrant.{".".join(result_file.filename.split(".")[-2:])}'
        else:
            extension = result_file.filename.split('.').pop()
        if bundle_file_format_name:
            bundle_file_basename = '.'.join(
                [bundle_file_format_name, extension]
            )
        else:
            bundle_file_basename = os.path.basename(
                result_file.filename
            )
            # The bundle id is only taken into account for image results
            # which contains the image version appended in its file name
            part_name = list(bundle_file_basename.partition(image_name))
            bundle_file_basename = ''.join(
                [
                    part_name[0], part_name[1],
                    part_name[2].replace(
                        image_version,
                        image_version + '-' + self.command_args['--id']
                    )
                ]
            )
        return bundle_file_basename

    @staticmethod
    def _build_rpm_package(
        bundle_directory: str, image_name: str, image_version: str,
        description_text, filenames: List[str]
    ) -> None:
        source_links = []
        for source_file in filenames:
            source_links.append(
                ' '.join(
                    [
                        'ln', '%{_sourcedir}/' + os.path.basename(source_file),
                        '%{buildroot}' + f'/var/tmp/{image_name}'
                    ]
                )
            )
        spec_file_name = os.path.join(bundle_directory, f'{image_name}.spec')
        spec_data = dedent('''
            %global _sourcedir %(pwd)
            %global _rpmdir .

            Url:            https://osinside.github.io/kiwi
            Name:           {name}
            Summary:        {name}
            Version:        {version}
            Release:        0
            Group:          %{{sysgroup}}
            License:        GPL-3.0-or-later
            BuildRoot:      %{{_tmppath}}/%{{name}}-%{{version}}-build
            BuildArch:      noarch

            %description
            {description}

            %prep

            %build

            %install
            install -d -m 755 %{{buildroot}}/var/tmp/{name}

            {source_links}

            %clean
            rm -rf %{{buildroot}}

            %files
            %defattr(-, root, root)
            /var/tmp/{name}

            %changelog
        ''').format(
            name=image_name,
            version=image_version,
            description=description_text,
            source_links=os.linesep.join(source_links)
        )
        with open(spec_file_name, 'w') as spec:
            spec.write(spec_data)
        os.chdir(bundle_directory)
        log.info('Creating rpm package...')
        Command.run(
            [
                'rpmbuild', '--nodeps', '--nocheck', '--rmspec',
                '-bb', spec_file_name
            ]
        )
        for source_file in filenames:
            os.unlink(source_file)
        Command.run(
            [
                'bash', '-c', 'mv noarch/*.rpm . && rmdir noarch'
            ]
        )

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::result::bundle')
        else:
            return False
        return self.manual
