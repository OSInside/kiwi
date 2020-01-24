# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
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
import re

# project
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.rpm import Rpm


class RpmDataBase:
    """
    **Setup RPM database configuration**
    """
    def __init__(self, root_dir, macro_file=None):
        self.rpmdb_host = Rpm()
        self.rpmdb_image = Rpm(root_dir, macro_file)
        self.root_dir = root_dir

    def has_rpm(self):
        """
        Check if rpmdb binary was found in root_dir to indicate
        that the rpm system is present.
        """
        rpm_bin = Path.which(
            'rpmdb', root_dir=self.root_dir, access_mode=os.X_OK
        )
        if not rpm_bin:
            return False
        return True

    def rebuild_database(self):
        """
        Rebuild image rpm database taking current macro setup into account
        """
        Command.run(
            ['chroot', self.root_dir, 'rpmdb', '--rebuilddb']
        )

    def init_database(self):
        Command.run(
            ['rpm', '--root', self.root_dir, '--initdb']
        )

    def set_macro_from_string(self, setting):
        """
        Setup given macro setting in image rpm configuration.
        The following format for the setting is expected:

            macro_base_key_name%macro_value.

        If this expression is not matched the macro setup will be
        skipped. Please note the macro_base_key_name includes
        the name of the macro as rpm expects it exlcuding the
        leading '%' character.

        Also note macro defintions must happen before calling
        set_database_* methods in order to become effective

        :param string setting: macro key and value as one string
        """
        match = re.match('(.*)%(.*)', setting)
        if match:
            self.rpmdb_image.set_config_value(
                match.group(1), match.group(2)
            )

    def write_config(self):
        self.rpmdb_image.write_config()

    def import_signing_key_to_image(self, key):
        """
        Import the given signing key to the image rpm database
        """
        Command.run(
            [
                'rpm', '--root', self.root_dir, '--import', key,
                '--dbpath', self.rpmdb_host.expand_query('%_dbpath')
            ]
        )

    def set_database_to_host_path(self):
        """
        Setup dbpath to point to the host rpm dbpath configuration
        and write the configuration file
        """
        self.rpmdb_image.set_config_value(
            '_dbpath', self.rpmdb_host.get_query('_dbpath')
        )
        self.rpmdb_image.write_config()

    def link_database_to_host_path(self):
        """
        Create a link from host database location to image database
        location. The link is only created if both locations differ
        and if the host database location does not exist.
        """
        rpm_host_dbpath = self.rpmdb_host.expand_query('%_dbpath')
        rpm_image_dbpath = self.rpmdb_image.expand_query('%_dbpath')
        if rpm_host_dbpath != rpm_image_dbpath:
            root_rpm_host_dbpath = os.path.normpath(
                os.sep.join([self.root_dir, rpm_host_dbpath])
            )
            if not os.path.exists(root_rpm_host_dbpath):
                Path.create(os.path.dirname(root_rpm_host_dbpath))
                host_to_root = ''.join(
                    '../' for i in os.path.dirname(
                        rpm_host_dbpath
                    ).lstrip(os.sep).split(os.sep)
                )
                Command.run(
                    [
                        'ln', '-s', os.path.normpath(
                            os.sep.join([host_to_root, rpm_image_dbpath])
                        ), root_rpm_host_dbpath
                    ]
                )

    def set_database_to_image_path(self):
        """
        Setup dbpath to point to the image rpm dbpath configuration
        Rebuild the database such that it gets moved to the standard
        path and delete KIWI's custom macro setup
        """
        self.rpmdb_image.wipe_config()
        rpm_image_dbpath = self.rpmdb_image.expand_query('%_dbpath')
        rpm_host_dbpath = self.rpmdb_host.expand_query('%_dbpath')
        if rpm_image_dbpath != rpm_host_dbpath:
            root_rpm_image_dbpath = os.path.normpath(
                os.sep.join([self.root_dir, rpm_image_dbpath])
            )
            root_rpm_host_dbpath = os.path.normpath(
                os.sep.join([self.root_dir, rpm_host_dbpath])
            )

            if os.path.islink(root_rpm_host_dbpath):
                self.rebuild_database()
                return

            if os.path.islink(root_rpm_image_dbpath):
                os.unlink(root_rpm_image_dbpath)
            else:
                Path.wipe(root_rpm_image_dbpath)

            self.rpmdb_image.set_config_value(
                '_dbpath', rpm_host_dbpath
            )
            self.rpmdb_image.set_config_value(
                '_dbpath_rebuild', self.rpmdb_image.get_query('_dbpath')
            )

            self.rpmdb_image.write_config()
            self.rebuild_database()
            self.rpmdb_image.wipe_config()

            root_rpm_alternatives = os.sep.join(
                [root_rpm_host_dbpath, 'alternatives']
            )
            if os.path.exists(root_rpm_alternatives):
                Command.run(
                    ['mv', root_rpm_alternatives, root_rpm_image_dbpath]
                )

            Path.wipe(root_rpm_host_dbpath)
