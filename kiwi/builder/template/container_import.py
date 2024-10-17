# Copyright (c) 2024 SUSE LLC.  All rights reserved.
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
from typing import List
from string import Template
from textwrap import dedent


class BuilderTemplateSystemdUnit:
    """
    **systemd unit file templates**
    """
    def __init__(self):
        self.unit = dedent('''
            # kiwi generated unit file
            [Unit]
            Description=Import Local Container(s)
        ''').strip() + os.linesep

        self.service = dedent('''
            [Service]
            Type=oneshot
        ''').strip() + os.linesep

        self.install = dedent('''
            [Install]
            WantedBy=multi-user.target
        ''').strip() + os.linesep

    def get_container_import_template(
        self, container_files: List[str], load_commands: List[List[str]],
        after: List[str]
    ):
        template_data = self.unit
        for container_file in container_files:
            template_data += 'ConditionPathExists={0}{1}'.format(
                container_file, os.linesep
            )
        if after:
            template_data += 'After={0}{1}'.format(
                ' '.join(after), os.linesep
            )
        template_data += self.service
        for load_command in load_commands:
            template_data += 'ExecStart={0}{1}'.format(
                ' '.join(load_command), os.linesep
            )
        for container_file in container_files:
            template_data += 'ExecStartPost=/bin/rm -f {0}{1}'.format(
                container_file, os.linesep
            )
        template_data += self.install
        return Template(template_data)
