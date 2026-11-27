# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import platform
import logging
from typing import Dict, Iterable, List, NamedTuple

# project
from kiwi.command import Command
from kiwi.utils.checksum import Checksum
from kiwi.utils.dir_files import DirFiles
from kiwi.utils.fetch_files import FetchFiles
from kiwi.solver.repository import SolverRepository
from kiwi.system.uri import Uri
from kiwi.path import Path
from kiwi.boxbuild.box_config import BoxConfig
from kiwi.boxbuild.defaults import BoxBuildDefaults

from kiwi.exceptions import (
    KiwiBoxChecksumError,
    KiwiBoxSignatureError,
)

vm_setup_type = NamedTuple(
    'vm_setup_type',
    [
        ('system', str),
        ('kernel', str),
        ('initrd', str),
        ('append', str),
        ('console', str),
        ('ram', str),
        ('smp', str),
    ],
)

log = logging.getLogger('kiwi')


class BoxDownload:
    """
    **Implements download of box file(s)**

    Reads the box configuration file and provides an interface
    to download the box files according to the configuration

    :param string boxname: name of the box from kiwi_boxed_plugin.yml
    :param string arch: arch name for box
    """

    def __init__(self, boxname: str, arch: str = '') -> None:
        self.arch = arch or platform.machine()
        self.box_config = BoxConfig(boxname, arch)
        self.box_dir = os.sep.join(
            [BoxBuildDefaults.get_local_box_cache_dir(), boxname]
        )
        self.box_stage = DirFiles(self.box_dir)
        self.system = ''
        self.kernel = ''
        self.initrd = ''
        Path.create(self.box_dir)

    def fetch_container(self) -> str:
        """
        Download container box from the open build service
        """
        container_source = self.box_config.get_box_container()
        if container_source:
            container_pull = ['sudo', 'podman', 'pull', container_source]
            os.system(' '.join(container_pull))
        return container_source

    def fetch(
        self, update_check: bool = True, snapshot: bool = True
    ) -> vm_setup_type:
        """
        Download box from the open build service

        :param bool update_check: check for box updates True|False
        :param bool snapshot: box is used in snapshot mode True|False
        """
        fetcher = FetchFiles()
        download = update_check
        repo_source = self.box_config.get_box_source()
        if repo_source:
            repo = SolverRepository.new(Uri(repo_source, 'rpm-md'))
            packages_file = self.box_config.get_box_packages_file()
            packages_shasum_file = (
                self.box_config.get_box_packages_shasum_file()
            )
            if update_check and packages_file and packages_shasum_file:
                local_packages_file = os.sep.join([self.box_dir, packages_file])
                local_packages_shasum_file = os.sep.join(
                    [self.box_dir, packages_shasum_file]
                )
                local_packages_file_tmp = self.box_stage.register(
                    local_packages_file
                )
                local_packages_shasum_file_tmp = self.box_stage.register(
                    local_packages_shasum_file
                )
                repo.download_from_repository(
                    packages_file, local_packages_file_tmp
                )
                checksum = Checksum(local_packages_file_tmp)
                shasum = checksum.sha256()
                if checksum.matches(shasum, local_packages_shasum_file):
                    download = False
                    self.box_stage.deregister(local_packages_shasum_file)
                else:
                    self._create_packages_checksum(
                        local_packages_shasum_file_tmp, shasum
                    )

            box_files = self.box_config.get_box_files()
            checksum_files = self.box_config.get_box_checksum_files()
            download_files = (
                box_files
                + checksum_files
                + [f'{checksum_file}.asc' for checksum_file in checksum_files]
            )
            local_files = {
                download_file: os.sep.join([self.box_dir, download_file])
                for download_file in download_files
            }
            if not all(
                os.path.exists(local_file)
                for local_file in local_files.values()
            ):
                download = True
            if download:
                for download_file in download_files:
                    log.info('Downloading {0}'.format(download_file))
                    local_files[download_file] = self.box_stage.register(
                        local_files[download_file]
                    )
                    fetcher.wget(
                        url=os.sep.join(
                            [repo._get_mime_typed_uri(), download_file]
                        ),
                        filename=local_files[download_file],
                    )

            # Downloaded box files are always verified, before they
            # replace the box files in the cache. Box files from the
            # cache are verified if an update check is requested. The
            # system image is changed when used without snapshot mode
            # and is not verified from the cache in this case
            verify_files = [
                box_file
                for box_file in box_files
                if download
                or (
                    update_check
                    and (snapshot or not box_file.endswith('.qcow2'))
                )
            ]
            if verify_files:
                try:
                    checksums = self._get_verified_checksums(
                        checksum_files, local_files
                    )
                    for box_file in verify_files:
                        self._verify_checksum(
                            box_file, local_files[box_file], checksums
                        )
                except Exception:
                    if download:
                        self._wipe_staged_files(local_files.values())
                    raise

            if download:
                self.box_stage.commit()

            for box_file in box_files:
                local_box_file = os.sep.join([self.box_dir, box_file])
                if box_file.endswith('.qcow2'):
                    self.system = local_box_file
                if box_file.endswith('.tar.xz'):
                    self.kernel = self._extract_kernel_from_tarball(
                        local_box_file
                    )
                    if self.box_config.use_initrd():
                        self.initrd = self._extract_initrd_from_tarball(
                            local_box_file
                        )

        return vm_setup_type(
            system=self.system,
            kernel=self.kernel,
            initrd=self.initrd,
            append='console={0} {1}'.format(
                self.box_config.get_box_console(),
                self.box_config.get_box_kernel_cmdline(),
            ),
            console=self.box_config.get_box_console(),
            ram=self.box_config.get_box_memory_mbytes(),
            smp=self.box_config.get_box_processors(),
        )

    def _get_verified_checksums(
        self, checksum_files: List[str], local_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Verify the signatures of the checksum files and provide the
        checksums they contain

        The signature of a checksum file is the detached signature
        in the checksum file name with the .asc extension appended,
        like the open build service creates it. It is verified by
        sqv, the signature verification tool of the Sequoia OpenPGP
        project, with the keyring from
        BoxBuildDefaults.get_box_keyring_file

        :param list checksum_files: names of the checksum files
        :param dict local_files: local path of each downloaded file

        :raises KiwiBoxSignatureError: if a signature is not valid

        :return: sha256 checksum by box file name

        :rtype: dict
        """
        keyring = BoxBuildDefaults.get_box_keyring_file()
        checksums: Dict[str, str] = {}
        for checksum_file in checksum_files:
            local_checksum_file = local_files[checksum_file]
            log.info(
                'Verifying signature of {0} with {1}'.format(
                    checksum_file, keyring
                )
            )
            sqv = Command.run(
                [
                    'sqv',
                    '--keyring',
                    keyring,
                    local_files[f'{checksum_file}.asc'],
                    local_checksum_file,
                ],
                raise_on_error=False,
            )
            if sqv.returncode != 0:
                raise KiwiBoxSignatureError(
                    'Signature verification failed for {0}: {1}'.format(
                        checksum_file, sqv.error
                    )
                )
            with open(local_checksum_file) as checksums_data:
                for line in checksums_data:
                    # sha256sum format: checksum, followed by the file
                    # name, prefixed by * for the binary mode
                    fields = line.split()
                    if len(fields) >= 2:
                        file_name = os.path.basename(fields[1].lstrip('*'))
                        checksums[file_name] = fields[0]
        return checksums

    def _verify_checksum(
        self, box_file: str, local_box_file: str, checksums: Dict[str, str]
    ) -> None:
        """
        Verify the given box file against its checksum

        :param str box_file: name of the box file
        :param str local_box_file: local path of the box file
        :param dict checksums: verified checksum by box file name

        :raises KiwiBoxChecksumError: if there is no checksum for the
            box file or if the checksum does not match
        """
        checksum = checksums.get(box_file)
        if not checksum:
            raise KiwiBoxChecksumError(
                f'No checksum for {box_file} found in the box checksum files'
            )
        log.info('Checksum test {0}'.format(box_file))
        if Checksum(local_box_file).sha256() != checksum:
            raise KiwiBoxChecksumError(f'Checksum failed for {box_file}')

    def _wipe_staged_files(self, staged_files: Iterable[str]) -> None:
        for staged_file in staged_files:
            if os.path.exists(staged_file):
                os.unlink(staged_file)

    def _create_packages_checksum(self, filename: str, shasum: str) -> None:
        with open(filename, 'w') as sha_file:
            sha_file.write(shasum)

    def _extract_kernel_from_tarball(self, tarfile: str) -> str:
        Command.run(
            [
                'tar',
                '-C',
                self.box_dir,
                '--transform',
                f's/.*/kernel.{self.arch}/',
                '--wildcards',
                '-xf',
                tarfile,
                '*.kernel',
            ]
        )
        return os.sep.join([self.box_dir, f'kernel.{self.arch}'])

    def _extract_initrd_from_tarball(self, tarfile: str) -> str:
        Command.run(
            [
                'tar',
                '-C',
                self.box_dir,
                '--transform',
                f's/.*/initrd.{self.arch}/',
                '--wildcards',
                '-xf',
                tarfile,
                '*.initrd',
            ]
        )
        return os.sep.join([self.box_dir, f'initrd.{self.arch}'])
