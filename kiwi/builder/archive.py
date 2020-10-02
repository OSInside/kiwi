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

# project
from kiwi.defaults import Defaults
from kiwi.archive.tar import ArchiveTar
from kiwi.system.setup import SystemSetup
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiArchiveSetupError
)

log = logging.getLogger('kiwi')


class ArchiveBuilder:
    """
    **Root archive image builder**

    :param obsject xml_state: Instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: root directory path name
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * xz_options: string of XZ compression parameters
    """
    def __init__(self, xml_state, target_dir, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.requested_archive_type = xml_state.get_build_type_name()
        self.result = Result(xml_state)
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = self._target_file_for('tar.xz')
        self.xz_options = custom_args['xz_options'] if custom_args \
            and 'xz_options' in custom_args else None

        self.runtime_config = RuntimeConfig()

    def create(self):
        """
        Create a root archive tarball

        Build a simple XZ compressed root tarball from the image root tree

        Image types which triggers this builder are:

        * image="tbz"

        :return: result

        :rtype: instance of :class:`Result`
        """
        supported_archives = Defaults.get_archive_image_types()
        if self.requested_archive_type not in supported_archives:
            raise KiwiArchiveSetupError(
                'Unknown archive type: %s' % self.requested_archive_type
            )

        if self.requested_archive_type == 'tbz':
            log.info('Creating XZ compressed tar archive')
            archive = ArchiveTar(
                self._target_file_for('tar')
            )
            archive.create_xz_compressed(
                self.root_dir, xz_options=self.xz_options,
                exclude=Defaults.get_exclude_list_for_root_data_sync()
            )
            self.result.verify_image_size(
                self.runtime_config.get_max_size_constraint(),
                self.filename
            )
            self.result.add(
                key='root_archive',
                filename=self.filename,
                use_for_bundle=True,
                compress=False,
                shasum=True
            )
            self.result.add(
                key='image_packages',
                filename=self.system_setup.export_package_list(
                    self.target_dir
                ),
                use_for_bundle=True,
                compress=False,
                shasum=False
            )
            self.result.add(
                key='image_changes',
                filename=self.system_setup.export_package_changes(
                    self.target_dir
                ),
                use_for_bundle=True,
                compress=True,
                shasum=False
            )
            self.result.add(
                key='image_verified',
                filename=self.system_setup.export_package_verification(
                    self.target_dir
                ),
                use_for_bundle=True,
                compress=False,
                shasum=False
            )
        return self.result

    def _target_file_for(self, suffix):
        return ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + self.xml_state.get_image_version(),
                '.', suffix
            ]
        )
