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
import os
from string import Template
from textwrap import dedent


class BootLoaderTemplateGrub2(object):
    """
    **grub2 configuraton file templates**
    """
    def __init__(self):
        self.header = dedent('''
            # kiwi generated one time grub2 config file
            set btrfs_relative_path="y"
            export btrfs_relative_path
            search ${search_params}
            set default=${default_boot}
            set timeout=${boot_timeout}
            if [ -n "$$extra_cmdline" ]; then
              submenu "Bootable snapshot $$snapshot_num" {
                menuentry "If OK, run snapper rollback and reboot." { true; }
              }
            fi
        ''').strip() + os.linesep

        self.header_hybrid = dedent('''
            set linux=linux
            set initrd=initrd
            if [ "$${grub_cpu}" = "x86_64" -o "$${grub_cpu}" = "i386" ];then
                if [ "$${grub_platform}" = "efi" ]; then
                    set linux=linuxefi
                    set initrd=initrdefi
                fi
            fi
        ''').strip() + os.linesep

        self.header_gfxterm = dedent('''
            if [ "$${grub_platform}" = "efi" ]; then
                echo "Please press 't' to show the boot menu on this console"
            fi
            set gfxmode=${gfxmode}
            terminal_output gfxterm
        ''').strip() + os.linesep

        self.header_serial = dedent('''
            serial --speed=9600 --unit=0 --word=8 --parity=no --stop=1
            terminal_input serial
            terminal_output serial
        ''').strip() + os.linesep

        self.header_textconsole = dedent('''
            terminal_input console
            terminal_output console
        ''').strip() + os.linesep

        self.fonts = dedent('''
            set font=($$root)${bootpath}/unicode.pf2
            set ascii_font=${boot_directory_name}/themes/${theme}/ascii.pf2
            set sans_bold_14_font=${boot_directory_name}/themes/${theme}/DejaVuSans-Bold14.pf2
            set sans_10_font=${boot_directory_name}/themes/${theme}/DejaVuSans10.pf2
            set sans_12_font=${boot_directory_name}/themes/${theme}/DejaVuSans12.pf2
        ''').strip() + os.linesep

        self.header_theme = self.fonts + dedent('''
            if [ -f $${font} ];then
                loadfont $${font}
            fi
            if [ -f ($$root)${bootpath}/$${ascii_font} ];then
                loadfont ($$root)${bootpath}/$${ascii_font}
            fi
            if [ -f ($$root)${bootpath}/$${sans_bold_14_font} ];then
                loadfont ($$root)${bootpath}/$${sans_bold_14_font}
            fi
            if [ -f ($$root)${bootpath}/$${sans_10_font} ];then
                loadfont ($$root)${bootpath}/$${sans_10_font}
            fi
            if [ -f ($$root)${bootpath}/$${sans_12_font} ];then
                loadfont ($$root)${bootpath}/$${sans_12_font}
            fi
            if [ -f ($$root)${bootpath}/${boot_directory_name}/themes/${theme}/theme.txt ];then
                set theme=($$root)${bootpath}/${boot_directory_name}/themes/${theme}/theme.txt
                export theme
            fi
        ''').strip() + os.linesep

        self.header_theme_iso = self.fonts + dedent('''
            if [ -f $${font} ];then
                loadfont $${font}
            fi
            if [ -f ($$root)/boot/$${ascii_font} ];then
                loadfont ($$root)/boot/$${ascii_font}
            fi
            if [ -f ($$root)/boot/$${sans_bold_14_font} ];then
                loadfont ($$root)/boot/$${sans_bold_14_font}
            fi
            if [ -f ($$root)/boot/$${sans_10_font} ];then
                loadfont ($$root)/boot/$${sans_10_font}
            fi
            if [ -f ($$root)/boot/$${sans_12_font} ];then
                loadfont ($$root)/boot/$${sans_12_font}
            fi
            if [ -f ($$root)/boot/${boot_directory_name}/themes/${theme}/theme.txt ];then
                set theme=($$root)/boot/${boot_directory_name}/themes/${theme}/theme.txt
            fi
        ''').strip() + os.linesep

        self.menu_entry_boot_snapshots = dedent('''
            if [ -f "/.snapshots/grub-snapshot.cfg" ]; then
                source "/.snapshots/grub-snapshot.cfg"
            fi
        ''').strip() + os.linesep

        self.menu_entry_console_switch = dedent('''
            if [ "$${grub_platform}" = "efi" ]; then
                hiddenentry "Text mode" --hotkey "t" {
                    set textmode=true
                    terminal_output console
                }
            fi
        ''').strip() + os.linesep

        self.menu_entry_hybrid = dedent('''
            menuentry "${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                $$linux ($$root)${bootpath}/${kernel_file} $${extra_cmdline} ${boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_entry_multiboot = dedent('''
            menuentry "${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                module ${bootpath}/${kernel_file} dummy ${boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + os.linesep

        self.menu_entry = dedent('''
            menuentry "${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                linux ($$root)${bootpath}/${kernel_file} $${extra_cmdline} ${boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_entry_failsafe_hybrid = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                $$linux ($$root)${bootpath}/${kernel_file} $${extra_cmdline} ${failsafe_boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_entry_failsafe_multiboot = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                module ${bootpath}/${kernel_file} dummy ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + os.linesep

        self.menu_entry_failsafe = dedent('''
            menuentry "Failsafe -- ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                linux ($$root)${bootpath}/${kernel_file} $${extra_cmdline} ${failsafe_boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_install_entry_hybrid = dedent('''
            menuentry "Install ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                $$linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_install_entry_multiboot = dedent('''
            menuentry "Install -- ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                module ${bootpath}/${kernel_file} dummy cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + os.linesep

        self.menu_install_entry = dedent('''
            menuentry "Install ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_mediacheck_entry_hybrid = dedent('''
            menuentry "Mediacheck" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                $$linux ($$root)${bootpath}/${kernel_file} mediacheck=1 plymouth.enable=0 ${boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_mediacheck_entry_multiboot = dedent('''
            menuentry "Mediacheck" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                module ${bootpath}/${kernel_file} dummy mediacheck=1 plymouth.enable=0 ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + os.linesep

        self.menu_mediacheck_entry = dedent('''
            menuentry "Mediacheck" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                linux ($$root)${bootpath}/${kernel_file} mediacheck=1 plymouth.enable=0 ${boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_install_entry_failsafe_hybrid = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                $$linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                $$initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_install_entry_failsafe_multiboot = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading hypervisor...
                multiboot ${bootpath}/${hypervisor} dummy
                echo Loading kernel...
                module ${bootpath}/${kernel_file} dummy cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                module ${bootpath}/${initrd_file} dummy
            }
        ''').strip() + os.linesep

        self.menu_install_entry_failsafe = dedent('''
            menuentry "Failsafe -- Install ${title}" --class os --unrestricted {
                set gfxpayload=keep
                echo Loading kernel...
                linux ($$root)${bootpath}/${kernel_file} cdinst=1 ${failsafe_boot_options}
                echo Loading initrd...
                initrd ($$root)${bootpath}/${initrd_file}
            }
        ''').strip() + os.linesep

        self.menu_iso_harddisk_entry = dedent('''
            menuentry "Boot from Hard Disk" --class os --unrestricted {
                search --set=root --label EFI
                chainloader ($${root})/EFI/BOOT/bootx64.efi
            }
        ''').strip() + os.linesep

    def get_disk_template(
        self, failsafe=True, hybrid=True, terminal='gfxterm'
    ):
        """
        Bootloader configuration template for disk image

        :param bool failsafe: with failsafe true|false
        :param bool hybrid: with hybrid true|false
        :param string terminal: output terminal name

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += '\n' + self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        if hybrid:
            template_data += self.menu_entry_hybrid
            if failsafe:
                template_data += self.menu_entry_failsafe_hybrid
        else:
            template_data += self.menu_entry
            if failsafe:
                template_data += self.menu_entry_failsafe
        template_data += self.menu_entry_boot_snapshots
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

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        template_data += self.menu_entry_multiboot
        if failsafe:
            template_data += self.menu_entry_failsafe_multiboot
        template_data += self.menu_entry_boot_snapshots
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_iso_template(
        self, failsafe=True, hybrid=True, terminal='gfxterm', checkiso=False
    ):
        """
        Bootloader configuration template for live ISO media

        :param bool failsafe: with failsafe true|false
        :param bool hybrid: with hybrid true|false
        :param string terminal: output terminal name

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme_iso
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        if hybrid:
            template_data += self.menu_entry_hybrid
            if failsafe:
                template_data += self.menu_entry_failsafe_hybrid
            if checkiso:
                template_data += self.menu_mediacheck_entry_hybrid
        else:
            template_data += self.menu_entry
            if failsafe:
                template_data += self.menu_entry_failsafe
            if checkiso:
                template_data += self.menu_mediacheck_entry
        template_data += self.menu_iso_harddisk_entry
        template_data += self.menu_entry_boot_snapshots
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)

    def get_multiboot_iso_template(
        self, failsafe=True, terminal='gfxterm', checkiso=False
    ):
        """
        Bootloader configuration template for live ISO media with
        hypervisor, e.g Xen dom0

        :param bool failsafe: with failsafe true|false
        :param string terminal: output terminal name

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme_iso
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        template_data += self.menu_entry_multiboot
        if failsafe:
            template_data += self.menu_entry_failsafe_multiboot
        if checkiso:
            template_data += self.menu_mediacheck_entry_multiboot
        template_data += self.menu_iso_harddisk_entry
        template_data += self.menu_entry_boot_snapshots
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

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if hybrid:
            template_data += self.header_hybrid
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme_iso
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        template_data += self.menu_iso_harddisk_entry
        if hybrid:
            template_data += self.menu_install_entry_hybrid
            if failsafe:
                template_data += self.menu_install_entry_failsafe_hybrid
        else:
            template_data += self.menu_install_entry
            if failsafe:
                template_data += self.menu_install_entry_failsafe
        template_data += self.menu_entry_boot_snapshots
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

        :return: instance of :class:`Template`

        :rtype: Template
        """
        template_data = self.header
        if terminal == 'gfxterm':
            template_data += self.header_gfxterm
            template_data += self.header_theme_iso
        elif terminal == 'serial':
            template_data += self.header_serial
        else:
            template_data += self.header_textconsole
        template_data += self.menu_iso_harddisk_entry
        template_data += self.menu_install_entry_multiboot
        if failsafe:
            template_data += self.menu_install_entry_failsafe_multiboot
        template_data += self.menu_entry_boot_snapshots
        if terminal == 'gfxterm':
            template_data += self.menu_entry_console_switch
        return Template(template_data)
