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
            terminal_output='console'
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
            terminal_output='console'
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
            terminal_output='serial'
        )

    def test_get_install_template(self):
        assert self.grub2.get_install_template(
            has_serial=True
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
            terminal_output='console'
        )

    def test_get_iso_template(self):
        assert self.grub2.get_iso_template(
            has_serial=True
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
            terminal_output='console'
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
            terminal_output='console'
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
            terminal_output='console'
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
            terminal_output='console'
        )

    def test_get_multiboot_iso_template_serial(self):
        assert self.grub2.get_multiboot_iso_template(
            has_graphics=False,
            has_serial=True
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
            terminal_output='serial'
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
            terminal_output='console'
        )
