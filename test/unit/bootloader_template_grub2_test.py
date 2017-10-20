from kiwi.bootloader.template.grub2 import BootLoaderTemplateGrub2


class TestBootLoaderTemplateGrub2(object):
    def setup(self):
        self.grub2 = BootLoaderTemplateGrub2()

    def test_get_disk_template(self):
        assert self.grub2.get_disk_template().substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2'
        )

    def test_get_disk_template_console(self):
        assert self.grub2.get_disk_template(
            terminal='console'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot'
        )

    def test_get_disk_template_serial_no_hybird(self):
        assert self.grub2.get_disk_template(
            terminal='serial',
            hybrid=False
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot'
        )

    def test_get_multiboot_disk_template(self):
        assert self.grub2.get_multiboot_disk_template().substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_disk_template_console(self):
        assert self.grub2.get_multiboot_disk_template(
            terminal='console'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_disk_template_serial(self):
        assert self.grub2.get_multiboot_disk_template(
            terminal='serial'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz'
        )

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
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_install_template_console(self):
        assert self.grub2.get_multiboot_install_template(
            terminal='console'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_install_template_serial(self):
        assert self.grub2.get_multiboot_install_template(
            terminal='serial'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            hypervisor='xen.gz'
        )

    def test_get_install_template(self):
        assert self.grub2.get_install_template().substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='cdinst=1 splash',
            failsafe_boot_options='cdinst=1 splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot',
            boot_directory_name='grub2'
        )

    def test_get_install_template_console_no_hybrid(self):
        assert self.grub2.get_install_template(
            terminal='console',
            hybrid=False
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='cdinst=1 splash',
            failsafe_boot_options='cdinst=1 splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot'
        )

    def test_get_install_template_serial_no_hybrid(self):
        assert self.grub2.get_install_template(
            terminal='serial',
            hybrid=False
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='cdinst=1 splash',
            failsafe_boot_options='cdinst=1 splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community [ VMX ]',
            bootpath='/boot'
        )

    def test_get_iso_template(self):
        assert self.grub2.get_iso_template().substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            gfxmode='800x600',
            theme='SLE',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2'
        )

    def test_get_iso_template_console_no_hybrid(self):
        assert self.grub2.get_iso_template(
            terminal='console',
            hybrid=False
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot'
        )

    def test_get_iso_template_serial_no_hybrid(self):
        assert self.grub2.get_iso_template(
            terminal='serial',
            hybrid=False
        ).substitute(
            search_params='--file --set=root /boot/0xd305fb7d',
            default_boot='0',
            kernel_file='boot/linux.vmx',
            initrd_file='boot/initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot'
        )

    def test_get_iso_template_checkiso_no_hybrid(self):
        assert self.grub2.get_iso_template(
            hybrid=False, checkiso=True
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
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2'
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
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2'
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
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_iso_template_console(self):
        assert self.grub2.get_multiboot_iso_template(
            terminal='console'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            hypervisor='xen.gz'
        )

    def test_get_multiboot_iso_template_serial(self):
        assert self.grub2.get_multiboot_iso_template(
            terminal='serial'
        ).substitute(
            search_params='--fs-uuid --set=root 0815',
            default_boot='0',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='splash',
            failsafe_boot_options='splash',
            boot_timeout='10',
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            hypervisor='xen.gz'
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
            title='LimeJeOS-SLE12-Community',
            bootpath='/boot',
            boot_directory_name='grub2',
            hypervisor='xen.gz'
        )
