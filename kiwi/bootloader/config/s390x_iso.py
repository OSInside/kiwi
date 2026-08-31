# Copyright (c) 2026 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import struct
import shutil
from typing import Dict
from textwrap import dedent

# project
from kiwi.system.identifier import SystemIdentifier
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.path import Path

log = logging.getLogger('kiwi')


class BootLoaderS390xIso(BootLoaderConfigBase):
    """
    **s390x iso bootloader configuration.**
    """
    def post_init(self, custom_args: Dict = {}) -> None:
        self.custom_args = custom_args
        self.cmdline = self.get_boot_cmdline(None) or ''
        self.config_files: Dict[str, str] = {}
        self.lookup_path = ''

    def write_meta_data(
        self, root_device: str = None, write_device: str = None, boot_options: str = ''
    ) -> None:
        self.cmdline = ' '.join(
            [self.get_boot_cmdline(root_device, write_device), boot_options]
        ).strip()

    def setup_disk_boot_images(
        self, boot_uuid: str, efi_uuid: str = None, lookup_path: str = None
    ) -> None:
        pass

    def setup_disk_image_config(
        self, boot_uuid: str = '', root_uuid: str = '', hypervisor: str = '',
        kernel: str = '', initrd: str = '', boot_options: Dict[str, str] = {}
    ) -> None:
        pass

    def setup_install_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        log.info('Creating s390x install boot images')
        self.lookup_path = lookup_path

    def setup_install_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = 'xen.gz',
        kernel: str = 'linux', initrd: str = 'initrd'
    ) -> None:
        log.info('Creating s390x install image config from template')
        self._prepare_config_files()

    def setup_live_boot_images(
        self, mbrid: SystemIdentifier, lookup_path: str = ''
    ) -> None:
        log.info('Creating s390x live boot images')
        self.lookup_path = lookup_path

    def setup_live_image_config(
        self, mbrid: SystemIdentifier, hypervisor: str = 'xen.gz',
        kernel: str = 'linux', initrd: str = 'initrd'
    ) -> None:
        log.info('Creating s390x live image config file from template')
        self._prepare_config_files()

    def setup_sysconfig_bootloader(self) -> None:
        pass

    def _prepare_config_files(self) -> None:
        relative_loader_path = self.get_boot_path('iso').lstrip('/')

        initrd_ofs_ofs = 0x0001040c
        initrd_siz_ofs = 0x00010414
        initrd_ofs = 0x01000000
        parmfile_ofs = 0x00010480

        # ensure it's never empty, add trailing space
        parmfile_content = self.cmdline.strip() + " "
        parmfile_hmc_content = f"{self.cmdline} console=ttyS1".strip() + " "

        suse_ins_content = dedent(f"""\
            * SUSE Linux for IBM z Systems Installation System
            linux 0x00000000
            initrd.off 0x{initrd_ofs_ofs:08x}
            initrd.siz 0x{initrd_siz_ofs:08x}
            initrd 0x{initrd_ofs:08x}
            parmfile 0x{parmfile_ofs:08x}
        """)

        media_suse_ins_content = dedent(f"""\
            * SUSE Linux for IBM z Systems Installation System
            {relative_loader_path}/linux 0x00000000
            {relative_loader_path}/initrd.off 0x{initrd_ofs_ofs:08x}
            {relative_loader_path}/initrd.siz 0x{initrd_siz_ofs:08x}
            {relative_loader_path}/initrd 0x{initrd_ofs:08x}
            {relative_loader_path}/parmfile 0x{parmfile_ofs:08x}
        """)

        media_susehmc_ins_content = dedent(f"""\
            * SUSE Linux for IBM z Systems Installation System via HMC
            {relative_loader_path}/linux 0x00000000
            {relative_loader_path}/initrd.off 0x{initrd_ofs_ofs:08x}
            {relative_loader_path}/initrd.siz 0x{initrd_siz_ofs:08x}
            {relative_loader_path}/initrd 0x{initrd_ofs:08x}
            {relative_loader_path}/parmfile.hmc 0x{parmfile_ofs:08x}
        """)

        # Note: The following file has spaces at the end of the lines to make them exactly 80 chars wide.
        sles_exec_content = dedent("""\
            /* REXX LOAD EXEC FOR SUSE LINUX S/390 VM GUESTS       */                       
            /* LOADS SUSE LINUX S/390 FILES INTO READER            */                       
            SAY ''                                                                          
            SAY 'LOADING SLES FILES INTO READER...'                                         
            'CP CLOSE RDR'                                                                  
            'PURGE RDR ALL'                                                                 
            'SPOOL PUNCH * RDR'                                                             
            'PUNCH SLES LINUX A (NOH'                                                       
            'PUNCH SLES PARMFILE A (NOH'                                                    
            'PUNCH SLES INITRD A (NOH'                                                      
            'IPL 00C'                                                                       
        """)

        self.config_files[os.path.join(relative_loader_path, 'parmfile')] = parmfile_content
        self.config_files[os.path.join(relative_loader_path, 'parmfile.hmc')] = parmfile_hmc_content
        self.config_files[os.path.join(relative_loader_path, 'suse.ins')] = suse_ins_content
        self.config_files['suse.ins'] = media_suse_ins_content
        self.config_files['susehmc.ins'] = media_susehmc_ins_content
        self.config_files[os.path.join(relative_loader_path, 'sles.exec')] = sles_exec_content

    def _create_s390x_boot_images(self, loader_path: str) -> None:
        initrd_ofs_ofs = 0x0001040c
        initrd_siz_ofs = 0x00010414
        initrd_ofs = 0x01000000
        parmfile_ofs = 0x00010480

        kernel_dest = os.path.join(loader_path, 'linux')
        initrd_dest = os.path.join(loader_path, 'initrd')

        if os.path.exists(kernel_dest) and os.path.exists(initrd_dest):
            initrd_size = os.path.getsize(initrd_dest)

            initrd_off_data = struct.pack('>I', initrd_ofs)
            with open(os.path.join(loader_path, 'initrd.off'), 'wb') as f:
                f.write(initrd_off_data)

            initrd_siz_data = struct.pack('>I', initrd_size)
            with open(os.path.join(loader_path, 'initrd.siz'), 'wb') as f:
                f.write(initrd_siz_data)

            with open(kernel_dest, 'rb') as f:
                cd_ikr_data = bytearray(f.read())

            def write_at_offset(data: bytearray, offset: int, payload: bytes) -> None:
                if len(data) < offset + len(payload):
                    data.extend(b'\x00' * (offset + len(payload) - len(data)))
                data[offset:offset + len(payload)] = payload

            write_at_offset(cd_ikr_data, initrd_ofs_ofs, initrd_off_data)
            write_at_offset(cd_ikr_data, initrd_siz_ofs, initrd_siz_data)
            write_at_offset(cd_ikr_data, parmfile_ofs, b'\x00' * 512)

            parmfile_content = self.cmdline
            write_at_offset(cd_ikr_data, parmfile_ofs, parmfile_content.encode('utf-8'))

            with open(initrd_dest, 'rb') as f:
                initrd_bytes = f.read()
            write_at_offset(cd_ikr_data, initrd_ofs, initrd_bytes)

            write_at_offset(cd_ikr_data, 4, b'\x80\x01\x00\x00')

            padding_size = -initrd_size & 0xfff
            if padding_size > 0:
                cd_ikr_data.extend(b'\x00' * padding_size)

            with open(os.path.join(loader_path, 'cd.ikr'), 'wb') as f:
                f.write(cd_ikr_data)
            log.info("Created s390x boot image: cd.ikr")
        else:
            log.info(
                "Skipping cd.ikr creation because kernel and initrd are not yet present "
                "in the boot loader directory."
            )

        with open(os.path.join(loader_path, 'zipl.map'), 'wb') as f:
            f.write(b'\x00' * (4096 * 4))
        log.info("Created zipl.map")

    def setup_s390x_boot_images(self, kernel_file: str, initrd_file: str) -> None:
        """
        Setup s390x boot images (linux, initrd, cd.ikr, zipl.map)
        from the finalized kernel and initrd files.
        """
        log.info('Setting up s390x boot images')
        loader_path = os.path.join(
            self.boot_dir, self.get_boot_path('iso').lstrip('/')
        )
        Path.create(loader_path)

        kernel_dest = os.path.join(loader_path, 'linux')
        initrd_dest = os.path.join(loader_path, 'initrd')

        shutil.copy(kernel_file, kernel_dest)
        shutil.copy(initrd_file, initrd_dest)
        log.info(f"Copied kernel to {kernel_dest} and initrd to {initrd_dest}")

        self._create_s390x_boot_images(loader_path)

    def write(self) -> None:
        log.info('Writing s390x bootloader configuration')
        loader_path = os.path.join(
            self.boot_dir, self.get_boot_path('iso').lstrip('/')
        )
        Path.create(loader_path)

        for filename, content in self.config_files.items():
            filepath = os.path.join(self.boot_dir, filename.lstrip('/'))
            Path.create(os.path.dirname(filepath))
            with open(filepath, 'w') as f:
                f.write(content)
            log.info(f"Created configuration file {filepath}")

        self._create_s390x_boot_images(loader_path)
