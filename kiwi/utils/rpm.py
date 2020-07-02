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
from kiwi.defaults import Defaults
from kiwi.path import Path


class Rpm:
    """
    **Helper methods to handle the rpm database configuration**
    """
    def __init__(self, root_dir=None, macro_file=None):
        self.root_dir = root_dir
        self.config = []
        self.custom_config = []
        self.macro_path = os.sep.join(
            [
                self.root_dir or '', Defaults.get_custom_rpm_macros_path()
            ]
        )
        self.macro_file = os.sep.join(
            [
                self.macro_path,
                macro_file if macro_file else
                Defaults.get_custom_rpm_bootstrap_macro_name()
            ]
        )

    def expand_query(self, key):
        """
        Query database configuration and expand it
        """
        if self.root_dir:
            rpmdb_call = Command.run(
                ['chroot', self.root_dir, 'rpm', '-E', key]
            )
        else:
            rpmdb_call = Command.run(
                ['rpm', '-E', key]
            )
        return rpmdb_call.output.strip()

    def get_query(self, key):
        """
        Query database configuration

        Extract the first match for the given key. The method
        expects the format of entries to match the regular
        expression: '.*key[\t ]+value'

        :param string key: query key name

        :returns: match or None if there isn't any match

        :rtype: string | None
        """
        if not self.config:
            self.config = self._read_macro_configuration()
        item_list = list(
            filter(lambda item: key in item, self.config)
        )
        for item in item_list:
            match = re.match('.*{0}[\t ]+(.*)'.format(key), item)
            if match:
                return match.group(1)

    def set_config_value(self, key, value):
        """
        Set custom database configuration key/value pair

        :param string key: key name
        :param string value: key value name
        """
        self.custom_config.append('%{0}\t{1}'.format(key, value))

    def write_config(self):
        """
        Write custom database configuration

        Write bootstrap macro file to the custom rpm macros path
        """
        if self.custom_config:
            Path.create(self.macro_path)
            with open(self.macro_file, 'w') as macro:
                for entry in self.custom_config:
                    macro.write('{0}{1}'.format(entry, os.linesep))

    def wipe_config(self):
        """
        Delete custom database configuration
        """
        Path.wipe(self.macro_file)

    def _read_macro_configuration(self):
        """
        Read rpm database macro and configuration setup

        Please note we intentionally don't use 'rpm -E' here because
        it tries to expand the complete macro and if that is not
        possible it returns with the given unexpanded macro. There
        is no way to detect if the macro really existed or not.
        In addition for the use case of this class the macro should
        be read as it was configured and not its expanded form.
        """
        if self.root_dir:
            rpmdb_call = Command.run(
                ['chroot', self.root_dir, 'rpmdb', '--showrc']
            )
        else:
            rpmdb_call = Command.run(
                ['rpmdb', '--showrc']
            )
        return rpmdb_call.output.split(os.linesep)
