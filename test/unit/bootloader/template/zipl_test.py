from kiwi.bootloader.template.zipl import BootLoaderTemplateZipl


class TestBootLoaderTemplateZipl:
    def setup(self):
        self.zipl = BootLoaderTemplateZipl()

    def setup_method(self, cls):
        self.setup()

    def test_get_loader_template(self):
        assert self.zipl.get_loader_template().substitute(
            boot_timeout='10',
            bootpath='/boot',
            targetbase='',
            targettype='SCSI',
            targetblocksize='512',
            targetoffset='2048',
            targetgeometry=''
        )

    def test_get_entry_template_standard(self):
        assert self.zipl.get_entry_template().substitute(
            title='title',
            boot_options='',
            kernel_file='linux',
            initrd_file='initrd'
        )

    def test_get_entry_template_secure(self):
        assert self.zipl.get_entry_template(secure=True).substitute(
            title='title',
            boot_options='',
            secure_image_file='linux'
        )
