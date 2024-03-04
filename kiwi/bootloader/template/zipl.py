# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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


class BootLoaderTemplateZipl:
    """
    **zipl configuraton file templates**
    """
    def __init__(self):
        self.cr = '\n'

        self.main_conf = dedent('''
            [defaultboot]
            defaultauto
            prompt=1
            target=${bootpath}
            ${targetbase}
            targettype=${targettype}
            targetblocksize=${targetblocksize}
            targetoffset=${targetoffset}
            ${targetgeometry}
            timeout=${boot_timeout}
            secure=auto
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
        template_data = self.main_conf
        return Template(template_data)

    def get_entry_template(self) -> Template:
        """
        Bootloader entry configuration template

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.entry
        return Template(template_data)
