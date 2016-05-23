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


class BootLoaderTemplateGrub2(object):
    """
    grub2 configuraton file templates
    """
    def __init__(self):
        self.cr = '\n'

        self.header = dedent('''
            # kiwi generated one time grub2 config file
            search ${search_params}
            set default=${default_boot}
            set timeout=${boot_timeout}
        ''').strip() + self.cr

        self.header_hybrid = dedent('''
            set linux=linux
            set initrd=initrd
            if [ "$${grub_cpu}" = "x86_64" -o "$${grub_cpu}" = "i386" ];then
                if [ "$${grub_platform}" = "efi" ]; then
                    set linux=linuxefi
                    set initrd=initrdefi
                fi
            fi
        ''').strip() + self.cr

        self.header_gfxterm = dedent('''
            if [ "$${grub_platform}" = "efi" ]; then
                echo "Please press 't' to show the boot menu on this console"
            fi
            set gfxmode=${gfxmode}
            insmod all_video
            insmod gfxterm
            terminal_output gfxterm
        ''').strip() + self.cr

        self.header_serial = dedent('''
            serial --speed=9600 --unit=0 --word=8 --parity=no --stop=1
            terminal_input serial
            terminal_output serial
        ''').strip() + self.cr

        self.header_theme = dedent('''
            set font=($$root)${bootpath}/unicode.pf2
            if loadfont ($$root)${bootpath}/grub2/themes/${theme}/ascii.pf2;then
                loadfont ($$root)${bootpath}/grub2/themes/${theme}/DejaVuSans-Bold14.pf2
                loadfont ($$root)${bootpath}/grub2/themes/${theme}/DejaVuSans10.pf2
                loadfont ($$root)${bootpath}/grub2/themes/${theme}/DejaVuSans12.pf2
                loadfont ($$root)${bootpath}/grub2/themes/${theme}/ascii.pf2
                set theme=($$root)${bootpath}/grub2/themes/${theme}/theme.txt
            fi
        ''').strip() + self.cr

        self.header_theme_iso = dedent('''
            set font=($$root)/boot/unicode.pf2
            if loadfont ($$root)/boot/grub2/themes/${theme}/ascii.pf2;then
                loadfont ($$root)/boot/grub2/themes/${theme}/DejaVuSans-Bold14.pf2
                loadfont ($$root)/boot/grub2/themes/${theme}/DejaVuSans10.pf2
                loadfont ($$root)/boot/grub2/themes/${theme}/DejaVuSans12.pf2
                loadfont ($$root)/boot/grub2/themes/${theme}/ascii.pf2
                set theme=($$root)/boot/grub2/themes/${theme}/theme.txt
            fi
        ''').strip() + self.cr

        self.menu_entry_console_switch = dedent('''
            if [ "$${grub_platform}" = "efi" ]; then
                hiddenentry "Text mode" --hotkey "t" {
                    set textmode=true
                    terminal_output console
                }
            fi
        ''').strip() + self.cr

        self.menu_entry_hybrid = dedent('''
            menuentry "${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                $$linux ($$root)${bootpath}/${kernel_file} ${boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_entry_multiboot = dedent('''
            menuentry "${title}" --class os --unrestricted {
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                module ${bootpath}/${kernel_file} dummy ${boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + self.cr

        self.menu_entry = dedent('''
            menuentry "${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                linux ($$root)${bootpath}/${kernel_file} ${boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_entry_failsafe_hybrid = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                $$linux ($$root)${bootpath}/${kernel_file} ${failsafe_boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_entry_failsafe_multiboot = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                module ${bootpath}/${kernel_file} dummy ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + self.cr

        self.menu_entry_failsafe = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                linux ($$root)${bootpath}/${kernel_file} ${failsafe_boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_install_entry_hybrid = dedent('''
            menuentry "Install ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                $$linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_install_entry_multiboot = dedent('''
            menuentry "Install -- ${title}" --class os --unrestricted {
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                module ${bootpath}/${kernel_file} dummy cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + self.cr

        self.menu_install_entry = dedent('''
            menuentry "Install ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_install_entry_failsafe_hybrid = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                $$linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_install_entry_failsafe_multiboot = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                module ${bootpath}/${kernel_file} dummy cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + self.cr

        self.menu_install_entry_failsafe = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                echo Loading kernel...
                set gfxpayload=${gfxmode}
                linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + self.cr

        self.menu_iso_harddisk_entry = dedent('''
            menuentry "Boot from Hard Disk" --class os --unrestricted {
                search --set=root --label EFI
                chainloader ($${root})/EFI/BOOT/bootx64.efi
            }
        ''').strip() + self.cr

    def get_disk_template(
        self, failsafe=True, hybrid=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for disk image

        :param bool failsafe: with failsafe true|false
        :param bool hybrid: with hybrid true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += '\n' + self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme
        if hybrid:
            template_data += self.menu_entry_hybrid
            if failsafe:
                template_data += self.menu_entry_failsafe_hybrid
        else:
            template_data += self.menu_entry
            if failsafe:
                template_data += self.menu_entry_failsafe
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_multiboot_disk_template(
        self, failsafe=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for disk image with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme
        template_data += self.menu_entry_multiboot
        if failsafe:
            template_data += self.menu_entry_failsafe_multiboot
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_iso_template(
        self, failsafe=True, hybrid=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for live ISO media

        :param bool failsafe: with failsafe true|false
        :param bool hybrid: with hybrid true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme_iso
        if hybrid:
            template_data += self.menu_entry_hybrid
            if failsafe:
                template_data += self.menu_entry_failsafe_hybrid
        else:
            template_data += self.menu_entry
            if failsafe:
                template_data += self.menu_entry_failsafe
        template_data += self.menu_iso_harddisk_entry
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_multiboot_iso_template(
        self, failsafe=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for live ISO media with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme_iso
        template_data += self.menu_entry_multiboot
        if failsafe:
            template_data += self.menu_entry_failsafe_multiboot
        template_data += self.menu_iso_harddisk_entry
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_install_template(
        self, failsafe=True, hybrid=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for install media

        :param bool failsafe: with failsafe true|false
        :param bool hybrid: with hybrid true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme_iso
        template_data += self.menu_iso_harddisk_entry
        if hybrid:
            template_data += self.menu_install_entry_hybrid
            if failsafe:
                template_data += self.menu_install_entry_failsafe_hybrid
        else:
            template_data += self.menu_install_entry
            if failsafe:
                template_data += self.menu_install_entry_failsafe
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_multiboot_install_template(
        self, failsafe=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for install media with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param string terminal: output terminal name

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
        else:
            template_data += self.header_serial
        template_data += self.header_theme_iso
        template_data += self.menu_iso_harddisk_entry
        template_data += self.menu_install_entry_multiboot
        if failsafe:
            template_data += self.menu_install_entry_failsafe_multiboot
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)
