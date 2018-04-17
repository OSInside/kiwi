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


class BootLoaderTemplateIsoLinux(object):
    """
    **isolinux configuraton file templates**
    """
    def __init__(self):
        self.cr = '\n'

        self.install_message = dedent('''
            Welcome !

            Boot_from_Hard_Disk
            Install_${title}
            Failsafe_--_Install_${title}


            Have a lot of fun...
        ''').strip() + self.cr

        self.message = dedent('''
            Welcome !

            ${title}
            Failsafe_${title}


            Have a lot of fun...
        ''').strip() + self.cr

        self.serial = dedent('''
            serial 0 9600
        ''')

        self.header = dedent('''
            # kiwi generated isolinux config file
            implicit 1
            prompt   1
            timeout  ${boot_timeout}
            display isolinux.msg
            default ${default_boot}
        ''').strip() + self.cr

        self.ui_theme = dedent('''
            ui gfxboot bootlogo isolinux.msg
            MENU RESOLUTION ${gfxmode}
        ''').strip() + self.cr

        self.ui_plain = dedent('''
            ui menu.c32
        ''').strip() + self.cr

        self.menu_harddisk_entry = dedent('''
            label Boot_from_Hard_Disk
                localboot 0x80
        ''').strip() + self.cr

        self.menu_install_entry_multiboot = dedent('''
            label Install_${title}
                kernel mboot.c32
                append ${hypervisor} --- ${kernel_file} ${boot_options} cdinst=1 showopts --- ${initrd_file} showopts
        ''').strip() + self.cr

        self.menu_install_entry_failsafe_multiboot = dedent('''
            label Failsafe_--_Install_${title}
                kernel mboot.c32
                append ${hypervisor} --- ${kernel_file} ${failsafe_boot_options} cdinst=1 showopts --- ${initrd_file} showopts
        ''').strip() + self.cr

        self.menu_entry_multiboot = dedent('''
            label ${title}
                kernel mboot.c32
                append ${hypervisor} --- ${kernel_file} ${boot_options} showopts --- ${initrd_file} showopts
        ''').strip() + self.cr

        self.menu_entry_failsafe_multiboot = dedent('''
            label Failsafe_--_${title}
                kernel mboot.c32
                append ${hypervisor} --- ${kernel_file} ${failsafe_boot_options} showopts --- ${initrd_file} showopts
        ''').strip() + self.cr

        self.menu_mediacheck_entry_multiboot = dedent('''
            label Mediacheck
                kernel mboot.c32
                append ${hypervisor} --- ${kernel_file} ${boot_options} mediacheck=1 plymouth.enable=0 showopts --- ${initrd_file} showopts
        ''').strip() + self.cr

        self.menu_install_entry = dedent('''
            label Install_${title}
                kernel ${kernel_file}
                append initrd=${initrd_file} ${boot_options} cdinst=1 showopts
        ''').strip() + self.cr

        self.menu_install_entry_failsafe = dedent('''
            label Failsafe_--_Install_${title}
                kernel ${kernel_file}
                append initrd=${initrd_file} ${failsafe_boot_options} cdinst=1 showopts
        ''').strip() + self.cr

        self.menu_entry = dedent('''
            label ${title}
                kernel ${kernel_file}
                append initrd=${initrd_file} ${boot_options} showopts
        ''').strip() + self.cr

        self.menu_entry_failsafe = dedent('''
            label Failsafe_--_${title}
                kernel ${kernel_file}
                append initrd=${initrd_file} ${failsafe_boot_options} showopts
        ''').strip() + self.cr

        self.menu_mediacheck_entry = dedent('''
            label Mediacheck
                kernel ${kernel_file}
                append initrd=${initrd_file} ${boot_options} mediacheck=1 plymouth.enable=0 showopts
        ''').strip() + self.cr

    def get_install_message_template(self):
        """
        Bootloader template for text message file in install mode.
        isolinux displays this as menu if no graphics mode can be
        initialized

        :return: instance of :class:`Template`

        :rtype: Template
        """
        return Template(self.install_message)

    def get_message_template(self):
        """
        Bootloader template for text message file. isolinux
        displays this as menu if no graphics mode can be initialized

        :return: instance of :class:`Template`

        :rtype: Template
        """
        return Template(self.message)

    def get_template(
        self, failsafe=True, with_theme=True, terminal=None, checkiso=False
    ):
        """
        Bootloader configuration template for live media

        :param bool failsafe: with failsafe true|false
        :param bool with_theme: with graphics theme true|false

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'serial':
            template_data += self.serial
            with_theme = False
        if with_theme:
            template_data += self.ui_theme
        else:
            template_data += self.ui_plain
        template_data += self.menu_entry
        if failsafe:
            template_data += self.menu_entry_failsafe
        template_data += self.menu_harddisk_entry
        if checkiso:
            template_data += self.menu_mediacheck_entry
        return Template(template_data)

    def get_multiboot_template(
        self, failsafe=True, with_theme=True, terminal=None, checkiso=False
    ):
        """
        Bootloader configuration template for live media with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param bool with_theme: with graphics theme true|false

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'serial':
            template_data += self.serial
            with_theme = False
        if with_theme:
            template_data += self.ui_theme
        else:
            template_data += self.ui_plain
        template_data += self.menu_entry_multiboot
        if failsafe:
            template_data += self.menu_entry_failsafe_multiboot
        template_data += self.menu_harddisk_entry
        if checkiso:
            template_data += self.menu_mediacheck_entry_multiboot
        return Template(template_data)

    def get_install_template(
        self, failsafe=True, with_theme=True, terminal=None
    ):
        """
        Bootloader configuration template for install media

        :param bool failsafe: with failsafe true|false
        :param bool with_theme: with graphics theme true|false

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'serial':
            template_data += self.serial
            with_theme = False
        if with_theme:
            template_data += self.ui_theme
        else:
            template_data += self.ui_plain
        template_data += self.menu_harddisk_entry
        template_data += self.menu_install_entry
        if failsafe:
            template_data += self.menu_install_entry_failsafe
        return Template(template_data)

    def get_multiboot_install_template(
        self, failsafe=True, with_theme=True, terminal=None
    ):
        """
        Bootloader configuration template for install media with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param bool with_theme: with graphics theme true|false

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'serial':
            template_data += self.serial
            with_theme = False
        if with_theme:
            template_data += self.ui_theme
        else:
            template_data += self.ui_plain
        template_data += self.menu_harddisk_entry
        template_data += self.menu_install_entry_multiboot
        if failsafe:
            template_data += self.menu_install_entry_failsafe_multiboot
        return Template(template_data)
