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
from tempfile import mkdtemp
from tempfile import NamedTemporaryFile
import platform
import shutil

# project
from kiwi.bootloader.config import BootLoaderConfig
from kiwi.filesystem import FileSystem
from kiwi.filesystem.isofs import FileSystemIsoFs
from kiwi.filesystem.setup import FileSystemSetup
from kiwi.storage.loop_device import LoopDevice
from kiwi.boot.image import BootImageDracut
from kiwi.system.size import SystemSize
from kiwi.system.setup import SystemSetup
from kiwi.firmware import FirmWare
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.system.result import Result
from kiwi.iso_tools.iso import Iso
from kiwi.system.identifier import SystemIdentifier
from kiwi.system.kernel import Kernel
from kiwi.logger import log
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiLiveBootImageError
)


class LiveImageBuilder(object):
    """
    **Live image builder**

    :param object xml_state: instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: root directory path name
    :param dict custom_args: Custom processing arguments
    """
    def __init__(self, xml_state, target_dir, root_dir, custom_args=None):
        self.media_dir = None
        self.live_container_dir = None
        self.arch = platform.machine()
        if self.arch == 'i686' or self.arch == 'i586':
            self.arch = 'ix86'
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.live_type = xml_state.build_type.get_flags()
        self.volume_id = xml_state.build_type.get_volid() or \
            Defaults.get_volume_id()
        self.mbrid = SystemIdentifier()
        self.mbrid.calculate_id()
        self.filesystem_custom_parameters = {
            'mount_options': xml_state.get_fs_mount_option_list()
        }
        self.publisher = xml_state.build_type.get_publisher() or \
            Defaults.get_publisher()
        self.custom_args = custom_args

        if not self.live_type:
            self.live_type = Defaults.get_default_live_iso_type()

        self.boot_image = BootImageDracut(
            xml_state, target_dir, self.root_dir
        )
        self.firmware = FirmWare(
            xml_state
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.isoname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
                '.iso'
            ]
        )
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self):
        """
        Build a bootable hybrid live ISO image

        Image types which triggers this builder are:

        * image="iso"

        :raises KiwiLiveBootImageError: if no kernel or hipervisor is found
            in boot image tree
        :return: result

        :rtype: instance of :class:`Result`
        """
        # media dir to store CD contents
        self.media_dir = mkdtemp(
            prefix='live-media.', dir=self.target_dir
        )

        # unpack cdroot user files to media dir
        self.system_setup.import_cdroot_files(self.media_dir)

        rootsize = SystemSize(self.media_dir)

        # custom iso metadata
        log.info('Using following live ISO metadata:')
        log.info('--> Application id: {0}'.format(self.mbrid.get_id()))
        log.info('--> Publisher: {0}'.format(Defaults.get_publisher()))
        log.info('--> Volume id: {0}'.format(self.volume_id))
        custom_iso_args = {
            'meta_data': {
                'publisher': self.publisher,
                'preparer': Defaults.get_preparer(),
                'volume_id': self.volume_id,
                'mbr_id': self.mbrid.get_id(),
                'efi_mode': self.firmware.efi_mode()
            }
        }

        # pack system into live boot structure as expected by dracut
        log.info(
            'Packing system into dracut live ISO type: {0}'.format(
                self.live_type
            )
        )
        root_filesystem = Defaults.get_default_live_iso_root_filesystem()
        filesystem_custom_parameters = {
            'mount_options': self.xml_state.get_fs_mount_option_list()
        }
        filesystem_setup = FileSystemSetup(
            self.xml_state, self.root_dir
        )
        root_image = NamedTemporaryFile()
        loop_provider = LoopDevice(
            root_image.name,
            filesystem_setup.get_size_mbytes(root_filesystem),
            self.xml_state.build_type.get_target_blocksize()
        )
        loop_provider.create()
        live_filesystem = FileSystem(
            name=root_filesystem,
            device_provider=loop_provider,
            root_dir=self.root_dir + os.sep,
            custom_args=filesystem_custom_parameters
        )
        live_filesystem.create_on_device()
        log.info(
            '--> Syncing data to {0} root image'.format(root_filesystem)
        )
        live_filesystem.sync_data(
            Defaults.get_exclude_list_for_root_data_sync()
        )
        log.info('--> Creating squashfs container for root image')
        self.live_container_dir = mkdtemp(
            prefix='live-container.', dir=self.target_dir
        )
        Path.create(self.live_container_dir + '/LiveOS')
        shutil.copy(
            root_image.name, self.live_container_dir + '/LiveOS/rootfs.img'
        )
        live_container_image = FileSystem(
            name='squashfs',
            device_provider=None,
            root_dir=self.live_container_dir
        )
        container_image = NamedTemporaryFile()
        live_container_image.create_on_file(
            container_image.name
        )
        Path.create(self.media_dir + '/LiveOS')
        shutil.copy(
            container_image.name, self.media_dir + '/LiveOS/squashfs.img'
        )

        # setup bootloader config to boot the ISO via isolinux
        log.info('Setting up isolinux bootloader configuration')
        bootloader_config_isolinux = BootLoaderConfig(
            'isolinux', self.xml_state, self.media_dir
        )
        bootloader_config_isolinux.setup_live_boot_images(
            mbrid=None,
            lookup_path=self.boot_image.boot_root_directory
        )
        bootloader_config_isolinux.setup_live_image_config(
            mbrid=None
        )
        bootloader_config_isolinux.write()

        # setup bootloader config to boot the ISO via EFI
        if self.firmware.efi_mode():
            log.info('Setting up EFI grub bootloader configuration')
            bootloader_config_grub = BootLoaderConfig(
                'grub2', self.xml_state, self.media_dir, {
                    'grub_directory_name':
                        Defaults.get_grub_boot_directory_name(self.root_dir)
                }
            )
            bootloader_config_grub.setup_live_boot_images(
                mbrid=self.mbrid, lookup_path=self.root_dir
            )
            bootloader_config_grub.setup_live_image_config(
                mbrid=self.mbrid
            )
            bootloader_config_grub.write()

        # call custom editbootconfig script if present
        self.system_setup.call_edit_boot_config_script(
            filesystem='iso:{0}'.format(self.media_dir), boot_part_id=1,
            working_directory=self.root_dir
        )

        # prepare dracut initrd call
        self.boot_image.prepare()

        # create dracut initrd for live image
        log.info('Creating live ISO boot image')
        self._create_dracut_live_iso_config()
        self.boot_image.create_initrd(self.mbrid)

        # setup kernel file(s) and initrd in ISO boot layout
        log.info('Setting up kernel file(s) and boot image in ISO boot layout')
        self._setup_live_iso_kernel_and_initrd()

        # calculate size and decide if we need UDF
        if rootsize.accumulate_mbyte_file_sizes() > 4096:
            log.info('ISO exceeds 4G size, using UDF filesystem')
            custom_iso_args['meta_data']['udf'] = True

        # create iso filesystem from media_dir
        log.info('Creating live ISO image')
        iso_image = FileSystemIsoFs(
            device_provider=None, root_dir=self.media_dir,
            custom_args=custom_iso_args
        )
        iso_image.create_on_file(self.isoname)

        # include metadata for checkmedia tool
        if self.xml_state.build_type.get_mediacheck() is True:
            Iso.set_media_tag(self.isoname)

        self.result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.isoname
        )
        self.result.add(
            key='live_image',
            filename=self.isoname,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result

    def _create_dracut_live_iso_config(self):
        live_config_file = self.root_dir + '/etc/dracut.conf.d/02-livecd.conf'
        omit_modules = [
            'kiwi-dump', 'kiwi-overlay', 'kiwi-repart', 'kiwi-lib', 'multipath'
        ]
        live_config = [
            'add_dracutmodules+=" {0} pollcdrom "'.format(
                Defaults.get_live_dracut_module_from_flag(self.live_type)
            ),
            'omit_dracutmodules+=" {0} "'.format(' '.join(omit_modules)),
            'hostonly="no"',
            'dracut_rescue_image="no"'
        ]
        with open(live_config_file, 'w') as config:
            for entry in live_config:
                config.write(entry + os.linesep)

    def _setup_live_iso_kernel_and_initrd(self):
        """
        Copy kernel and initrd from the root tree into the iso boot structure
        """
        boot_path = ''.join(
            [self.media_dir, '/boot/', self.arch, '/loader']
        )
        Path.create(boot_path)

        # Move kernel files to iso filesystem structure
        kernel = Kernel(self.boot_image.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(boot_path, '/linux')
        else:
            raise KiwiLiveBootImageError(
                'No kernel in boot image tree {0} found'.format(
                    self.boot_image.boot_root_directory
                )
            )
        if self.xml_state.is_xen_server():
            if kernel.get_xen_hypervisor():
                kernel.copy_xen_hypervisor(boot_path, '/xen.gz')
            else:
                raise KiwiLiveBootImageError(
                    'No hypervisor in boot image tree {0} found'.format(
                        self.boot_image.boot_root_directory
                    )
                )

        # Move initrd to iso filesystem structure
        if os.path.exists(self.boot_image.initrd_filename):
            shutil.move(
                self.boot_image.initrd_filename, boot_path + '/initrd'
            )
        else:
            raise KiwiLiveBootImageError(
                'No boot image {0} in boot image tree {1} found'.format(
                    self.boot_image.initrd_filename,
                    self.boot_image.boot_root_directory
                )
            )

    def __del__(self):
        if self.media_dir or self.live_container_dir:
            log.info(
                'Cleaning up {0} instance'.format(type(self).__name__)
            )
            if self.media_dir:
                Path.wipe(self.media_dir)
            if self.live_container_dir:
                Path.wipe(self.live_container_dir)
