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
import os
import logging
from tempfile import mkdtemp

# project
from kiwi.defaults import Defaults
from kiwi.utils.sync import DataSync
from kiwi.system.prepare import SystemPrepare
from kiwi.system.profile import Profile
from kiwi.system.setup import SystemSetup
from kiwi.archive.cpio import ArchiveCpio
from kiwi.utils.compress import Compress
from kiwi.path import Path
from kiwi.boot.image.base import BootImageBase

log = logging.getLogger('kiwi')


class BootImageKiwi(BootImageBase):
    """
    **Implements preparation and creation of kiwi boot(initrd) images**

    The kiwi initrd is a customized first boot initrd which allows
    to control the first boot an appliance. The kiwi initrd replaces
    itself after first boot by the result of dracut.
    """
    def post_init(self):
        """
        Post initialization method

        Creates custom directory to prepare the boot image
        root filesystem which is a separate image to create
        the initrd from
        """
        # builtin kiwi initrd builds its own root tree to create
        # an initrd from. Thus there is no pre defined boot root
        # directory
        self.boot_root_directory = None

        self.temp_directories = []

    def prepare(self):
        """
        Prepare new root system suitable to create a kiwi initrd from it
        """
        self.boot_root_directory = mkdtemp(
            prefix='kiwi_boot_root.', dir=self.target_dir
        )
        self.temp_directories.append(
            self.boot_root_directory
        )
        self.load_boot_xml_description()
        boot_image_name = self.boot_xml_state.xml_data.get_name()

        self.import_system_description_elements()

        log.info('Preparing boot image')
        system = SystemPrepare(
            xml_state=self.boot_xml_state,
            root_dir=self.boot_root_directory,
            allow_existing=True
        )
        manager = system.setup_repositories(signing_keys=self.signing_keys)
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
        profile.create(
            Defaults.get_profile_file(self.boot_root_directory)
        )
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

    def create_initrd(self, mbrid=None, basename=None, install_initrd=False):
        """
        Create initrd from prepared boot system tree and compress the result

        :param object mbrid: instance of ImageIdentifier
        :param string basename: base initrd file name
        :param bool install_initrd: installation media initrd

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
            if basename:
                kiwi_initrd_basename = basename
            else:
                kiwi_initrd_basename = self.initrd_base_name
            temp_boot_root_directory = mkdtemp(
                prefix='kiwi_boot_root_copy.'
            )
            os.chmod(temp_boot_root_directory, 0o755)
            self.temp_directories.append(
                temp_boot_root_directory
            )
            data = DataSync(
                self.boot_root_directory + '/',
                temp_boot_root_directory
            )
            data.sync_data(
                options=['-a']
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

            cpio = ArchiveCpio(
                os.sep.join([self.target_dir, kiwi_initrd_basename])
            )
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
            compress = Compress(
                os.sep.join([self.target_dir, kiwi_initrd_basename])
            )
            compress.xz(
                ['--check=crc32', '--lzma2=dict=1MiB', '--threads=0']
            )
            self.initrd_filename = compress.compressed_filename

    def cleanup(self):
        for directory in self.temp_directories:
            if directory and os.path.exists(directory):
                Path.wipe(directory)
