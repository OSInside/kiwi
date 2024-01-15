from kiwi.bootloader.template.systemd_boot import BootLoaderTemplateSystemdBoot


class TestBootLoaderTemplateSystemdBoot:
    def setup(self):
        self.systemd_boot = BootLoaderTemplateSystemdBoot()

    def setup_method(self, cls):
        self.setup()

    def test_get_loader_template(self):
        assert self.systemd_boot.get_loader_template().substitute(
            boot_timeout='10'
        )
