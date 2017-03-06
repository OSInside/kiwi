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
from tempfile import mkdtemp

from kiwi.defaults import Defaults
from kiwi.utils.sync import DataSync
from kiwi.system.prepare import SystemPrepare
from kiwi.system.profile import Profile
from kiwi.system.setup import SystemSetup
from kiwi.logger import log
from kiwi.archive.cpio import ArchiveCpio
from kiwi.utils.compress import Compress
from kiwi.path import Path
from kiwi.boot.image.base import BootImageBase


class BootImageKiwi(BootImageBase):
    """
    Implements preparation and creation of kiwi boot(initrd) images
    The kiwi initrd is a customized first boot initrd which allows
    to control the first boot an appliance. The kiwi initrd replaces
    itself after first boot by the result of dracut.
    """
    def prepare(self):
        """
        Prepare new root system suitable to create a kiwi initrd from it
        """
        self.load_boot_xml_description()
        boot_image_name = self.boot_xml_state.xml_data.get_name()

        self.import_system_description_elements()

        log.info('Preparing boot image')
        system = SystemPrepare(
            xml_state=self.boot_xml_state,
            root_dir=self.boot_root_directory,
            allow_existing=True
        )
        manager = system.setup_repositories()
        system.install_bootstrap(
            manager
        )
        system.install_system(
            manager
        )

        profile = Profile(self.boot_xml_state)
        profile.add('kiwi_initrdname', boot_image_name)

        defaults = Defaults()
        defaults.to_profile(profile)

        self.setup = SystemSetup(
            self.boot_xml_state, self.boot_root_directory
        )
        self.setup.import_shell_environment(profile)
        self.setup.import_description()
        self.setup.import_overlay_files(
            follow_links=True
        )
        self.setup.call_config_script()

        system.pinch_system(
            manager=manager, force=True
        )
        # make sure system instance is cleaned up before setting up
        del system

        self.setup.call_image_script()
        self.setup.create_init_link_from_linuxrc()

    def create_initrd(self, mbrid=None):
        """
        Create initrd from prepared boot system tree and compress the result

        :param object mbrid: instance of ImageIdentifier
        """
        if self.is_prepared():
            log.info('Creating initrd cpio archive')
            # we can't simply exclude boot when building the archive
            # because the file boot/mbrid must be preserved. Because of
            # that we create a copy of the boot directory and remove
            # everything in boot/ except for boot/mbrid. The original
            # boot directory should not be changed because we rely
            # on other data in boot/ e.g the kernel to be available
            # for the entire image building process
            temp_boot_root_directory = mkdtemp(
                prefix='kiwi_boot_root_copy.'
            )
            self.temp_directories.append(
                temp_boot_root_directory
            )
            data = DataSync(
                self.boot_root_directory + '/',
                temp_boot_root_directory
            )
            data.sync_data(
                options=['-z', '-a']
            )
            boot_directory = temp_boot_root_directory + '/boot'
            Path.wipe(boot_directory)
            if mbrid:
                log.info(
                    '--> Importing mbrid: %s', mbrid.get_id()
                )
                Path.create(boot_directory)
                image_identifier = boot_directory + '/mbrid'
                mbrid.write(image_identifier)

            cpio = ArchiveCpio(self.initrd_file_name)
            # the following is a list of directories which were needed
            # during the process of creating an image but not when the
            # image is actually booting with this initrd
            exclude_from_archive = [
                '/' + Defaults.get_shared_cache_location(),
                '/image', '/usr/lib/grub*'
            ]
            # the following is a list of directories to exclude which
            # are not needed inside of the initrd
            exclude_from_archive += [
                '/usr/share/doc', '/usr/share/man', '/home', '/media', '/srv'
            ]
            cpio.create(
                source_dir=temp_boot_root_directory,
                exclude=exclude_from_archive
            )
            log.info(
                '--> xz compressing archive'
            )
            compress = Compress(self.initrd_file_name)
            compress.xz()
            self.initrd_filename = compress.compressed_filename
