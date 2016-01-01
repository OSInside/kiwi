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
from collections import OrderedDict
import os
import re

# project
from command import Command
from disk_format_base import DiskFormatBase
from logger import log

from exceptions import (
    KiwiVmdkToolsError
)


class DiskFormatVmdk(DiskFormatBase):
    """
        create vmdk image format
    """
    def post_init(self, custom_args):
        self.options = []
        if custom_args:
            self.options.append('-o')
            ordered_args = OrderedDict(custom_args.items())
            for key, value in custom_args.iteritems():
                self.options.append(key)
                self.options.append(value)

    def create_image_format(self):
        Command.run(
            [
                'qemu-img', 'convert', '-c', '-f', 'raw', self.diskname,
                '-O', 'vmdk'
            ] + self.options + [
                self.get_target_name_for_format('vmdk')
            ]
        )
        self.__update_vmdk_descriptor()

    def __update_vmdk_descriptor(self):
        """
            Update the VMDK descriptor with the VMware tools version
            and type information. This is done to let VMware's virtualization
            infrastructure know about the installed VMware tools at boot
            time of the image within a VMware virtual environment
            e.g VCloud Air. It's required to have vmtoolsd installed as
            part of the image. If not found a warning is provided to the
            user and the VMDK descriptor stays untouched
        """
        vmdk_vmtoolsd = self.source_dir + '/usr/bin/vmtoolsd'
        if not os.path.exists(vmdk_vmtoolsd):
            log.warning(
                'Could not find vmtoolsd in image root %s' % self.source_dir
            )
            log.warning(
                'Update of VMDK metadata skipped'
            )
            return
        log.info('Updating VMDK metadata')
        vmdk_tools_install_type = 4
        vmdk_tools_version = self.__get_vmdk_tools_version()
        vmdk_image_name = self.get_target_name_for_format('vmdk')
        log.info(
            '--> Setting tools version: %d', vmdk_tools_version
        )
        log.info(
            '--> Setting tools install type: %d', vmdk_tools_install_type
        )
        vmdk_descriptor_call = Command.run(
            ['dd', 'if=' + vmdk_image_name, 'bs=1', 'count=1024', 'skip=512']
        )
        vmdk_descriptor_lines = vmdk_descriptor_call.output.split('\n')
        vmdk_descriptor_lines.insert(0, 'encoding="UTF-8"')
        vmdk_descriptor_lines.append(
            'ddb.toolsInstallType = "%s"' % vmdk_tools_install_type
        )
        vmdk_descriptor_lines.append(
            'ddb.toolsVersion = "%s"' % vmdk_tools_version
        )
        with open(vmdk_image_name, 'wb') as vmdk:
            vmdk.seek(512, 0)
            vmdk.write('\n'.join(vmdk_descriptor_lines))
            vmdk.seek(0, 2)

    def __get_vmdk_tools_version(self):
        vmdk_tools_version_call = Command.run(
            ['chroot', self.source_dir, 'vmtoolsd', '--version']
        )
        vmdk_tools_version = vmdk_tools_version_call.output
        vmdk_tools_version_format = re.match(
            ''.join(
                [
                    '^VMware Tools daemon, version ',
                    '(.*)',
                    '\.',
                    '(.*)',
                    '\.',
                    '(.*)',
                    '\.',
                    '(.*?)',
                    ' \(.*\)',
                    '$'
                ]
            ), vmdk_tools_version
        )
        if vmdk_tools_version_format:
            return \
                (int(vmdk_tools_version_format.group(1)) * 1024) + \
                (int(vmdk_tools_version_format.group(2)) * 32) + \
                int(vmdk_tools_version_format.group(3))
        else:
            raise KiwiVmdkToolsError(
                'vmtools version %s does not match format' % vmdk_tools_version
            )
