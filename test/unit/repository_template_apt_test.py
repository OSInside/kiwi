
from mock import patch

import mock

from .test_helper import *

from kiwi.repository.template.apt import PackageManagerTemplateAptGet


class TestPackageManagerTemplateAptGet(object):
    def setup(self):
        self.apt = PackageManagerTemplateAptGet()

    def test_get_host_template(self):
        assert self.apt.get_host_template().substitute(
            apt_shared_base='/var/cache/kiwi/apt-get'
        )

    def test_get_image_template(self):
        assert self.apt.get_image_template().substitute()

    def test_get_host_template_with_exclude_docs(self):
        assert self.apt.get_host_template(exclude_docs=True).substitute(
            apt_shared_base='/var/cache/kiwi/apt-get'
        )

    def test_get_image_template_with_exclude_docs(self):
        assert self.apt.get_image_template(exclude_docs=True).substitute()
