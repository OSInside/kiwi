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
import pwd
import time
import logging
import platform
from threading import Thread
from typing import (
    List, Optional
)

# project
from kiwi.path import Path
from kiwi.command import Command
from kiwi.boxbuild.box_download import BoxDownload
from kiwi.boxbuild.defaults import BoxBuildDefaults
import kiwi.boxbuild.defaults as runtime

from kiwi.exceptions import (
    KiwiBoxDownloadError,
    KiwiBoxQEMUBinaryNotFound,
    KiwiBoxSSHPortInvalid,
    KiwiBoxSSHKeyNotFound,
    KiwiBoxBuildError
)

log = logging.getLogger('kiwi')


class BoxBuild:
    """
    **Implements boxbuild command**

    Implements an interface to run a kiwi build box using
    the KVM virtualization platform

    :param str boxname: name of the box from kiwi_boxed_plugin.yml
    :param str ram: amount of main memory to use for the box
    :param str console: console name for the box kernel
    :param str smp: number of CPUs to use in the SMP setup for the box
    :param str arch: arch name for box
    :param str machine: machine emulaton type for the box
    :param str cpu: CPU emulation type
    :param str sharing_backend: guest/host sharing backend type
    :param str ssh_key: name of the ssh key to authorize for sshfs sharing
    :param str ssh_port: host port number to use to forward the guest's SSH port
    :param bool accel: use KVM hardware acceleration True|False
    """
    def __init__(
        self, boxname: str, ram: Optional[str] = None,
        console: Optional[str] = None, smp: Optional[str] = None,
        arch: str = '', machine: Optional[str] = None, cpu: str = 'host',
        sharing_backend: str = '9p', ssh_key: str = 'id_rsa',
        ssh_port: str = '', accel: bool = True
    ) -> None:
        self.ram = ram
        self.console = console
        self.smp = smp
        self.cpu = cpu
        self.machine = machine
        self.arch = arch or platform.machine()
        self.box = BoxDownload(boxname, arch)
        self.sharing_backend = sharing_backend
        self.ssh_key = ssh_key
        self.ssh_port = ssh_port
        self.kiwi_exit: Optional[int] = None
        self.accel = accel

    def run(
        self, kiwi_build_command: List[str], update_check: bool = True,
        snapshot: bool = True, keep_open: bool = False,
        kiwi_version: Optional[str] = None,
        custom_shared_path: Optional[str] = None
    ) -> None:
        """
        Start the build process in a box VM using KVM

        :param list kiwi_build_command:
            kiwi build command line Example:

            .. code:: python

                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'some/description',
                    '--target-dir', 'some/target-dir'
                ]

        :param bool update_check: check for box updates True|False
        :param bool snapshot: run box in snapshot mode True|False
        :param bool keep_open: keep VM running True|False
        :param str kiwi_version: pip install this kiwi version
        :param str custom_shared_path: make this path available in the box
        """
        self.kiwi_build_command = kiwi_build_command
        desc = self._pop_arg_param(
            '--description'
        )
        target_dir = self._pop_arg_param(
            '--target-dir'
        )
        BoxBuildDefaults.create_build_target_dir(target_dir)
        try:
            vm_setup = self.box.fetch(update_check, snapshot)
        except Exception as issue:
            raise KiwiBoxDownloadError(
                f'Failed to fetch box file(s): {issue}'
            )
        vm_append = [
            vm_setup.append,
            'kiwi=\\"{0}\\"'.format(' '.join(self.kiwi_build_command))
        ]
        if self.console:
            vm_append[0] = vm_append[0].replace(
                f'console={vm_setup.console}', f'console={self.console}'
            )
        if keep_open:
            vm_append.append('kiwi-no-halt')
        if kiwi_version:
            vm_append.append('kiwi_version=_{0}_'.format(kiwi_version))
        if custom_shared_path:
            vm_append.append('custom_mount=_{0}_'.format(custom_shared_path))
        if self.sharing_backend == 'sshfs':
            ssh_key_file = os.sep.join(
                [os.environ.get('HOME') or '~', '.ssh', f'{self.ssh_key}.pub']
            )
            if not os.path.isfile(ssh_key_file):
                raise KiwiBoxSSHKeyNotFound(
                    f'SSH pkey file {ssh_key_file} not found, use --ssh-key'
                )
            with open(ssh_key_file) as key_fd:
                ssh_key = key_fd.read().split()
                key_type = ssh_key[0]
                key_value = ssh_key[1]
                vm_append.append(f'ssh_key=_{key_value}_')
                vm_append.append(f'ssh_key_type=_{key_type}_')
            user = pwd.getpwuid(os.geteuid()).pw_name
            vm_append.append(
                'host_kiwidescription=_{0}_'.format(
                    f'{user}@localhost:{desc}'
                )
            )
            vm_append.append(
                'host_kiwibundle=_{0}_'.format(
                    f'{user}@localhost:{target_dir}'
                )
            )
            if custom_shared_path:
                vm_append.append(
                    'host_custompath=_{0}_'.format(
                        f'{user}@localhost:{custom_shared_path}'
                    )
                )
        vm_append.append(
            'sharing_backend=_{0}_'.format(self.sharing_backend)
        )
        vm_machine = []
        if self.machine:
            vm_machine.append('-machine')
            vm_machine.append(self.machine)

        if self.accel:
            vm_machine.append('-accel')
            vm_machine.append('accel=kvm')

        if len(self.ssh_port) > 0:
            if not self.ssh_port.isdigit():
                raise KiwiBoxSSHPortInvalid(
                    f'Invalid SSH port: {self.ssh_port} '
                    '(must be a positive integer)'
                )
            BoxBuildDefaults.box_ssh_port_forwarded_to_host = int(self.ssh_port)

        vm_machine.append('-cpu')
        vm_machine.append(self.cpu)
        vm_memory = format(self.ram or vm_setup.ram)
        qemu_binary = self._find_qemu_call_binary()
        if not qemu_binary:
            raise KiwiBoxQEMUBinaryNotFound(
                f'No QEMU binary for {self.arch} found'
            )
        vm_run = [
            qemu_binary,
            '-m', vm_memory
        ] + vm_machine + [
        ] + BoxBuildDefaults.get_qemu_generic_setup() + [
            '-kernel', vm_setup.kernel,
            '-append', '"{0}"'.format(' '.join(vm_append))
        ] + BoxBuildDefaults.get_qemu_storage_setup(
            vm_setup.system, snapshot
        ) + \
            BoxBuildDefaults.get_qemu_network_setup() + \
            BoxBuildDefaults.get_qemu_console_setup() + \
            BoxBuildDefaults.get_qemu_shared_path_setup(
                0, desc, 'kiwidescription', self.sharing_backend) + \
            BoxBuildDefaults.get_qemu_shared_path_setup(
                1, target_dir, 'kiwibundle', self.sharing_backend)
        if custom_shared_path:
            vm_run += BoxBuildDefaults.get_qemu_shared_path_setup(
                2, custom_shared_path, 'custompath', self.sharing_backend
            )
        if self.sharing_backend == 'virtiofs':
            vm_run += [
                '-object', '{0},id=mem,size={1},mem-path={2},share=on'.format(
                    'memory-backend-file', vm_memory, '/dev/shm'
                ),
                '-numa', 'node,memdev=mem'
            ]
        if vm_setup.initrd:
            vm_run += ['-initrd', vm_setup.initrd]
        if vm_setup.smp:
            vm_run += ['-smp', format(self.smp or vm_setup.smp)]
        os.environ['TMPDIR'] = BoxBuildDefaults.get_local_box_cache_dir()
        log.debug(
            'Set TMPDIR: {0}'.format(os.environ['TMPDIR'])
        )
        if self.sharing_backend == 'sshfs':
            log.debug('Initiating port forwarding')
            # delete eventual existing host key for localhost on
            # the kvm forwared box ssh port box_ssh_port_forwarded_to_host
            # this is required because the host ssh key changes
            # with every kvm box run. ssh identifies this as
            # a potential man-in-the-middle attack and will disable
            # port forwarding which is required though.
            Command.run(
                [
                    'ssh-keygen', '-R',
                    '[localhost]:{0}'.format(
                        runtime.BoxBuildDefaults.box_ssh_port_forwarded_to_host
                    )
                ], raise_on_error=False
            )
            # remote forward the host ssh port(22) into the box
            # at port HOST_SSH_PORT_FORWARDED_TO_BOX using the kvm forwarded
            # box ssh port box_ssh_port_forwarded_to_host. This action only
            # completes successfully when the box has started up and is
            # ready to operate through ssh
            ssh_forward_thread = Thread(
                target=self._forward_host_ssh_to_guest,
                args=()
            )
            ssh_forward_thread.start()
        log.debug(
            'Calling Qemu: {0}'.format(vm_run)
        )
        os.system(
            ' '.join(vm_run)
        )
        for virtiofsd_process in runtime.VIRTIOFSD_PROCESS_LIST:
            virtiofsd_process.terminate()

        exit_code_file = os.sep.join(
            [target_dir, BoxBuildDefaults.result_exitcode_name]
        )
        build_log_file = os.sep.join(
            [target_dir, BoxBuildDefaults.result_log_name]
        )
        self.kiwi_exit = 0
        if os.path.exists(exit_code_file):
            with open(exit_code_file) as exit_code:
                self.kiwi_exit = int(exit_code.readline())

        if self.kiwi_exit != 0:
            raise KiwiBoxBuildError(
                f'Box build failed. Find build log at: {build_log_file!r}'
            )

        log.info(
            f'Box build done. Find build log at: {build_log_file!r}'
        )

    def _pop_arg_param(self, arg: str) -> str:
        arg_index = self.kiwi_build_command.index(arg)
        arg_value = ''
        if arg_index:
            arg_value = self.kiwi_build_command[arg_index + 1]
            del self.kiwi_build_command[arg_index + 1]
            del self.kiwi_build_command[arg_index]
        return arg_value

    def _find_qemu_call_binary(self) -> str:
        qemu_by_system = Path.which(f'qemu-system-{self.arch}')
        if qemu_by_system:
            return qemu_by_system
        if self.arch == 'x86_64':
            return Path.which('qemu-kvm') or ''
        return ''

    def _forward_host_ssh_to_guest(self) -> None:
        while self.kiwi_exit is None:
            try:
                Command.run(
                    [
                        'ssh', '-NT',
                        '-o', 'StrictHostKeyChecking=no',
                        'root@localhost',
                        '-p',
                        format(
                            runtime.BoxBuildDefaults.box_ssh_port_forwarded_to_host
                        ),
                        '-R',
                        '{0}:localhost:22'.format(
                            runtime.HOST_SSH_PORT_FORWARDED_TO_BOX
                        )
                    ]
                )
            except Exception as issue:
                log.debug(issue)
            time.sleep(2)
