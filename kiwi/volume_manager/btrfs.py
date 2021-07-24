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
import logging
import shutil
import datetime
from xml.etree import ElementTree
from xml.dom import minidom
from typing import List

# project
import kiwi.defaults as defaults

from kiwi.command import Command
from kiwi.volume_manager.base import VolumeManagerBase
from kiwi.mount_manager import MountManager
from kiwi.storage.mapped_device import MappedDevice
from kiwi.filesystem import FileSystem
from kiwi.utils.sync import DataSync
from kiwi.utils.block import BlockID
from kiwi.utils.sysconfig import SysConfig
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiVolumeRootIDError,
    KiwiVolumeManagerSetupError
)

log = logging.getLogger('kiwi')


class VolumeManagerBtrfs(VolumeManagerBase):
    """
    Implements btrfs sub-volume management

    :param list subvol_mount_list: list of mounted btrfs subvolumes
    :param object toplevel_mount: :class:`MountManager` for root mountpoint
    """
    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom btrfs initialization arguments

        :param list custom_args: custom btrfs volume manager arguments
        """
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'root_label' not in self.custom_args:
            self.custom_args['root_label'] = 'ROOT'
        if 'root_is_snapshot' not in self.custom_args:
            self.custom_args['root_is_snapshot'] = False
        if 'root_is_readonly_snapshot' not in self.custom_args:
            self.custom_args['root_is_readonly_snapshot'] = False
        if 'quota_groups' not in self.custom_args:
            self.custom_args['quota_groups'] = False

        self.subvol_mount_list = []
        self.toplevel_mount = None
        self.toplevel_volume = None

    def setup(self, name=None):
        """
        Setup btrfs volume management

        In case of btrfs a toplevel(@) subvolume is created and marked
        as default volume. If snapshots are activated via the custom_args
        the setup method also created the @/.snapshots/1/snapshot
        subvolumes. There is no concept of a volume manager name, thus
        the name argument is not used for btrfs

        :param string name: unused
        """
        self.setup_mountpoint()

        filesystem = FileSystem.new(
            name='btrfs',
            device_provider=MappedDevice(
                device=self.device, device_provider=self.device_provider_root
            ),
            custom_args=self.custom_filesystem_args
        )
        filesystem.create_on_device(
            label=self.custom_args['root_label']
        )
        self.toplevel_mount = MountManager(
            device=self.device, mountpoint=self.mountpoint
        )
        self.toplevel_mount.mount(
            self.custom_filesystem_args['mount_options']
        )
        if self.custom_args['quota_groups']:
            Command.run(
                ['btrfs', 'quota', 'enable', self.mountpoint]
            )
        root_volume = self.mountpoint + '/@'
        Command.run(
            ['btrfs', 'subvolume', 'create', root_volume]
        )
        if self.custom_args['root_is_snapshot']:
            snapshot_volume = self.mountpoint + '/@/.snapshots'
            Command.run(
                ['btrfs', 'subvolume', 'create', snapshot_volume]
            )
            volume_mount = MountManager(
                device=self.device,
                mountpoint=self.mountpoint + '/.snapshots'
            )
            self.subvol_mount_list.append(volume_mount)
            Path.create(snapshot_volume + '/1')
            snapshot = self.mountpoint + '/@/.snapshots/1/snapshot'
            Command.run(
                ['btrfs', 'subvolume', 'snapshot', root_volume, snapshot]
            )
            self._set_default_volume('@/.snapshots/1/snapshot')
        else:
            self._set_default_volume('@')

    def create_volumes(self, filesystem_name):
        """
        Create configured btrfs subvolumes

        Any btrfs subvolume is of the same btrfs filesystem. There is no
        way to have different filesystems per btrfs subvolume. Thus
        the filesystem_name has no effect for btrfs

        :param string filesystem_name: unused
        """
        log.info(
            'Creating %s sub volumes', filesystem_name
        )
        self.create_volume_paths_in_root_dir()

        canonical_volume_list = self.get_canonical_volume_list()
        if canonical_volume_list.full_size_volume:
            # put an eventual fullsize volume to the volume list
            # because there is no extra handling required for it on btrfs
            canonical_volume_list.volumes.append(
                canonical_volume_list.full_size_volume
            )

        for volume in canonical_volume_list.volumes:
            if volume.is_root_volume:
                # the btrfs root volume named '@' has been created as
                # part of the setup procedure
                pass
            else:
                log.info('--> sub volume %s', volume.realpath)
                toplevel = self.mountpoint + '/@/'
                volume_parent_path = os.path.normpath(
                    toplevel + os.path.dirname(volume.realpath)
                )
                if not os.path.exists(volume_parent_path):
                    Path.create(volume_parent_path)
                Command.run(
                    [
                        'btrfs', 'subvolume', 'create',
                        os.path.normpath(toplevel + volume.realpath)
                    ]
                )
                self.apply_attributes_on_volume(
                    toplevel, volume
                )
                if self.custom_args['root_is_snapshot']:
                    snapshot = self.mountpoint + '/@/.snapshots/1/snapshot/'
                    volume_mount = MountManager(
                        device=self.device,
                        mountpoint=os.path.normpath(snapshot + volume.realpath)
                    )
                    self.subvol_mount_list.append(
                        volume_mount
                    )

    def get_fstab(self, persistency_type='by-label', filesystem_name=None):
        """
        Implements creation of the fstab entries. The method
        returns a list of fstab compatible entries

        :param string persistency_type: by-label | by-uuid
        :param string filesystem_name: unused

        :return: list of fstab entries

        :rtype: list
        """
        fstab_entries = []
        mount_options = \
            self.custom_filesystem_args['mount_options'] or ['defaults']
        block_operation = BlockID(self.device)
        blkid_type = 'LABEL' if persistency_type == 'by-label' else 'UUID'
        device_id = block_operation.get_blkid(blkid_type)
        for volume_mount in self.subvol_mount_list:
            subvol_name = self._get_subvol_name_from_mountpoint(volume_mount)
            mount_entry_options = mount_options + ['subvol=' + subvol_name]
            fs_check = self._is_volume_enabled_for_fs_check(
                volume_mount.mountpoint
            )
            fstab_entry = ' '.join(
                [
                    blkid_type + '=' + device_id, subvol_name.replace('@', ''),
                    'btrfs', ','.join(mount_entry_options),
                    '0 {fs_passno}'.format(
                        fs_passno='2' if fs_check else '0'
                    )
                ]
            )
            fstab_entries.append(fstab_entry)
        return fstab_entries

    def get_volumes(self):
        """
        Return dict of volumes

        :return: volumes dictionary

        :rtype: dict
        """
        volumes = {}
        for volume_mount in self.subvol_mount_list:
            subvol_name = self._get_subvol_name_from_mountpoint(volume_mount)
            subvol_options = ','.join(
                [
                    'subvol=' + subvol_name
                ] + self.custom_filesystem_args['mount_options']
            )
            volumes[subvol_name.replace('@', '')] = {
                'volume_options': subvol_options,
                'volume_device': volume_mount.device
            }
        return volumes

    def mount_volumes(self):
        """
        Mount btrfs subvolumes
        """
        self.toplevel_mount.mount(
            self.custom_filesystem_args['mount_options']
        )

        for volume_mount in self.subvol_mount_list:
            if self.volumes_mounted_initially:
                volume_mount.mountpoint = os.path.normpath(
                    volume_mount.mountpoint.replace(self.toplevel_volume, '', 1)
                )
            if not os.path.exists(volume_mount.mountpoint):
                Path.create(volume_mount.mountpoint)
            subvol_name = self._get_subvol_name_from_mountpoint(volume_mount)
            subvol_options = ','.join(
                [
                    'subvol=' + subvol_name
                ] + self.custom_filesystem_args['mount_options']
            )
            volume_mount.mount(
                options=[subvol_options]
            )

        self.volumes_mounted_initially = True

    def umount_volumes(self):
        """
        Umount btrfs subvolumes

        :return: True if all subvolumes are successfully unmounted

        :rtype: bool
        """
        all_volumes_umounted = True
        for volume_mount in reversed(self.subvol_mount_list):
            if volume_mount.is_mounted():
                if not volume_mount.umount():
                    all_volumes_umounted = False

        if all_volumes_umounted:
            if self.toplevel_mount.is_mounted():
                if not self.toplevel_mount.umount():
                    all_volumes_umounted = False

        return all_volumes_umounted

    def get_mountpoint(self) -> str:
        """
        Provides btrfs root mount point directory

        Effective use of the directory is guaranteed only after sync_data

        :return: directory path name

        :rtype: string
        """
        sync_target: List[str] = [self.mountpoint, '@']
        if self.custom_args.get('root_is_snapshot'):
            sync_target.extend(['.snapshots', '1', 'snapshot'])
        return os.path.join(*sync_target)

    def sync_data(self, exclude=None):
        """
        Sync data into btrfs filesystem

        If snapshots are activated the root filesystem is synced
        into the first snapshot

        :param list exclude: files to exclude from sync
        """
        if self.toplevel_mount:
            sync_target = self.get_mountpoint()
            if self.custom_args['root_is_snapshot']:
                self._create_snapshot_info(
                    ''.join([self.mountpoint, '/@/.snapshots/1/info.xml'])
                )
            data = DataSync(self.root_dir, sync_target)
            data.sync_data(
                options=Defaults.get_sync_options(), exclude=exclude
            )
            if self.custom_args['quota_groups'] and \
               self.custom_args['root_is_snapshot']:
                self._create_snapper_quota_configuration()

    def set_property_readonly_root(self):
        """
        Sets the root volume to be a readonly filesystem
        """
        root_is_snapshot = \
            self.custom_args['root_is_snapshot']
        root_is_readonly_snapshot = \
            self.custom_args['root_is_readonly_snapshot']
        if root_is_snapshot and root_is_readonly_snapshot:
            sync_target = self.mountpoint
            Command.run(
                ['btrfs', 'property', 'set', sync_target, 'ro', 'true']
            )

    def _is_volume_enabled_for_fs_check(self, mountpoint):
        for volume in self.volumes:
            if volume.realpath in mountpoint:
                if 'enable-for-filesystem-check' in volume.attributes:
                    return True
        return False

    def _set_default_volume(self, default_volume):
        subvolume_list_call = Command.run(
            ['btrfs', 'subvolume', 'list', self.mountpoint]
        )
        for subvolume in subvolume_list_call.output.split('\n'):
            id_search = re.search('ID (\d+) .*path (.*)', subvolume)
            if id_search:
                volume_id = id_search.group(1)
                volume_path = id_search.group(2)
                if volume_path == default_volume:
                    Command.run(
                        [
                            'btrfs', 'subvolume', 'set-default',
                            volume_id, self.mountpoint
                        ]
                    )
                    self.toplevel_volume = default_volume
                    return

        raise KiwiVolumeRootIDError(
            'Failed to find btrfs volume: %s' % default_volume
        )

    def _xml_pretty(self, toplevel_element):
        xml_data_unformatted = ElementTree.tostring(
            toplevel_element, 'utf-8'
        )
        xml_data_domtree = minidom.parseString(xml_data_unformatted)
        return xml_data_domtree.toprettyxml(indent="    ")

    def _create_snapper_quota_configuration(self):
        root_path = os.sep.join([self.mountpoint, '@/.snapshots/1/snapshot'])
        snapper_default_conf = os.path.normpath(os.sep.join(
            [root_path, Defaults.get_snapper_config_template_file()]
        ))
        if os.path.exists(snapper_default_conf):
            # snapper requires an extra parent qgroup to operate with quotas
            Command.run(
                ['btrfs', 'qgroup', 'create', '1/0', self.mountpoint]
            )
            config_file = self._set_snapper_sysconfig_file(root_path)
            if not os.path.exists(config_file):
                shutil.copyfile(snapper_default_conf, config_file)
            Command.run([
                'chroot', root_path, 'snapper', '--no-dbus', 'set-config',
                'QGROUP=1/0'
            ])

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
            raise KiwiVolumeManagerSetupError(
                'Unsupported SNAPPER_CONFIGS value: {0}'.format(
                    sysconf_file['SNAPPER_CONFIGS']
                )
            )
        return os.sep.join([
            root_path, 'etc/snapper/configs',
            sysconf_file['SNAPPER_CONFIGS'].strip('\"')]
        )

    def _create_snapshot_info(self, filename):
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

        with open(filename, 'w') as snapshot_info_file:
            snapshot_info_file.write(self._xml_pretty(snapshot))

    def _get_subvol_name_from_mountpoint(self, volume_mount):
        path_start_index = len(defaults.TEMP_DIR.split(os.sep)) + 1
        subvol_name = os.sep.join(
            volume_mount.mountpoint.split(os.sep)[path_start_index:]
        )
        if self.toplevel_volume and self.toplevel_volume in subvol_name:
            subvol_name = subvol_name.replace(self.toplevel_volume, '')
        return os.path.normpath(os.sep.join(['@', subvol_name]))

    def __del__(self):
        if self.toplevel_mount:
            log.info('Cleaning up %s instance', type(self).__name__)
            if not self.umount_volumes():
                log.warning('Subvolumes still busy')
