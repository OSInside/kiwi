# Copyright (c) 2026 Marcus Schäfer.  All rights reserved.
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
import hmac
import json
import uuid
import hashlib
import logging
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple

# project
from kiwi.command import Command
from kiwi.defaults import Defaults
import kiwi.defaults as defaults
from kiwi.path import Path
from kiwi.utils.temporary import Temporary
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.utils.reproducible import Reproducible
from kiwi.xml_state import volume_type

log = logging.getLogger('kiwi')

# kiwi platform name to systemd architecture name
REPART_ARCHITECTURES = {
    'x86_64': 'x86-64',
    'aarch64': 'arm64',
    'armv7l': 'arm',
    'riscv64': 'riscv64',
    'loongarch64': 'loongarch64',
    'ppc64le': 'ppc64-le',
    's390x': 's390x',
}

# prefix of the environment variables systemd-repart takes extra mkfs
# options from, followed by the filesystem name in upper case
REPART_MKFS_OPTIONS = 'SYSTEMD_REPART_MKFS_OPTIONS_'


class RepartMkfsTool(NamedTuple):
    """
    mkfs tool of a filesystem and the first version of it that
    creates the filesystem reproducible with SOURCE_DATE_EPOCH.
    For btrfs and XFS the DETERMINISTIC_SEED environment variable
    is needed in addition

    :param str tool: mkfs tool name, e.g. mke2fs
    :param str version_flag: option to print the version
    :param str channel: output channel the version is printed to
    :param tuple min_version: first reproducible version
    :param str package: package that provides the tool
    """

    tool: str
    version_flag: str
    channel: Literal['stdout', 'stderr']
    min_version: Tuple[int, ...]
    package: str


# mkfs tool by repart filesystem name
REPART_MKFS_REPRODUCIBLE: Dict[str, RepartMkfsTool] = {
    'ext2': RepartMkfsTool('mke2fs', '-V', 'stderr', (1, 47, 1), 'e2fsprogs'),
    'ext3': RepartMkfsTool('mke2fs', '-V', 'stderr', (1, 47, 1), 'e2fsprogs'),
    'ext4': RepartMkfsTool('mke2fs', '-V', 'stderr', (1, 47, 1), 'e2fsprogs'),
    'btrfs': RepartMkfsTool(
        'mkfs.btrfs', '--version', 'stdout', (7, 3), 'btrfs-progs'
    ),
    'xfs': RepartMkfsTool('mkfs.xfs', '-V', 'stdout', (6, 18), 'xfsprogs'),
}

# filesystems whose mkfs tool takes the DETERMINISTIC_SEED environment
# variable to derive its internal UUIDs and random values
REPART_DETERMINISTIC_SEED = ['btrfs', 'xfs']


class RepartPartition(NamedTuple):
    """
    Partition as created by systemd-repart

    :param str name: kiwi partition map name, e.g. efi, swap or root
    :param str partition_type: repart partition type, e.g. esp or root
    :param str label: partition and filesystem label
    :param str uuid: partition UUID
    :param str filesystem: repart filesystem name, e.g. ext4 or swap
    :param int mbsize: partition size, 0 uses the remaining space
    :param list copy_files: source:target pairs copied into the filesystem
    :param list exclude_files: source paths excluded from copy_files
    :param list make_directories: directories created in the filesystem
    :param list exclude_files_target:
        target paths excluded from copy_files, unlike exclude_files
        only effective for the copy_files entries whose target
        contains the path
    :param list subvolumes:
        btrfs subvolume paths in the filesystem, a path with the
        suffix :ro creates a read-only subvolume
    :param str default_subvolume:
        btrfs default subvolume path, one of the subvolumes
    :param str compression:
        compression algorithm for the data copied into the
        filesystem, e.g zstd for btrfs
    :param int compression_level:
        compression level of the compression algorithm, only
        effective with compression
    :param list mkfs_options:
        additional options for the mkfs tool of the filesystem
    """

    name: str
    partition_type: str
    label: str
    uuid: str
    filesystem: str
    mbsize: int = 0
    copy_files: Optional[List[str]] = None
    exclude_files: Optional[List[str]] = None
    make_directories: Optional[List[str]] = None
    exclude_files_target: Optional[List[str]] = None
    subvolumes: Optional[List[str]] = None
    default_subvolume: Optional[str] = None
    compression: Optional[str] = None
    compression_level: Optional[int] = None
    mkfs_options: Optional[List[str]] = None


class RepartBtrfsVolume(NamedTuple):
    """
    btrfs subvolume of a root filesystem created by systemd-repart

    :param str path: subvolume path in the filesystem, e.g /@/home
    :param str mountpoint: mount point of the subvolume, e.g /home
    :param bool filesystem_check: enable the subvolume for fsck
    """

    path: str
    mountpoint: str
    filesystem_check: bool = False


class RepartBtrfsLayout:
    """
    **Subvolume layout of a btrfs root filesystem created by systemd-repart**

    Provides the subvolume layout the kiwi btrfs volume manager
    creates on a mounted filesystem, see VolumeManagerBtrfs, in
    terms of systemd-repart partition settings:

    * The root tree is stored in the toplevel of the filesystem or
      in the root subvolume, /@ by default. With root_is_snapshot
      the root tree is stored in the first snapper snapshot
      /@/.snapshots/1/snapshot and /@/.snapshots is mounted at
      /.snapshots
    * Each volume is a subvolume below its parent, which is the
      root subvolume if the volume has no parent attribute, and
      it is mounted at its mount point by subvol= mount option
    * The root subvolume or snapshot is the default subvolume if
      requested. A snapshot is always the default subvolume

    :param list volumes: volumes, see XMLState.get_volumes
    :param bool root_is_subvolume:
        store the root tree in a subvolume, None stands for True
        as with the btrfs volume manager
    :param bool root_is_snapshot:
        store the root tree in the first snapper snapshot
    :param bool root_is_readonly_snapshot:
        create the snapshot read-only
    :param bool default_volume_requested:
        make the root subvolume the default subvolume
    """

    def __init__(
        self,
        volumes: List[volume_type],
        root_is_subvolume: Optional[bool],
        root_is_snapshot: bool = False,
        root_is_readonly_snapshot: bool = False,
        default_volume_requested: bool = True,
    ) -> None:
        if root_is_subvolume is None:
            # same default and deprecation warning as the
            # btrfs volume manager
            log.warning('Implicitly creating root volume')
            log.warning('--> Future versions of kiwi will not do this anymore')
            log.warning('--> Please specify btrfs_root_is_subvolume true|false')
            root_is_subvolume = True
        self.root_volume_name = '/'
        if root_is_subvolume:
            self.root_volume_name = '@'
            for volume in volumes:
                if volume.is_root_volume and volume.name:
                    self.root_volume_name = volume.name
        if root_is_snapshot and self.root_volume_name == '/':
            log.warning(
                'root_is_snapper_snapshot requires a toplevel sub-volume'
            )
            log.warning('root_is_snapper_snapshot has been disabled')
            root_is_snapshot = False
        self.root_is_snapshot = root_is_snapshot
        self.root_is_readonly_snapshot = bool(
            root_is_snapshot and root_is_readonly_snapshot
        )
        self.default_volume_requested = default_volume_requested
        self.root_volume_path = self._abspath(self.root_volume_name)
        self.snapshots_path: Optional[str] = None
        self.root_path = self.root_volume_path
        if self.root_is_snapshot:
            self.snapshots_path = self.root_volume_path + '/.snapshots'
            self.root_path = self.snapshots_path + '/1/snapshot'

        volume_by_mountpoint: Dict[str, RepartBtrfsVolume] = {}
        for volume in volumes:
            if volume.is_root_volume or volume.realpath in ['/', 'swap']:
                continue
            mountpoint = self._abspath(volume.realpath)
            volume_by_mountpoint[mountpoint] = RepartBtrfsVolume(
                path=self._abspath(
                    volume.parent or self.root_volume_name, volume.realpath
                ),
                mountpoint=mountpoint,
                filesystem_check=(
                    'enable-for-filesystem-check' in volume.attributes
                ),
            )
        # volumes in the order they are mounted
        self.volumes: List[RepartBtrfsVolume] = [
            volume_by_mountpoint[mountpoint]
            for mountpoint in Path.sort_by_hierarchy(
                sorted(volume_by_mountpoint.keys())
            )
        ]

    def get_mount_volumes(self) -> List[RepartBtrfsVolume]:
        """
        Subvolumes mounted by fstab in the order they are mounted,
        the volumes and the snapper snapshots subvolume

        :return: list of RepartBtrfsVolume

        :rtype: list
        """
        mount_volumes = list(self.volumes)
        if self.snapshots_path:
            mount_volumes.append(
                RepartBtrfsVolume(self.snapshots_path, '/.snapshots')
            )
        mount_volumes.sort(key=lambda volume: volume.mountpoint.count('/'))
        return mount_volumes

    def get_path(self, path: str) -> str:
        """
        Location of the given path of the root tree in the
        filesystem, taking into account the volume it is stored in

        :param str path: path in the root tree, e.g /boot

        :return: path in the filesystem, e.g /@/boot

        :rtype: str
        """
        return self._get_path(path)

    def get_subvolumes(self) -> List[str]:
        """
        Subvolumes to create, read-only subvolumes have the :ro suffix

        :return: list of subvolume paths

        :rtype: list
        """
        subvolumes = {volume.path for volume in self.volumes}
        if self.root_volume_path != os.sep:
            subvolumes.add(self.root_volume_path)
        if self.snapshots_path:
            subvolumes.add(self.snapshots_path)
            subvolumes.add(self.root_path)
        return [
            (
                f'{subvolume}:ro'
                if self.root_is_readonly_snapshot
                and subvolume == self.root_path
                else subvolume
            )
            for subvolume in Path.sort_by_hierarchy(sorted(subvolumes))
        ]

    def get_default_subvolume(self) -> Optional[str]:
        """
        Subvolume to set as default subvolume

        :return: subvolume path or None

        :rtype: str
        """
        if self.root_path != os.sep and (
            self.root_is_snapshot or self.default_volume_requested
        ):
            return self.root_path
        return None

    def get_root_mount_option(self) -> Optional[str]:
        """
        Mount option to mount the root tree if it is not stored in
        the default subvolume

        :return: subvol= mount option or None

        :rtype: str
        """
        if self.root_path != os.sep and not self.default_volume_requested:
            return 'subvol={0}'.format(self.root_path.lstrip(os.sep))
        return None

    def get_copy_files(self, source: str) -> Tuple[List[str], List[str]]:
        """
        CopyFiles= and ExcludeFilesTarget= settings to copy the root
        tree from the source directory into the filesystem. The data
        of a volume that is not stored below the location of the
        root tree is copied into its subvolume and excluded from the
        copy of the root tree, only the mount point directory of the
        volume is kept there. All volume mount points must exist in
        the source directory

        :param str source: source directory of the root tree

        :return: tuple of copy_files and exclude_files_target lists

        :rtype: tuple
        """
        copy_files = [f'{source}:{self.root_path}']
        exclude_files_target = []
        for volume in self.volumes:
            data_path = self._get_path(volume.mountpoint, without=volume)
            if data_path != volume.path:
                copy_files.append(
                    '{0}:{1}'.format(
                        os.path.normpath(
                            os.sep.join([source, volume.mountpoint])
                        ),
                        volume.path,
                    )
                )
                exclude_files_target.append(data_path + os.sep)
        return (copy_files, exclude_files_target)

    def get_make_directories(self) -> List[str]:
        """
        Directories to create in the filesystem, each subvolume needs
        a directory and the snapshot a /.snapshots mount point

        :return: list of directory paths

        :rtype: list
        """
        make_directories = [
            subvolume.split(':')[0] for subvolume in self.get_subvolumes()
        ]
        if self.root_is_snapshot:
            make_directories.append(self.root_path + '/.snapshots')
        return make_directories

    def _get_path(
        self, path: str, without: Optional[RepartBtrfsVolume] = None
    ) -> str:
        path = self._abspath(path)
        location, mountpoint = self.root_path, os.sep
        for volume in self.volumes:
            if volume is without:
                continue
            if (
                path == volume.mountpoint
                or path.startswith(volume.mountpoint + os.sep)
            ) and len(volume.mountpoint) > len(mountpoint):
                location, mountpoint = volume.path, volume.mountpoint
        return self._abspath(location, os.path.relpath(path, mountpoint))

    @staticmethod
    def _abspath(*elements: str) -> str:
        """
        Normalized absolute path of the joined path elements. Unlike
        os.path.normpath this never keeps two leading slashes
        """
        path = os.path.normpath(os.sep.join(elements)).lstrip(os.sep)
        return os.sep if path in ('', '.') else os.sep + path


class SystemdRepart:
    """
    **Create a disk image with systemd-repart**

    systemd-repart creates the GPT partition table and the
    filesystems including their content directly in the image
    file. It does not use loop devices or mounts.

    :param str diskname: file path of the disk image to create
    :param str arch: kiwi platform name of the image
    :param int sector_size:
        optional logical sector size, defaults to kiwi_sectorsize.
        The sector size is always passed to systemd-repart because
        it otherwise creates the filesystems with a 4096 bytes
        sector size while the partition table uses 512 bytes
        sectors. Firmware like OVMF refuses to read a FAT ESP whose
        sector size does not match the disk sector size
    """

    def __init__(
        self, diskname: str, arch: str, sector_size: Optional[int] = None
    ) -> None:
        self.diskname = diskname
        self.architecture = REPART_ARCHITECTURES.get(arch)
        self.sector_size = int(
            sector_size or Defaults().get('kiwi_sectorsize') or 512
        )
        self.partitions: List[RepartPartition] = []

    def add_partition(self, partition: RepartPartition) -> None:
        """
        Add a partition. Partitions are numbered in the order
        they are added

        :param RepartPartition partition: partition to create
        """
        self.partitions.append(partition)

    def get_partition_id_map(self) -> Dict[str, int]:
        """
        Partition number of each partition by its kiwi map name

        :return: map name to partition number

        :rtype: dict
        """
        return {
            partition.name: number
            for number, partition in enumerate(self.partitions, 1)
        }

    @staticmethod
    def get_filesystem_uuid(partition: RepartPartition) -> str:
        """
        Filesystem UUID systemd-repart assigns to the filesystem of
        the given partition. systemd-repart derives it from the
        partition UUID as HMAC-SHA256 of the string "file-system-uuid"
        keyed by the partition UUID, using the first half of the
        digest as v4 UUID. The filesystem UUID is thus known before
        systemd-repart creates the filesystem. For vfat the volume
        id is the first 32 bits of that UUID

        :param RepartPartition partition: partition with a filesystem

        :return: filesystem UUID as reported by blkid

        :rtype: str
        """
        fs_uuid = SystemdRepart._get_filesystem_uuid(partition)
        if partition.filesystem == 'vfat':
            volume_id = fs_uuid.hex[:8].upper()
            return f'{volume_id[:4]}-{volume_id[4:]}'
        return format(fs_uuid)

    def create(self, disksize_mbytes: int) -> List[Dict]:
        """
        Create the disk image

        :param int disksize_mbytes: size of the disk image

        :return: systemd-repart JSON result, one entry per partition

        :rtype: list
        """
        definitions = Temporary(prefix='kiwi_repart.').new_dir()
        for number, partition in enumerate(self.partitions, 1):
            self._write_definition(
                os.sep.join(
                    [definitions.name, f'{number:02d}-{partition.name}.conf']
                ),
                partition,
            )
        repart_call = [
            'systemd-repart',
            '--empty=create',
            f'--size={disksize_mbytes}M',
            '--offline=yes',
            '--dry-run=no',
            '--json=short',
            '--seed={0}'.format(
                Reproducible.get_seeded_uuid('systemd-repart') or 'random'
            ),
            f'--definitions={definitions.name}',
        ]
        if self.architecture:
            repart_call.append(f'--architecture={self.architecture}')
        repart_call.append(f'--sector-size={self.sector_size}')
        repart_call.append(self.diskname)
        log.info('Creating disk image with systemd-repart')
        Path.wipe(self.diskname)
        return json.loads(
            Command.run(
                repart_call, custom_env=self._get_mkfs_environment()
            ).output
        )

    def _get_mkfs_environment(self) -> Optional[Dict[str, str]]:
        """
        Environment for the systemd-repart call. systemd-repart
        appends the content of the SYSTEMD_REPART_MKFS_OPTIONS_<FS>
        environment variable to the mkfs call of each filesystem of
        type <FS>. The partitions of the disk builder use each of
        these filesystem types at most once. The mkfs options of
        a partition, see _get_custom_mkfs_options, are passed this
        way, as well as the subvolume setup of btrfs, see
        _get_subvolume_setup. If SOURCE_DATE_EPOCH
        is set and a btrfs or XFS filesystem is created,
        DETERMINISTIC_SEED is set, see _get_reproducible_mkfs_options

        :return: environment or None if no changes are needed

        :rtype: dict
        """
        reproducible = Reproducible.get_source_date_epoch() is not None
        mkfs_options: Dict[str, List[str]] = {}
        deterministic_seed = False
        for partition in self.partitions:
            options = self._get_subvolume_setup(partition)[1]
            custom_options, extended_options = self._get_custom_mkfs_options(
                partition
            )
            options += custom_options
            if reproducible:
                self._check_mkfs_source_date_epoch_support(partition.filesystem)
                options += self._get_reproducible_mkfs_options(
                    partition, extended_options
                )
                if partition.filesystem in REPART_DETERMINISTIC_SEED:
                    deterministic_seed = True
            elif extended_options:
                options += [
                    '-E',
                    ','.join(
                        defaults.REPART_EXT_EXTENDED_OPTIONS + extended_options
                    ),
                ]
            if options:
                mkfs_options.setdefault(partition.filesystem, []).extend(
                    options
                )
        if not mkfs_options and not deterministic_seed:
            return None
        custom_env = dict(os.environ)
        for filesystem, options in mkfs_options.items():
            variable = f'{REPART_MKFS_OPTIONS}{filesystem.upper()}'
            custom_env[variable] = ' '.join(
                [custom_env.get(variable, '')] + options
            ).strip()
        if deterministic_seed:
            custom_env['DETERMINISTIC_SEED'] = '1'
        return custom_env

    @staticmethod
    def _get_custom_mkfs_options(
        partition: RepartPartition,
    ) -> Tuple[List[str], List[str]]:
        """
        mkfs options of the given partition, split into the options
        and the extended options of mke2fs.

        systemd-repart appends the options from the environment to
        its own mkfs call, an option given there therefore overrides
        the same option systemd-repart sets. This does not work for
        the -E option of mke2fs. mke2fs only uses the last -E option
        given, which would drop the extended options systemd-repart
        or kiwi pass with their own -E option. For the filesystems
        created by mke2fs the values of the -E options are therefore
        taken out of the options, to be passed together with the
        other extended options in one -E option. The value of -E
        can be given as separate argument or attached to it, e.g
        -E stride=8 or -Estride=8

        :param RepartPartition partition: partition

        :return: tuple of mkfs options and extended options

        :rtype: tuple
        """
        mkfs_options = list(partition.mkfs_options or [])
        if partition.filesystem not in defaults.REPART_EXT_FILESYSTEMS:
            return (mkfs_options, [])
        options: List[str] = []
        extended_options: List[str] = []
        arguments = iter(mkfs_options)
        for argument in arguments:
            if argument == '-E':
                value = next(arguments, None)
                if value is None:
                    # incomplete option, left for mke2fs to report
                    options.append(argument)
                else:
                    extended_options.append(value)
            elif argument.startswith('-E'):
                extended_options.append(argument[2:])
            else:
                options.append(argument)
        return (options, extended_options)

    @staticmethod
    def _get_reproducible_mkfs_options(
        partition: RepartPartition,
        extended_options: Optional[List[str]] = None,
    ) -> List[str]:
        """
        mkfs options to create the filesystem of the given partition
        reproducible. systemd-repart passes SOURCE_DATE_EPOCH to the
        mkfs tools but not all of them use it for every random or
        time based value:

        * mkfs.vfat < 4.3 sets the volume label timestamp to the
          current time. --invariant uses a constant instead but also
          a constant volume ID, the volume ID systemd-repart passes
          is therefore repeated after --invariant
        * mke2fs creates a random directory hash seed, the filesystem
          UUID is used as seed. mke2fs only uses the last -E option
          given, the options systemd-repart passes with its own -E
          option are therefore repeated, followed by the given
          extended options
        * mkfs.btrfs and mkfs.xfs create random UUIDs for internal
          structures, e.g. device and subvolume UUIDs or inode
          generation numbers, unless the DETERMINISTIC_SEED environment
          variable is set to 1. No mkfs option is needed for them

        :param RepartPartition partition: partition
        :param list extended_options:
            extended options for mke2fs, see _get_custom_mkfs_options

        :return: list of mkfs options

        :rtype: list
        """
        if partition.filesystem == 'vfat':
            fs_uuid = SystemdRepart._get_filesystem_uuid(partition)
            return ['--invariant', '-i', fs_uuid.hex[:8].upper()]
        if partition.filesystem in defaults.REPART_EXT_FILESYSTEMS:
            fs_uuid = SystemdRepart._get_filesystem_uuid(partition)
            return [
                '-E',
                ','.join(
                    defaults.REPART_EXT_EXTENDED_OPTIONS
                    + [f'hash_seed={fs_uuid}']
                    + (extended_options or [])
                ),
            ]
        return []

    @staticmethod
    def _check_mkfs_source_date_epoch_support(filesystem: str) -> None:
        """
        Warn if the mkfs tool of the given filesystem is older than
        the first version that creates the filesystem reproducible,
        see REPART_MKFS_REPRODUCIBLE

        :param str filesystem: repart filesystem name, e.g. ext4
        """
        mkfs = REPART_MKFS_REPRODUCIBLE.get(filesystem)
        if mkfs and not CommandCapabilities.check_version(
            mkfs.tool,
            mkfs.min_version,
            version_flags=[mkfs.version_flag],
            raise_on_error=False,
            silent=True,
            channel=mkfs.channel,
        ):
            log.warning(
                '{0} is older than {1} or its version is unknown. It does '
                'not support SOURCE_DATE_EPOCH, the {2} filesystem is not '
                'reproducible. Use {3} >= {1} for a bit identical '
                'disk image'.format(
                    mkfs.tool,
                    '.'.join(str(number) for number in mkfs.min_version),
                    filesystem,
                    mkfs.package,
                )
            )

    @staticmethod
    def _get_filesystem_uuid(partition: RepartPartition) -> uuid.UUID:
        digest = hmac.new(
            uuid.UUID(partition.uuid).bytes,
            b'file-system-uuid',
            hashlib.sha256,
        ).digest()
        return uuid.UUID(bytes=digest[:16], version=4)

    @staticmethod
    def _get_subvolume_setup(
        partition: RepartPartition,
    ) -> Tuple[List[str], List[str]]:
        """
        Subvolumes for the Subvolumes= setting and mkfs.btrfs options
        for the read-only and the default subvolume.

        systemd-repart passes the flags of a subvolume to mkfs.btrfs
        as suffix, e.g --subvol path:ro,default, but mkfs.btrfs
        expects the subvolume type as prefix, e.g --subvol
        default-ro:path, and fails otherwise. Therefore these
        subvolumes are not configured by Subvolumes= and
        DefaultSubvolume= but passed to mkfs.btrfs directly through
        the SYSTEMD_REPART_MKFS_OPTIONS_BTRFS environment variable.
        A path with a leading slash is relative to the root
        directory mkfs.btrfs populates the filesystem from

        :param RepartPartition partition: partition

        :return: tuple of subvolume paths and mkfs.btrfs options

        :rtype: tuple
        """
        subvolumes = []
        mkfs_options = []
        for subvolume in partition.subvolumes or []:
            path, _, flags = subvolume.partition(':')
            readonly = 'ro' in flags.split(',')
            default = path == partition.default_subvolume
            if default and readonly:
                mkfs_options += ['--subvol', f'default-ro:{path}']
            elif default:
                mkfs_options += ['--subvol', f'default:{path}']
            elif readonly:
                mkfs_options += ['--subvol', f'ro:{path}']
            else:
                subvolumes.append(path)
        return (subvolumes, mkfs_options)

    @staticmethod
    def _write_definition(filename: str, partition: RepartPartition) -> None:
        definition = [
            '[Partition]',
            f'Type={partition.partition_type}',
            f'Label={partition.label}',
            f'UUID={partition.uuid}',
            f'Format={partition.filesystem}',
        ]
        if partition.mbsize:
            definition += [
                f'SizeMinBytes={partition.mbsize}M',
                f'SizeMaxBytes={partition.mbsize}M',
            ]
        for copy_files in partition.copy_files or []:
            definition.append(f'CopyFiles={copy_files}')
        if partition.exclude_files:
            definition.append(
                'ExcludeFiles={0}'.format(' '.join(partition.exclude_files))
            )
        if partition.exclude_files_target:
            definition.append(
                'ExcludeFilesTarget={0}'.format(
                    ' '.join(partition.exclude_files_target)
                )
            )
        if partition.make_directories:
            definition.append(
                'MakeDirectories={0}'.format(
                    ' '.join(partition.make_directories)
                )
            )
        subvolumes = SystemdRepart._get_subvolume_setup(partition)[0]
        if subvolumes:
            definition.append('Subvolumes={0}'.format(' '.join(subvolumes)))
        if partition.compression:
            definition.append(f'Compression={partition.compression}')
            if partition.compression_level is not None:
                definition.append(
                    f'CompressionLevel={partition.compression_level}'
                )
        log.debug('systemd-repart definition %s', os.path.basename(filename))
        log.debug('--------------conf start------------')
        for line in definition:
            log.debug(line)
        log.debug('--------------conf stop-------------')
        with open(filename, 'w') as conf:
            conf.write(os.linesep.join(definition) + os.linesep)
