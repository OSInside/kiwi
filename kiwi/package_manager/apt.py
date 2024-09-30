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
import re
import os
import glob
import logging
import pathlib
from typing import (
    List, Dict
)

# project
from kiwi.command import CommandCallT
from kiwi.command import Command
from kiwi.path import Path
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.repository.apt import RepositoryApt
from kiwi.utils.temporary import Temporary

import kiwi.defaults as defaults

from kiwi.exceptions import (
    KiwiDebianBootstrapError,
    KiwiRequestError,
    KiwiFileNotFound
)

log = logging.getLogger('kiwi')


class PackageManagerApt(PackageManagerBase):
    """
    **Implements Installation/Deletion of packages/collections with apt-get**

    :param list apt_get_args:
        apt-get arguments from repository runtime configuration
    :param dict command_env:
        apt-get command environment from repository
        runtime configuration
    """
    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom apt-get arguments

        :param list custom_args: custom apt-get arguments
        """
        self.repository: RepositoryApt = self.repository
        self.custom_args = custom_args

        self.deboostrap_minbase: bool = True

        runtime_config = self.repository.runtime_config()
        self.apt_get_args = runtime_config['apt_get_args']
        self.command_env = runtime_config['command_env']
        self.distribution = runtime_config['distribution']
        self.distribution_path = runtime_config['distribution_path']

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name: str) -> None:
        """
        Queue a collection request

        There is no collection definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Collection(%s) handling not supported for apt-get', name
        )

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        There is no product definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Product(%s) handling not supported for apt-get', name
        )

    def request_package_exclusion(self, name: str) -> None:
        """
        Queue a package exclusion(skip) request

        Package exclusion for apt package manager not yet implemented

        :param str name: unused
        """
        log.warning(
            'Package exclusion for (%s) not supported for apt-get', name
        )

    def setup_repository_modules(
        self, collection_modules: Dict[str, List[str]]
    ) -> None:
        """
        Repository modules not supported for apt-get
        The method does nothing in this scope

        :param dict collection_modules: unused
        """
        pass

    def process_install_requests_bootstrap(
        self, root_bind: RootBind = None, bootstrap_package: str = None
    ) -> CommandCallT:
        """
        Process package install requests for bootstrap phase (no chroot)
        Either a manual unpacking strategy or a prebuilt bootstrap
        package can be used to bootstrap a new system.

        :param object root_bind:
            unused
        :param str bootstrap_package:
            package name of a bootstrap package

        :return: process results as command instance

        :rtype: command_call_type
        """
        if bootstrap_package:
            return self._process_install_requests_bootstrap_prebuild_root(
                bootstrap_package
            )
        else:
            return self._process_install_requests_bootstrap()

    def _process_install_requests_bootstrap_prebuild_root(
        self, bootstrap_package: str
    ) -> CommandCallT:
        """
        Process bootstrap phase (no chroot) using a prebuilt bootstrap
        package. The package has to provide a tarball below the
        directory /var/cache/kiwi/bootstrap/PACKAGE_NAME.ARCH.tar.xz
        and will be unpacked to serve as the bootstrap root.

        The optionally listed packages in the kiwi bootstrap section
        will be installed as part of a chroot install and returned
        as command instance

        :param str bootstrap_package:
            package name of the bootstrap package containing the
            bootstrap root as a tarball

        :return: process results as command instance

        :rtype: command_call_type
        """
        # Install prebuilt bootstrap package on build host
        update_command = [
            'apt-get'
        ] + self.apt_get_args + self.custom_args + [
            'update'
        ]
        install_command = [
            'apt-get'
        ] + self.apt_get_args + self.custom_args + [
            'install', bootstrap_package
        ]
        Command.run(
            update_command, self.command_env
        )
        Command.run(
            install_command, self.command_env
        )
        # Unpack prebuilt bootstrap root tarball as new root
        bootstrap_root_tarball = '/var/lib/bootstrap/{0}.{1}.tar.xz'.format(
            bootstrap_package, defaults.PLATFORM_MACHINE
        )
        if not os.path.isfile(bootstrap_root_tarball):
            raise KiwiFileNotFound(
                f'bootstrap tarball: {bootstrap_root_tarball!r} not found'
            )
        Command.run(
            ['tar', '-C', self.root_dir, '-xf', bootstrap_root_tarball]
        )
        # Install eventual bootstrap packages as standard system install
        return self.process_install_requests()

    def _process_install_requests_bootstrap(self) -> CommandCallT:
        """
        Process package install requests for bootstrap phase (no chroot).

        :raises KiwiDebianBootstrapError

        :return: process results in command type

        :rtype: CommandCallT
        """
        # we invoke apt-get install to download all the essential packages.
        # With DPkg::Pre-Install-Pkgs, we specify a shell command that will
        # receive the list of packages that will be installed on stdin.
        # By configuring Debug::pkgDpkgPm=1, apt-get install will not
        # actually execute any dpkg commands, so all it does is download
        # the essential debs and tell us their full in the apt cache without
        # actually installing them.
        try:
            # TODO: Drop once apt 2.5.4 is widely available.
            pathlib.Path(f'{self.root_dir}/var/lib/dpkg').mkdir(
                parents=True, exist_ok=True
            )
            pathlib.Path(f'{self.root_dir}/var/lib/dpkg/status.kiwi').touch()
            pathlib.Path(f'{self.root_dir}/var/lib/dpkg/available').touch()

            if 'apt' not in self.package_requests:
                self.package_requests.append('apt')
            update_cache = [
                'apt-get'
            ] + self.apt_get_args + self.custom_args + [
                'update'
            ]
            result = Command.run(
                update_cache, self.command_env
            )
            log.debug(
                'Apt update: {0} {1}'.format(result.output, result.error)
            )
            package_names = Temporary(prefix='kiwi_debs_').new_file()
            download_bootstrap = [
                'apt-get'
            ] + self.apt_get_args + self.custom_args + [
                'install',
                '-oDebug::pkgDPkgPm=1',
                f'-oDPkg::Pre-Install-Pkgs::=cat >{package_names.name}',
                '?essential'
            ] + self.package_requests
            # Download solved bootstrap packages
            result = Command.run(
                download_bootstrap, self.command_env
            )
            log.debug(
                'Apt download: {0} {1}'.format(result.output, result.error)
            )
            # Extract bootstrap packages
            with open(package_names.name) as packages:
                solved_debootstrap_packages = [p.rstrip() for p in packages]
            self.command_env['PATH'] = '$PATH:/usr/bin:/bin:/usr/sbin:/sbin'
            for package in solved_debootstrap_packages:
                Command.run(
                    [
                        'bash', '-c',
                        'dpkg-deb --fsys-tarfile {0} | tar -C {1} -x'.format(
                            package, self.root_dir
                        )
                    ], self.command_env
                )
            # Run package scripts. Unfortuantely Debian based systems
            # requires special sauce for bootstrap. See the exceptions
            # we have to apply below:
            #
            # * manual order is required to make sure users(root) exists
            # * the usr-merge strategy only works after bootstrap
            #
            # 1. Pass: Run package scripts, manual order
            self._run_bootstrap_scripts(
                solved_debootstrap_packages,
                only_for=['base-passwd'], skip=['usrmerge']
            )
            # 2. Pass: Run package scripts in apt order
            self._run_bootstrap_scripts(
                solved_debootstrap_packages,
                skip=['usrmerge']
            )
            self.cleanup_requests()
            return Command.call(
                update_cache, self.command_env
            )
        except Exception as e:
            raise KiwiDebianBootstrapError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        update_command = ['chroot', self.root_dir, 'apt-get']
        update_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        update_command.extend(self.custom_args)
        update_command.append('update')
        Command.run(update_command, self.command_env)

        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('install')
        apt_get_command.extend(self._package_requests())

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: true|false

        :raises KiwiRequestError: if none of the packages to delete is
            installed
        :return: process results in command type

        :rtype: namedtuple
        """
        delete_items = []
        for delete_item in self._package_requests():
            try:
                Command.run(
                    ['chroot', self.root_dir, 'dpkg', '-l', delete_item]
                )
                delete_items.append(delete_item)
            except Exception:
                # ignore packages which are not installed
                pass
        if not delete_items:
            raise KiwiRequestError(
                'None of the requested packages to delete are installed'
            )

        # deleting debs for some reason can also trigger package
        # scripts from the libc-bin (glibc) package. This often
        # results in calls like ldconfig which failed unless the
        # system would be really running. Since the deletion
        # happens via chroot and with the system in offline mode
        # many attempts to uninstall a package, even cracefully
        # failed for this reason. So far I only saw the workaround
        # to make ldconfig a noop during the process of uninstall.
        # This is not a nice solution and I dislike it. However,
        # the only one I could come up with to turn the package
        # uninstall in a useful feature in kiwi.
        Command.run(
            [
                'cp',
                f'{self.root_dir}/usr/sbin/ldconfig',
                f'{self.root_dir}/usr/sbin/ldconfig.orig'
            ]
        )
        Command.run(
            [
                'cp',
                f'{self.root_dir}/usr/bin/true',
                f'{self.root_dir}/usr/sbin/ldconfig'
            ]
        )
        if force:
            # force deleting debs only worked well for me when ignoring
            # the pre/post-inst and pre/post-remove codings. No idea why it
            # ends in so many conflicts but if you want to force get rid
            # of stuff this was the only way I could come up with. There
            # are still cases when it does not work depending on the many
            # code that runs on deleting
            for package in delete_items:
                pre_delete_pattern = \
                    f'{self.root_dir}/var/lib/dpkg/info/{package}*.pre*'
                post_delete_pattern = \
                    f'{self.root_dir}/var/lib/dpkg/info/{package}*.post*'
                for delete_file in glob.iglob(pre_delete_pattern):
                    Path.wipe(delete_file)
                for delete_file in glob.iglob(post_delete_pattern):
                    Path.wipe(delete_file)

            apt_get_command = ['chroot', self.root_dir, 'dpkg']
            apt_get_command.extend(
                [
                    '--remove',
                    '--force-remove-reinstreq',
                    '--force-remove-essential',
                    '--force-depends'
                ]
            )
            apt_get_command.extend(delete_items)
        else:
            apt_get_command = ['chroot', self.root_dir, 'apt-get']
            apt_get_command.extend(
                Path.move_to_root(self.root_dir, self.apt_get_args)
            )
            apt_get_command.extend(self.custom_args)
            apt_get_command.extend(['--auto-remove', 'remove'])
            apt_get_command.extend(delete_items)

        return Command.call(
            apt_get_command, self.command_env
        )

    def post_process_delete_requests(
        self, root_bind: RootBind = None
    ) -> None:
        """
        Revert system changes done prior deleting packages

        :param object root_bind: unused
        """
        Command.run(
            [
                'mv',
                f'{self.root_dir}/usr/sbin/ldconfig.orig',
                f'{self.root_dir}/usr/sbin/ldconfig'
            ]
        )

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('upgrade')

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--no-install-recommends' not in self.custom_args:
            self.custom_args.append('--no-install-recommends')
        self.deboostrap_minbase = True

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--no-install-recommends' in self.custom_args:
            self.custom_args.remove('--no-install-recommends')
        self.deboostrap_minbase = False

    def match_package_installed(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the apt-get command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param str package_name: package_name
        :param str package_manager_output: apt-get status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Unpacking {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def match_package_deleted(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been deleted

        :param str package_name: package_name
        :param str package_manager_output: apt-get status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Removing {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def _package_requests(self) -> List:
        items = self.package_requests[:]
        self.cleanup_requests()
        return items

    def _run_bootstrap_scripts(
        self, solved_debootstrap_packages: List[str],
        only_for: List[str] = [], skip: List[str] = []
    ):
        # TODO: this should not be needed but without setting
        # the following environment variables no package pre/post
        # script completes its task. I leave it up to the Debian
        # experts to provide a fix if needed.
        self.command_env['DPKG_MAINTSCRIPT_NAME'] = 'true'
        self.command_env['DPKG_MAINTSCRIPT_PACKAGE'] = 'libc6'

        post_script_dir = Temporary(
            prefix='kiwi_debpost.', path=self.root_dir
        ).new_dir()
        for package in solved_debootstrap_packages:
            package_base_name = os.path.basename(package)
            go_ahead = False if only_for else True
            for name in only_for:
                if name in package_base_name:
                    go_ahead = True
                    break
            for name in skip:
                if name in package_base_name:
                    go_ahead = False
                    break
            if not go_ahead:
                continue
            log.debug(
                f'Running pre/post scripts for: {package_base_name}'
            )
            package_metadata_dir = \
                f'{post_script_dir.name}/{os.path.basename(package)}'
            Command.run(
                ['dpkg', '-e', package, package_metadata_dir]
            )
            script_pre = f'{package_metadata_dir}/preinst'
            script_post = f'{package_metadata_dir}/postinst'
            # 1. preinst
            if os.path.exists(script_pre):
                Command.run(
                    [
                        'chroot', self.root_dir, 'bash',
                        f'{script_pre.replace(self.root_dir, "")}', 'install'
                    ], self.command_env
                )
            # 2. postinst
            if os.path.exists(script_post):
                Command.run(
                    [
                        'chroot', self.root_dir, 'bash',
                        f'{script_post.replace(self.root_dir, "")}', 'configure'
                    ], self.command_env
                )
