# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
from string import Template
from textwrap import dedent


class BootLoaderTemplateSystemdBoot:
    """
    **systemd-boot configuraton file templates**
    """
    def __init__(self):
        self.cr = '\n'

        self.loader = dedent('''
            # kiwi generated loader config file
            console-mode max
            editor  no
        ''').strip() + self.cr

        self.timeout = dedent('''
            timeout ${boot_timeout}
        ''').strip() + self.cr

        self.entry = dedent('''
            title ${title}
            options ${boot_options}
            linux ${kernel_file}
            initrd ${initrd_file}
        ''').strip() + self.cr

    def get_loader_template(self) -> Template:
        """
        Bootloader main configuration template

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.loader
        template_data += self.timeout
        return Template(template_data)

    def get_entry_template(self) -> Template:
        """
        Bootloader entry configuration template

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.entry
        return Template(template_data)
