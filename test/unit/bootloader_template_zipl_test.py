from kiwi.bootloader.template.zipl import BootLoaderTemplateZipl


class TestBootLoaderTemplateZipl(object):
    def setup(self):
        self.zipl = BootLoaderTemplateZipl()

    def test_get_template(self):
        assert self.zipl.get_template().substitute(
            device='/dev/loop0',
            target_type='CDL',
            blocksize='4096',
            offset=24,
            geometry='2912,15,12',
            default_boot='1',
            bootpath='boot/zipl',
            boot_timeout='200',
            title='LimeJeOS-DASD-ECKD-SLE12_(_VMX_)',
            kernel_file='linux.vmx',
            initrd_file='initrd.vmx',
            boot_options='cio_ignore=all,!ipldev,!condev',
            failsafe_boot_options='x11failsafe cio_ignore=all,!ipldev,!condev'
        )
