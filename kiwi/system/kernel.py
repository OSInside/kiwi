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
from typing import (
    NamedTuple, Optional, List, Tuple, Union
)

# project
from kiwi.command import Command

from kiwi.exceptions import KiwiKernelLookupError

kernel_type = NamedTuple(
    'kernel_type', [
        ('name', str),
        ('filename', str),
        ('version', str)
    ]
)
xen_hypervisor_type = NamedTuple(
    'xen_hypervisor_type', [
        ('filename', str),
        ('name', str)
    ]
)


class Kernel:
    """
    **Implementes kernel lookup and extraction from given root tree**

    If more than one kernel is installed in the root tree, the
    kernel of the latest version is used. The version of a kernel
    is the name of its modules directory, which is also the version
    the initrd gets created for, see get_kernel_versions()

    :param str root_dir: root directory path name
    :param list kernel_names: list of kernel names to search for
        functions.sh::suseStripKernel() provides a normalized
        file so that we do not have to search for many different
        names in this code
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.kernel_names = self._setup_kernel_names_for_lookup()

    def get_kernel(
        self, raise_on_not_found: bool = False
    ) -> Optional[kernel_type]:
        """
        Lookup kernel files and provide filename and version

        :param bool raise_on_not_found: sets the method to raise an exception
            if the kernel is not found

        :raises KiwiKernelLookupError: if raise_on_not_found flag is active
            and kernel is not found
        The kernel names are ordered by kernel version, latest first,
        see _setup_kernel_names_for_lookup(). The first existing kernel
        file is therefore the kernel of the latest version which is
        installed. Its version is taken from the kernel name, which is
        relative to the root tree: a path of the root tree itself does
        not affect it

        :return: tuple with filename, kernelname and version

        :rtype: tuple|None
        """
        kernel_patterns = [
            r'^boot/[^/-]+-(.+)$',
            r'^(?:usr/)?lib/modules/([^/]+)/[^/]+$'
        ]
        for kernel_name in self.kernel_names:
            kernel_file = os.sep.join(
                [self.root_dir, kernel_name]
            )
            if os.path.exists(kernel_file):
                for kernel_pattern in kernel_patterns:
                    version_match = re.match(kernel_pattern, kernel_name)
                    if version_match:
                        version = version_match.group(1)
                        return kernel_type(
                            name=os.path.basename(
                                os.path.realpath(kernel_file)
                            ),
                            filename=kernel_file,
                            version=version
                        )
        if raise_on_not_found:
            raise KiwiKernelLookupError(
                'No kernel found in {0}, searched for {1}'.format(
                    self.root_dir, self.kernel_names
                )
            )
        return None

    def get_kernel_versions(self) -> List[str]:
        """
        Provide the versions of the kernels installed in the root tree,
        latest first

        The version of a kernel is the name of its modules directory
        below lib/modules or usr/lib/modules. The directories are not
        ordered by their name but by version, see version_key(), e.g
        6.10.1 is later than 6.9.12. A version which is installed
        below both directories, e.g with lib being a link to usr/lib,
        is only listed once

        :return: list of kernel versions

        :rtype: list
        """
        kernel_versions = set()
        kernel_module_dirs = [
            os.sep.join([self.root_dir, 'lib/modules']),
            os.sep.join([self.root_dir, 'usr/lib/modules'])
        ]
        for kernel_module_dir in kernel_module_dirs:
            if os.path.isdir(kernel_module_dir):
                kernel_versions.update(os.listdir(kernel_module_dir))
        return sorted(
            kernel_versions,
            key=lambda version: (Kernel.version_key(version), version),
            reverse=True
        )

    def get_version_in_name(self, name: str) -> Optional[str]:
        """
        Provide the version of the installed kernel the given file
        name refers to, e.g 6.4.0-1-default for initrd-6.4.0-1-default

        The installed versions are looked for in the name longest
        first, a version does not match within a longer one, e.g 6.1
        within initramfs-6.10.img

        :param str name: file name

        :return: kernel version or None

        :rtype: str|None
        """
        for version in sorted(
            self.get_kernel_versions(),
            key=lambda version: (-len(version), version)
        ):
            if version in name:
                return version
        return None

    @staticmethod
    def version_key(version: str) -> List[Tuple[int, Union[int, str]]]:
        """
        Provide a sort key which orders kernel versions by version
        rather than by name

        The version is split into its numeric and alphabetic parts,
        all other characters only separate them, like rpm does it.
        Numeric parts are compared as numbers, alphabetic parts as
        strings and a numeric part is later than an alphabetic one.
        A version which continues where another one ends is the later
        one, e.g:

        6.4.0-150600.23.7-default < 6.4.0-150600.23.25-default
        6.9.12-1-default < 6.10.1-1-default

        :param str version: kernel version

        :return: sort key

        :rtype: list
        """
        return [
            (1, int(part)) if part.isdigit() else (0, part)
            for part in re.findall(r'[0-9]+|[a-zA-Z]+', version)
        ]

    def get_xen_hypervisor(self) -> Optional[xen_hypervisor_type]:
        """
        Lookup xen hypervisor and provide filename and hypervisor name

        :return: tuple with filename and hypervisor name

        :rtype: tuple|None
        """
        xen_hypervisor = self.root_dir + '/boot/xen.gz'
        if os.path.exists(xen_hypervisor):
            return xen_hypervisor_type(
                filename=xen_hypervisor,
                name='xen.gz'
            )
        return None

    def copy_kernel(self, target_dir: str, file_name: str = None) -> None:
        """
        Copy kernel to specified target

        If no file_name is given the target filename is set
        as kernel-<kernel.version>.kernel

        :param str target_dir: target path name
        :param str filename: base filename in target
        """
        kernel = self.get_kernel()
        if kernel:
            if not file_name:
                file_name = 'kernel-' + kernel.version + '.kernel'
            target_file = ''.join(
                [target_dir, '/', file_name]
            )
            Command.run(['cp', kernel.filename, target_file])

    def copy_xen_hypervisor(
        self, target_dir: str, file_name: str = None
    ) -> None:
        """
        Copy xen hypervisor to specified target

        If no file_name is given the target filename is set
        as hypervisor-<xen.name>

        :param str target_dir: target path name
        :param str filename: base filename in target
        """
        xen = self.get_xen_hypervisor()
        if xen:
            if not file_name:
                file_name = 'hypervisor-' + xen.name
            target_file = ''.join(
                [target_dir, '/', file_name]
            )
            Command.run(['cp', xen.filename, target_file])

    def _setup_kernel_names_for_lookup(self) -> List[str]:
        """
        The kernel image name is different per arch and distribution
        This method returns a list of possible kernel image names in
        order to search and find one of them

        The names are ordered by kernel version, latest first, and
        only then by the image name prefixes. All names of a version
        come before the names of an earlier version, the kernel of a
        later version is found first no matter its image name

        :return: list of kernel image names

        :rtype: list
        """
        kernel_names = []
        kernel_dirs = self.get_kernel_versions()
        if kernel_dirs:
            # append lookup for the real kernel image names
            # depending on the arch and os they are different
            # in their prefix
            kernel_prefixes = [
                'uImage', 'Image', 'zImage', 'vmlinuz', 'image', 'vmlinux', 'kernel'
            ]
            for kernel_dir in kernel_dirs:
                for kernel_prefix in kernel_prefixes:
                    # add kernel names to be found in boot
                    kernel_names.append(
                        f'boot/{kernel_prefix}-{kernel_dir}'
                    )
                    # add kernel names to be found in modules
                    kernel_names.append(
                        f'lib/modules/{kernel_dir}/{kernel_prefix}'
                    )
                    kernel_names.append(
                        f'usr/lib/modules/{kernel_dir}/{kernel_prefix}'
                    )
        return kernel_names
