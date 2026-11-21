from kiwi.bootloader.template.grub2 import BootLoaderTemplateGrub2


class TestBootLoaderTemplateGrub2:
    def setup(self):
        self.grub2 = BootLoaderTemplateGrub2()

    def setup_method(self, cls):
        self.setup()

    def test_get_multiboot_install_template(self):
        assert self.grub2.get_multiboot_install_template().substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_install_template_console(self):
        assert self.grub2.get_multiboot_install_template(
            has_graphics=False
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_install_template_serial(self):
        assert self.grub2.get_multiboot_install_template(
            has_graphics=False, has_serial=True
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='serial --speed=38400',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='serial',
            terminal_output='serial',
        )

    def test_get_multiboot_install_template_console_relative_btrfs(self):
        assert self.grub2.get_multiboot_install_template(
            has_graphics=False, has_btrfs_relative_path=True
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_install_template(self):
        assert self.grub2.get_install_template(has_serial=True).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='cdinst=1 splash',
            failsafe_boot_options='cdinst=1 splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_install_template_supports_iso_scan(self):
        template = self.grub2.get_install_template().substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )
        assert 'isoboot="iso-scan/filename=${iso_path}"' in template
        # install and failsafe install entry
        assert template.count('cdinst=1 ${isoboot} splash') == 2

    def test_get_install_template_relative_btrfs(self):
        assert self.grub2.get_install_template(
            has_serial=True, has_btrfs_relative_path=True
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='cdinst=1 splash',
            failsafe_boot_options='cdinst=1 splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_iso_template(self):
        assert self.grub2.get_iso_template(has_serial=True).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_iso_template_checkiso(self):
        assert self.grub2.get_iso_template(checkiso=True).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_iso_template_checkiso_relative_btrfs(self):
        assert self.grub2.get_iso_template(
            checkiso=True, has_btrfs_relative_path=True
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_iso_template(self):
        assert self.grub2.get_multiboot_iso_template().substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_iso_template_console(self):
        assert self.grub2.get_multiboot_iso_template(
            has_graphics=False
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_iso_template_serial(self):
        assert self.grub2.get_multiboot_iso_template(
            has_graphics=False, has_serial=True
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='serial',
            terminal_output='serial',
        )

    def test_get_multiboot_iso_template_checkiso(self):
        assert self.grub2.get_multiboot_iso_template(checkiso=True).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def test_get_multiboot_iso_template_checkiso_relative_btrfs(self):
        assert self.grub2.get_multiboot_iso_template(
            checkiso=True, has_btrfs_relative_path=True
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )

    def _get_disk_template_parameters(self):
        return {
            'search_params': '--no-floppy --fs-uuid --set=root 0815',
            'default_boot': '0',
            'kernel_file': '/boot/vmlinuz-6.12-default',
            'initrd_file': '/boot/initrd-6.12-default',
            'boot_options': 'splash root=PARTUUID=0816',
            'failsafe_boot_options': 'splash root=PARTUUID=0816 failsafe',
            'gfxmode': '800x600',
            'theme': 'SLE',
            'boot_timeout': '10',
            'boot_timeout_style': 'menu',
            'serial_line_setup': 'serial --speed=38400',
            'title': 'Disk',
            'bootpath': '/boot',
            'boot_directory_name': 'grub2',
            'terminal_input': 'console',
            'terminal_output': 'gfxterm',
        }

    def test_get_disk_template(self):
        config = self.grub2.get_disk_template().substitute(
            self._get_disk_template_parameters()
        )
        assert config.startswith(
            '# kiwi generated grub2 config file\n'
            'search --no-floppy --fs-uuid --set=root 0815\n'
            'set default=0\n'
            'set timeout=10\n'
            'set timeout_style=menu\n'
        )
        assert (
            'menuentry "Disk" --class os --unrestricted {\n'
            '    set gfxpayload=keep\n'
            '    echo Loading kernel...\n'
            '    linux ($root)/boot/vmlinuz-6.12-default '
            'splash root=PARTUUID=0816\n'
            '    echo Loading initrd...\n'
            '    initrd ($root)/boot/initrd-6.12-default\n'
            '}\n'
        ) in config
        assert 'menuentry "Failsafe -- Disk"' in config
        assert 'set gfxmode=800x600' in config
        assert 'set theme=($root)/boot/grub2/themes/SLE/theme.txt' in config
        assert 'hiddenentry "Text mode"' in config
        assert 'serial --speed=38400' not in config
        assert 'btrfs_relative_path' not in config

    def test_get_disk_template_console_serial_relative_btrfs(self):
        parameters = self._get_disk_template_parameters()
        parameters['kernel_file_1'] = '/boot/vmlinuz-6.12-kvmsmall'
        parameters['initrd_file_1'] = '/boot/initrd-6.12-kvmsmall'
        parameters['title_1'] = 'Disk (kvmsmall)'
        config = self.grub2.get_disk_template(
            failsafe=False,
            has_graphics=False,
            has_serial=True,
            has_btrfs_relative_path=True,
            kernel_count=2,
        ).substitute(parameters)
        assert config.startswith('set btrfs_relative_path="y"\n')
        assert 'serial --speed=38400\n' in config
        assert 'menuentry "Disk" --class os' in config
        assert 'menuentry "Disk (kvmsmall)" --class os' in config
        assert 'linux ($root)/boot/vmlinuz-6.12-kvmsmall' in config
        assert 'Failsafe' not in config
        assert 'gfxmode' not in config
        assert 'Text mode' not in config

    def test_get_kernel_menu_entries(self):
        # the main entry of the live and the install entry of the
        # install templates is repeated once per kernel
        parameters = dict(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux',
            initrd_file='initrd',
            kernel_file_1='linux-default',
            initrd_file_1='initrd-default',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            boot_timeout_style='menu',
            serial_line_setup='',
            title='Bob (rt)',
            title_1='Bob (default)',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz',
            efi_image_name='bootx64.efi',
            terminal_input='console',
            terminal_output='console',
        )
        for get_template, entry_title in [
            (self.grub2.get_iso_template, 'menuentry "Bob'),
            (self.grub2.get_multiboot_iso_template, 'menuentry "Bob'),
            (self.grub2.get_install_template, 'menuentry "Install Bob'),
            (
                self.grub2.get_multiboot_install_template,
                'menuentry "Install -- Bob',
            ),
        ]:
            config = get_template(kernel_count=2).substitute(parameters)
            assert config.count(f'{entry_title} (rt)"') == 1
            assert config.count(f'{entry_title} (default)"') == 1
            assert config.count('/linux-default') == 1
            assert config.count('/initrd-default') == 1
