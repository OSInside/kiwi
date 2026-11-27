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
import re
import pathlib
import subprocess
from subprocess import Popen
from typing import List, Optional

# project
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiBoxVirtioFsError,
    KiwiBoxTargetPathError,
    KiwiBoxBuildError,
)

VIRTIOFSD_PROCESS_LIST: List[Popen[bytes]] = []
HOST_SSH_PORT_FORWARDED_TO_BOX = 10000


class BoxBuildDefaults:
    """
    **Implements default values for the boxbuild command**

    Provides static methods for default values and state information
    """

    box_ssh_port_forwarded_to_host = 10022
    result_log_name = 'result.log'
    result_exitcode_name = 'result.code'

    @staticmethod
    def get_box_config_file() -> str:
        """
        Config file name: `kiwi_boxed_plugin.yml`
        Locations are searched in this order:
            1. ENV variable: $KIWI_BOXED_PLUGIN_CFG
               full path to file, name is freely selectable
            2. $PWD/kiwi_boxed_plugin.yml
            3. $HOME/.config/kiwi/kiwi_boxed_plugin.yml
            4. /etc/kiwi_boxed_plugin.yml
            5. Resource (default config, coming with kiwi)
        """
        return BoxBuildDefaults._get_box_resource_file(
            'kiwi_boxed_plugin.yml', 'KIWI_BOXED_PLUGIN_CFG'
        )

    @staticmethod
    def get_box_keyring_file() -> str:
        """
        Keyring file name: `kiwi_boxed_plugin.gpg`

        The keyring holds the trusted public keys, the signatures
        of the box checksum files are verified with. The keyring
        coming with kiwi holds the signing key of the open build
        service project Virtualization:Appliances, which builds
        the boxes of the default config. Boxes signed with other
        keys require a custom keyring. Locations are searched in
        the same order as for the config file:
            1. ENV variable: $KIWI_BOXED_PLUGIN_KEYRING
               full path to file, name is freely selectable
            2. $PWD/kiwi_boxed_plugin.gpg
            3. $HOME/.config/kiwi/kiwi_boxed_plugin.gpg
            4. /etc/kiwi_boxed_plugin.gpg
            5. Resource (default keyring, coming with kiwi)
        """
        # an absolute path, such that the keyring used for the
        # signature verification is clearly identified in the log
        return os.path.abspath(
            BoxBuildDefaults._get_box_resource_file(
                'kiwi_boxed_plugin.gpg', 'KIWI_BOXED_PLUGIN_KEYRING'
            )
        )

    @staticmethod
    def _get_box_resource_file(name: str, env_name: str) -> str:
        # 1.
        path_env: str = os.environ.get(env_name) or ''
        if path_env and os.path.exists(path_env):
            return path_env

        # 2.
        path_pwd = os.path.abspath(name)
        if os.path.exists(path_pwd):
            return path_pwd

        # 3.
        path_home: pathlib.Path = pathlib.Path.home().joinpath(
            f'.config/kiwi/{name}'
        )
        if path_home.exists():
            return path_home.as_posix()

        # 4.
        path_system = f'/etc/{name}'
        if os.path.exists(path_system):
            return path_system

        # 5.
        return Defaults.project_file(f'config/{name}')

    @staticmethod
    def get_local_box_cache_dir() -> str:
        local_box_cache_dir_env: Optional[str] = os.environ.get(
            'KIWI_BOXED_CACHE_DIR'
        )
        if local_box_cache_dir_env and os.path.isdir(local_box_cache_dir_env):
            return local_box_cache_dir_env
        return f'{os.environ.get("HOME")}/.kiwi_boxes'

    @staticmethod
    def get_qemu_generic_setup() -> List[str]:
        return ['-nographic', '-nodefaults', '-snapshot']

    @staticmethod
    def get_qemu_network_setup() -> List[str]:
        return [
            '-nic',
            'user,model=virtio,hostfwd=tcp::{0}-:22'.format(
                BoxBuildDefaults.box_ssh_port_forwarded_to_host
            ),
        ]

    @staticmethod
    def get_qemu_shared_path_setup(
        index: int, path: str, mount_tag: str, sharing_backend: str = '9p'
    ) -> List[str]:
        shared_setup: List[str] = []
        if sharing_backend == '9p':
            shared_setup = BoxBuildDefaults.get_qemu_shared_path_setup_9p(
                index, path, mount_tag
            )
        if sharing_backend == 'virtiofs':
            shared_setup = BoxBuildDefaults.get_qemu_shared_path_setup_virtiofs(
                index, path, mount_tag
            )
        return shared_setup

    @staticmethod
    def get_qemu_shared_path_setup_9p(
        index: int, path: str, mount_tag: str
    ) -> List[str]:
        return [
            '-fsdev',
            'local,security_model=mapped,id=fsdev{0},path={1}'.format(
                index, path
            ),
            '-device',
            'virtio-9p-pci,id=fs{0},fsdev=fsdev{0},mount_tag={1}'.format(
                index, mount_tag
            ),
        ]

    @staticmethod
    def get_qemu_shared_path_setup_virtiofs(
        index: int, path: str, mount_tag: str
    ) -> List[str]:
        virtiofsd_lookup_paths = {
            'PATH': '/usr/libexec:/usr/lib/virtiofsd:/usr/lib/qemu/virtiofsd'
        }
        virtiofsd = Path.which('virtiofsd', virtiofsd_lookup_paths)
        if not virtiofsd:
            raise KiwiBoxVirtioFsError(
                'virtiofsd not found in: {0}'.format(virtiofsd_lookup_paths)
            )
        try:
            virtiofsd_process = subprocess.Popen(
                [
                    virtiofsd,
                    '--socket-path=/tmp/vhostqemu_{0}'.format(index),
                    '--shared-dir',
                    os.path.abspath(path),
                    '--sandbox',
                    'namespace',
                    '--cache',
                    'always',
                    '--allow-direct-io',
                    '--posix-acl',
                    '--xattr',
                ],
                close_fds=True,
            )
        except Exception as issue:
            raise KiwiBoxVirtioFsError(
                'Failed to start virtiofsd: {0}'.format(issue)
            )
        VIRTIOFSD_PROCESS_LIST.append(virtiofsd_process)
        return [
            '-chardev',
            'socket,id=char{0},path=/tmp/vhostqemu_{0}'.format(index),
            '-device',
            'vhost-user-fs-pci,queue-size=1024,chardev=char{0},tag={1}'.format(
                index, mount_tag
            ),
        ]

    @staticmethod
    def get_qemu_console_setup() -> List[str]:
        return [
            '-device',
            'virtio-serial',
            '-chardev',
            'stdio,id=virtiocon0',
            '-device',
            'virtconsole,chardev=virtiocon0',
        ]

    @staticmethod
    def get_qemu_storage_setup(
        image_file: str, snapshot: bool = True
    ) -> List[str]:
        return [
            '-drive',
            'file={0},if=virtio,driver=qcow2,cache=off,snapshot={1}'.format(
                image_file, 'on' if snapshot else 'off'
            ),
        ]

    @staticmethod
    def create_build_target_dir(target_dir: str) -> None:
        try:
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
            build_log_file = os.path.join(
                target_dir, BoxBuildDefaults.result_log_name
            )
            pathlib.Path(build_log_file).touch()
        except Exception as issue:
            raise KiwiBoxTargetPathError(
                f'Failed to create/setup target path {target_dir}: {issue}'
            )

    @staticmethod
    def get_kiwi_git_box_args(kiwi_git: str) -> List[str]:
        """
        Translate a kiwi git link into the box variables used by
        the box to clone and install kiwi from source.

        The link can be specified as repository URL with an
        optional branch reference in the web URL notation:

        .. code:: shell

            https://github.com/OSInside/kiwi
            https://github.com/OSInside/kiwi/tree/BRANCH_NAME

        :param str kiwi_git: kiwi git link

        :return: box variables, Example:

            .. code:: python

                [
                    'kiwi_git_repo=_https://github.com/OSInside/kiwi_',
                    'kiwi_git_branch=_BRANCH_NAME_'
                ]

        :rtype: list
        """
        # The information is passed along as box variable on the
        # kernel/container command line and is evaluated by a shell
        # in the box. Thus only allow characters that are safe in
        # this context
        if not re.match(r'^[\w.~:/@+%-]+$', kiwi_git or ''):
            raise KiwiBoxBuildError(f'Invalid kiwi git link: {kiwi_git!r}')
        repo, tree, branch = kiwi_git.partition('/tree/')
        repo = repo.rstrip('/')
        if repo.endswith('/-'):
            # gitlab web URL notation: REPO/-/tree/BRANCH_NAME
            repo = repo[:-2]
        branch = branch.strip('/')
        if not repo or (tree and not branch):
            raise KiwiBoxBuildError(f'Invalid kiwi git link: {kiwi_git!r}')
        box_args = [f'kiwi_git_repo=_{repo}_']
        if branch:
            box_args.append(f'kiwi_git_branch=_{branch}_')
        return box_args
