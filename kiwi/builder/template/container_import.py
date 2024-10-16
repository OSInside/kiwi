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
from string import Template
from textwrap import dedent


class BuilderTemplateSystemdUnit:
    """
    **systemd unit file templates**
    """
    def get_container_import_template(self) -> Template:
        template_data = dedent('''
            # kiwi generated unit file
            [Unit]
            Description=Import Local Container: ${container_name}
            ConditionPathExists=${container_file}

            [Service]
            Type=oneshot
            ExecStart=${load_command}
            ExecStartPost=/bin/rm ${container_file}

            [Install]
            WantedBy=multi-user.target
        ''').strip() + os.linesep
        return Template(template_data)
