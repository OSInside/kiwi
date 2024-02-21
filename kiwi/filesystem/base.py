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
import logging
import copy
from typing import (
    Dict, List, Optional
)

# project
import kiwi.defaults as defaults

from kiwi.defaults import Defaults
from kiwi.utils.sync import DataSync
from kiwi.mount_manager import MountManager
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.utils.veritysetup import VeritySetup

from kiwi.exceptions import (
    KiwiFileSystemSyncError
)

log = logging.getLogger('kiwi')


class FileSystemBase:
    """
    **Implements base class for filesystem interface**

    :param object device_provider:
        Instance of a class based on DeviceProvider
        required for filesystems which needs a block device for
        creation. In most cases the DeviceProvider is a LoopDevice
    :param string root_dir: root directory path name
    :param dict custom_args: custom filesystem arguments
    """
    def __init__(
        self, device_provider: DeviceProvider,
        root_dir: str = '', custom_args: Dict = {}
    ):
        # filesystems created with a block device stores the mountpoint
        # here. The file name of the file containing the filesystem is
        # stored in the device_provider if the filesystem is represented
        # as a file there
        self.filesystem_mount: Optional[MountManager] = None

        # the underlaying device provider. This is only required if the
        # filesystem required a block device to become created
        self.device_provider = device_provider

        self.root_dir = root_dir

        # filesystems created without a block device stores the result
        # filesystem file name here
        self.filename = ''

        self.custom_args: Dict = {}
        self.post_init(custom_args)
        self.veritysetup: Optional[VeritySetup] = None

    def __enter__(self):
        return self

    def post_init(self, custom_args: Dict):
        """
        Post initialization method

        Store dictionary of custom arguments if not empty. This
        overrides the default custom argument hash

        :param dict custom_args: custom arguments

            .. code:: python

                {
                    'create_options': ['option'],
                    'mount_options': ['option'],
                    'meta_data': {
                        'key': 'value'
                    }
                }
        """
        if custom_args:
            self.custom_args = copy.deepcopy(custom_args)

        if not self.custom_args.get('create_options'):
            self.custom_args['create_options'] = []

        if not self.custom_args.get('meta_data'):
            self.custom_args['meta_data'] = {}

        if not self.custom_args.get('mount_options'):
            self.custom_args['mount_options'] = []

        if not self.custom_args.get('fs_attributes'):
            self.custom_args['fs_attributes'] = []

    def set_uuid(self):
        """
        Create new random filesystem UUID

        Implement in specialized filesystem class for filesystems which
        supports the concept of an UUID and allows to change it
        """
        log.warning(
            'Instance {0} has no support for setting a new UUID label'.format(
                type(self).__name__
            )
        )

    def create_on_device(
        self, label: str = None, size: int = 0, unit: str = defaults.UNIT.kb,
        uuid: str = None
    ):
        """
        Create filesystem on block device

        Implement in specialized filesystem class for filesystems which
        requires a block device for creation, e.g ext4.

        :param str label: label name
        :param int size:
            size value, can also be counted from the end via -X
            The value is interpreted in units of: unit
        :param str unit:
            unit name. Default unit is set to: defaults.UNIT.kb
        :param str uuid: UUID name
        """
        raise NotImplementedError

    def create_on_file(
        self, filename: str, label: str = None, exclude: List[str] = None
    ):
        """
        Create filesystem from root data tree

        Implement in specialized filesystem class for filesystems which
        requires a data tree for creation, e.g squashfs.

        :param string filename: result file path name
        :param string label: label name
        :param list exclude: list of exclude dirs/files
        """
        raise NotImplementedError

    def get_mountpoint(self) -> Optional[str]:
        """
        Provides mount point directory

        Effective use of the directory is guaranteed only after sync_data

        :return: directory path name

        :rtype: string
        """
        if self.filesystem_mount:
            return self.filesystem_mount.mountpoint
        return None

    def sync_data(self, exclude: List[str] = []) -> MountManager:
        """
        Copy data tree into filesystem

        :param list exclude: list of exclude dirs/files
        :return: The mount created for syncing data. It should be used to
            un-mount the filesystem again.
        """
        if not self.root_dir:
            raise KiwiFileSystemSyncError(
                'no root directory specified'
            )
        if not os.path.exists(self.root_dir):
            raise KiwiFileSystemSyncError(
                'given root directory %s does not exist' % self.root_dir
            )
        self.filesystem_mount = MountManager(
            device=self.device_provider.get_device()
        )
        self.filesystem_mount.mount(
            self.custom_args['mount_options']
        )
        self._apply_attributes()
        data = DataSync(
            self.root_dir, self.filesystem_mount.mountpoint
        )
        data.sync_data(
            exclude=exclude, options=Defaults.get_sync_options()
        )
        return self.filesystem_mount

    def create_verity_layer(
        self, blocks: Optional[int] = None, filename: str = None
    ):
        """
        Create veritysetup on device

        :param int block:
            Number of blocks to use for veritysetup.
            If not specified the entire root device is used
        :param str filename:
            Target filename to use for VeritySetup.
            If not specified the filename or block special
            provided at object construction time is used
        """
        on_file_name = filename or self.filename
        self.veritysetup = VeritySetup(
            on_file_name or self.device_provider.get_device(),
            blocks
        )
        log.info(
            '--> Creating dm verity hash ({0} blocks)...'.format(
                blocks or 'all'
            )
        )
        log.debug(
            '--> dm verity metadata: {0}'.format(self.veritysetup.format())
        )

    def create_verification_metadata(self, device_node: str = '') -> None:
        """
        Write verification block at the end of the device

        :param str device_node:
            Target device node, if not specified the root device
            from this instance is used
        """
        if self.veritysetup:
            log.info('--> Creating verification metadata...')
            self.veritysetup.create_verity_verification_metadata()
            log.info('--> Signing verification metadata...')
            self.veritysetup.sign_verification_metadata()
            self.veritysetup.write_verification_metadata(
                device_node or self.device_provider.get_device()
            )

    def mount(self) -> None:
        """
        Mount the filesystem
        """
        if self.filesystem_mount:
            self.filesystem_mount.mount(
                self.custom_args['mount_options']
            )

    def umount(self) -> None:
        """
        Umounts the filesystem in case it is mounted, does nothing otherwise
        """
        if self.filesystem_mount:
            log.info('umount %s instance', type(self).__name__)
            self.filesystem_mount.umount()

    def umount_volumes(self) -> None:
        """
        Consistency layer with regards to VolumeManager classes

        Invokes umount
        """
        self.umount()

    def mount_volumes(self) -> None:
        """
        Consistency layer with regards to VolumeManager classes

        Invokes mount
        """
        self.mount()

    def get_volumes(self) -> Dict:
        """
        Consistency layer with regards to VolumeManager classes

        Raises
        """
        raise NotImplementedError

    def get_root_volume_name(self) -> None:
        """
        Consistency layer with regards to VolumeManager classes

        Raises
        """
        raise NotImplementedError

    def get_fstab(
        self, persistency_type: str = 'by-label', filesystem_name: str = ''
    ) -> List[str]:
        """
        Consistency layer with regards to VolumeManager classes

        Raises
        """
        raise NotImplementedError

    def set_property_readonly_root(self) -> None:
        """
        Consistency layer with regards to VolumeManager classes

        Raises
        """
        raise NotImplementedError

    def _map_size(self, size: float, from_unit: str, to_unit: str) -> float:
        """
        Return byte size value for given size and unit

        :param float size:
            requested filesystem size. The value is interpreted
            by the given from_unit.

        :param str from_unit: source unit
        :param str to_unit: target unit

        :return: size value in unit: to_unit

        :rtype: float
        """
        unit_map = {
            defaults.UNIT.byte: 1,
            defaults.UNIT.kb: 1024,
            defaults.UNIT.mb: 1048576,
            defaults.UNIT.gb: 1073741824
        }
        byte_size = size * unit_map[from_unit]
        return byte_size / unit_map[to_unit]

    def _fs_size(
        self, size: float, blocksize: int = 1, unit: str = defaults.UNIT.kb
    ) -> str:
        """
        Calculate filesystem size parameter in number of blocksize
        blocks. If the given size is <= 0 the calculation is done from
        the actual size of the block device reduced by the given size

        :param float size:
            requested filesystem size. The value is interpreted
            by the given unit.

        :param int blocksize:
            blocksize as requested from the filesystem creation tool
            for specifying the filesystem size. The value is interpreted
            by the given unit. By default set to: 1

        :param str unit:
            Unit to use for calculations and return value
            Default unit is set to: defaults.UNIT.kb

        :return: an int block count of the specified unit as str

        :rtype: str
        """
        if size > 0:
            result_size = size / blocksize
        else:
            device_name = self.device_provider.get_device()
            device_byte_size = self.device_provider.get_byte_size(device_name)
            requested_byte_size = self._map_size(size, unit, defaults.UNIT.byte)
            result_size = self._map_size(
                (device_byte_size + requested_byte_size) / blocksize,
                from_unit=defaults.UNIT.byte, to_unit=unit
            )
        return format(int(result_size))

    def _apply_attributes(self):
        """
        Apply filesystem attributes
        """
        attribute_map = {
            'synchronous-updates': '+S',
            'no-copy-on-write': '+C'
        }
        for attribute in self.custom_args['fs_attributes']:
            if attribute_map.get(attribute):
                log.info(
                    '--> setting {0} for {1}'.format(
                        attribute, self.filesystem_mount.mountpoint
                    )
                )
                Command.run(
                    [
                        'chattr', attribute_map.get(attribute),
                        self.filesystem_mount.mountpoint
                    ]
                )

    def __exit__(self, exc_type, exc_value, traceback):
        self.umount()
