from kiwi.repository.template.apt import PackageManagerTemplateAptGet


class TestPackageManagerTemplateAptGet:
    def setup(self):
        self.apt = PackageManagerTemplateAptGet()

    def setup_method(self, cls):
        self.setup()

    def test_get_host_template(self):
        assert self.apt.get_host_template().substitute(
            apt_shared_base='/var/cache/kiwi/apt-get',
            unauthenticated='true'
        )

    def test_get_image_template(self):
        assert self.apt.get_image_template().substitute(
            unauthenticated='true'
        )

    def test_get_host_template_with_exclude_docs(self):
        assert self.apt.get_host_template(exclude_docs=True).substitute(
            apt_shared_base='/var/cache/kiwi/apt-get',
            unauthenticated='true'
        )

    def test_get_image_template_with_exclude_docs(self):
        assert self.apt.get_image_template(exclude_docs=True).substitute(
            unauthenticated='true'
        )
