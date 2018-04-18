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
from string import Template
from textwrap import dedent


class BootLoaderTemplateZipl(object):
    """
    **zipl configuraton file templates**
    """
    def __init__(self):
        self.cr = '\n'

        self.header = dedent('''
            # kiwi generated zipl config file
            [defaultboot]
            defaultmenu = menu

            :menu
                targetbase = ${device}
                targettype = ${target_type}
                targetblocksize = ${blocksize}
                targetoffset = ${offset}
                targetgeometry = ${geometry}
                default = ${default_boot}
                prompt  = 1
                target  = ${bootpath}
                timeout = ${boot_timeout}
        ''').strip() + self.cr

        self.activate_menu_entry = \
            '    1 = ${title}' + self.cr
        self.activate_failsafe_menu_entry = \
            '    2 = Failsafe_--_${title}' + self.cr

        self.menu_entry = dedent('''
            [${title}]
                image   = ${bootpath}/${kernel_file}
                target  = ${bootpath}
                ramdisk = ${bootpath}/${initrd_file},0x4000000
                parameters = "${boot_options}"
        ''').strip() + self.cr

        self.menu_entry_failsafe = dedent('''
            [Failsafe_--_${title}]
                image   = ${bootpath}/${kernel_file}
                target  = ${bootpath}
                ramdisk = ${bootpath}/${initrd_file},0x4000000
                parameters = "${failsafe_boot_options}"
        ''').strip() + self.cr

    def get_template(self, failsafe=True):
        """
        Bootloader configuration template for disk boot

        :param bool failsafe: with failsafe true|false

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        template_data += self.activate_menu_entry
        if failsafe:
            template_data += self.activate_failsafe_menu_entry
        template_data += self.cr
        template_data += self.menu_entry
        if failsafe:
            template_data += self.cr
            template_data += self.menu_entry_failsafe
        return Template(template_data)
