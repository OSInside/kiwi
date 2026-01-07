# Copyright (c) 2025 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import shutil
import datetime
from typing import List
from xml.etree import ElementTree
from xml.dom import minidom

# project
from kiwi.command import Command
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.snapshot_manager.base import SnapshotManagerBase
from kiwi.mount_manager import MountManager
from kiwi.utils.sysconfig import SysConfig
from kiwi.chroot_manager import (
    ChrootManager, ChrootMount
)
from kiwi.exceptions import (
    KiwiSnapshotManagerSetupError
)


class SnapshotManagerSnapper(SnapshotManagerBase):
    """
    **Implements the snapshots management for Snapper**

    :param str device: storage device node name
    :param str root_dir: root directory path
    :param str mountpoint: mountpoint of the filesystem to snapshot
    :param str root_volume_name: the name of the root volume in case
        snapshots are hosted in a subvolume.
    """
    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom snapper manager initialization arguments

        :param dict custom_args: custom snapper manager arguments
        """
        self.default_snapshot_name = \
            f'/{self.root_volume_name}/.snapshots/1/snapshot'
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'quota_groups' not in self.custom_args:
            self.custom_args['quota_groups'] = False

    def create_first_snapshot(self) -> List[MountManager]:
        """
        Creates the first snapshot on an empty filesystem

        In fact it is essentially creating an empty subvolume
        following the snapper's structure and convetion to store
        snapshots

        :return: list of additional mountpoints added on top of the given
            root mountpoint

        :rtype: list
        """
        snapshot_path = os.path.normpath(os.sep.join([
            self.mountpoint,
            self.default_snapshot_name
        ]))
        snapshot_path = self.mountpoint + self.default_snapshot_name
        if CommandCapabilities.check_version(
            'snapper', (0, 12, 1), root=self.root_dir
        ):
            with ChrootManager(
                self.root_dir, binds=[ChrootMount(self.mountpoint)]
            ) as chroot:
                chroot.run([
                    '/usr/lib/snapper/installation-helper', '--root-prefix',
                    os.sep.join([self.mountpoint, self.root_volume_name]),
                    '--step', 'filesystem'
                ])
        else:
            # with snapper <= 0.12.0 the first snapshot subvolume
            # structure is crafted manually
            snapshot_volume = self.mountpoint + \
                f'/{self.root_volume_name}/.snapshots'
            Command.run(
                ['btrfs', 'subvolume', 'create', snapshot_volume]
            )
            os.chmod(snapshot_volume, 0o700)
            Path.create(snapshot_volume + '/1')
            Command.run(
                ['btrfs', 'subvolume', 'create', snapshot_path]
            )
            Command.run(
                ['btrfs', 'subvolume', 'set-default', snapshot_path]
            )

        # Mount /{some-name}/.snapshots as /.snapshots inside the root
        snapshots_mount = MountManager(
            device=self.device,
            attributes={
                'subvol_path': f'{self.root_volume_name}/.snapshots',
                'subvol_name': f'{self.root_volume_name}/.snapshots'
            },
            mountpoint=snapshot_path + '/.snapshots'
        )
        return [snapshots_mount]

    def setup_first_snapshot(self):
        """
        Arranges the snapshot configuration once the OS tree is synched.
        It uses the snapper and the data from the snapshot itself.
        """
        snapshot_path = os.path.normpath(os.sep.join([
            self.mountpoint,
            self.default_snapshot_name
        ]))
        if CommandCapabilities.check_version(
            'snapper', (0, 12, 1), root=snapshot_path
        ):
            snapshots_prefix = os.sep.join([snapshot_path, '.snapshots'])
            with ChrootManager(
                self.root_dir, binds=[
                    ChrootMount(snapshot_path), ChrootMount(snapshots_prefix)
                ]
            ) as chroot:
                chroot.run([
                    '/usr/lib/snapper/installation-helper', '--root-prefix',
                    snapshot_path, '--step', 'config', '--description',
                    'first root filesystem'
                ])
        else:
            # with snapper <= 0.12.0 the snapshot configuration is
            # crafted manually
            date_info = datetime.datetime.now()
            snapshot = ElementTree.Element('snapshot')

            snapshot_type = ElementTree.SubElement(snapshot, 'type')
            snapshot_type.text = 'single'

            snapshot_number = ElementTree.SubElement(snapshot, 'num')
            snapshot_number.text = '1'

            snapshot_description = ElementTree.SubElement(snapshot, 'description')
            snapshot_description.text = 'first root filesystem'

            snapshot_date = ElementTree.SubElement(snapshot, 'date')
            snapshot_date.text = date_info.strftime("%Y-%m-%d %H:%M:%S")

            with open(os.path.join(snapshot_path, '../info.xml'), 'w') as snapshot_info_file:
                snapshot_info_file.write(self._xml_pretty(snapshot))

        if self.custom_args['quota_groups']:
            snapper_default_conf = Defaults.get_snapper_config_template_file(
                snapshot_path
            )
            if snapper_default_conf:
                # snapper requires an extra parent qgroup to operate with quotas
                Command.run(
                    ['btrfs', 'qgroup', 'create', '1/0', self.mountpoint]
                )
                config_file = self._set_snapper_sysconfig_file(snapshot_path)
                if not os.path.exists(config_file):
                    shutil.copyfile(snapper_default_conf, config_file)
                with ChrootManager(snapshot_path) as chroot:
                    chroot.run([
                        'snapper', '--no-dbus', 'set-config', 'QGROUP=1/0'
                    ])
        with ChrootManager(snapshot_path) as chroot:
            chroot.run([
                'snapper', '--no-dbus', 'modify', '--default', '1'
            ])

    def get_default_snapshot_name(self) -> str:
        """
        Gets the name of the default snapshot for snapper

        :return: default snapper snapshot path

        :rtype: string
        """
        return self.default_snapshot_name

    def _xml_pretty(self, toplevel_element):
        xml_data_unformatted = ElementTree.tostring(
            toplevel_element, 'utf-8'
        )
        xml_data_domtree = minidom.parseString(xml_data_unformatted)
        return xml_data_domtree.toprettyxml(indent="    ")

    @staticmethod
    def _set_snapper_sysconfig_file(root_path):
        sysconf_file = SysConfig(
            os.sep.join([root_path, 'etc/sysconfig/snapper'])
        )
        if not sysconf_file.get('SNAPPER_CONFIGS') or \
           len(sysconf_file['SNAPPER_CONFIGS'].strip('\"')) == 0:

            sysconf_file['SNAPPER_CONFIGS'] = '"root"'
            sysconf_file.write()
        elif len(sysconf_file['SNAPPER_CONFIGS'].split()) > 1:
            raise KiwiSnapshotManagerSetupError(
                'Unsupported SNAPPER_CONFIGS value: {0}'.format(
                    sysconf_file['SNAPPER_CONFIGS']
                )
            )
        return os.sep.join([
            root_path, 'etc/snapper/configs',
            sysconf_file['SNAPPER_CONFIGS'].strip('\"')]
        )
