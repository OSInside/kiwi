# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from pytest import raises
from unittest.mock import Mock

from kiwi.bootloader.config.custom import BootLoaderConfigCustom


class TestBootLoaderConfigCustom:
    def setup(self):
        self.bootloader = BootLoaderConfigCustom(
            Mock(), 'root_dir'
        )

    def setup_method(self, cls):
        self.setup()

    def test_setup_disk_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_disk_boot_images('0815')

    def test_setup_disk_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_disk_image_config(Mock())

    def test_setup_install_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_install_boot_images('0815')

    def test_setup_install_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_install_image_config(Mock())

    def test_setup_live_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_live_boot_images('0815')

    def test_setup_live_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_live_image_config(Mock())

    def test_setup_sysconfig_bootloader(self):
        with raises(NotImplementedError):
            self.bootloader.setup_sysconfig_bootloader()

    def test_write(self):
        with raises(NotImplementedError):
            self.bootloader.write()
