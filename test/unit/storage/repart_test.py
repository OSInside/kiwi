import os
import json
import logging
from unittest.mock import patch, call, Mock
from pytest import fixture

from kiwi.storage.repart import (
    SystemdRepart,
    RepartPartition,
    RepartBtrfsLayout,
    RepartBtrfsVolume,
)
from kiwi.xml_state import volume_type


def volume(name, realpath, parent='', attributes=None, is_root_volume=False):
    return volume_type(
        name=name,
        parent=parent,
        size=None,
        realpath=realpath,
        mountpoint=None if is_root_volume else realpath,
        fullsize=False,
        label=None,
        attributes=attributes or [],
        is_root_volume=is_root_volume,
    )


class TestSystemdRepart:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.repart = SystemdRepart('disk.raw', 'x86_64', 4096)
        self.repart.add_partition(
            RepartPartition(
                name='efi',
                partition_type='esp',
                label='EFI',
                uuid='efi-uuid',
                filesystem='vfat',
                mbsize=20,
                copy_files=['/staging/boot/efi:/'],
            )
        )
        self.repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='root-uuid',
                filesystem='ext4',
                copy_files=['/staging:/'],
                exclude_files=['/staging/boot/efi/', '/staging/foo'],
                make_directories=['/boot/efi'],
            )
        )

    def setup_method(self, cls):
        self.setup()

    def test_get_filesystem_uuid(self):
        # filesystem UUIDs of a disk image created by systemd-repart
        assert (
            SystemdRepart.get_filesystem_uuid(
                RepartPartition(
                    name='root',
                    partition_type='root',
                    label='ROOT',
                    uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
                    filesystem='ext3',
                )
            )
            == 'eb272619-2296-4fd3-b9a5-9151b07c10ed'
        )
        assert (
            SystemdRepart.get_filesystem_uuid(
                RepartPartition(
                    name='efi',
                    partition_type='esp',
                    label='EFI',
                    uuid='c5c167b6-18d4-4a2a-bd63-35fd3799c2bc',
                    filesystem='vfat',
                )
            )
            == '07D3-31C2'
        )

    def test_get_partition_id_map(self):
        assert self.repart.get_partition_id_map() == {'efi': 1, 'root': 2}

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        result = [{'uuid': 'root-uuid', 'offset': 1048576}]
        mock_Command_run.return_value = Mock(output=json.dumps(result))
        with patch.dict('os.environ', {}, clear=True):
            assert self.repart.create(42) == result
        mock_wipe.assert_called_once_with('disk.raw')
        mock_Command_run.assert_called_once_with(
            [
                'systemd-repart',
                '--empty=create',
                '--size=42M',
                '--offline=yes',
                '--dry-run=no',
                '--json=short',
                '--seed=random',
                f'--definitions={tmp_path}',
                '--architecture=x86-64',
                '--sector-size=4096',
                'disk.raw',
            ],
            custom_env=None,
        )
        assert sorted(os.listdir(tmp_path)) == ['01-efi.conf', '02-root.conf']
        assert (tmp_path / '01-efi.conf').read_text() == (
            '[Partition]\n'
            'Type=esp\n'
            'Label=EFI\n'
            'UUID=efi-uuid\n'
            'Format=vfat\n'
            'SizeMinBytes=20M\n'
            'SizeMaxBytes=20M\n'
            'CopyFiles=/staging/boot/efi:/\n'
        )
        assert (tmp_path / '02-root.conf').read_text() == (
            '[Partition]\n'
            'Type=root\n'
            'Label=ROOT\n'
            'UUID=root-uuid\n'
            'Format=ext4\n'
            'CopyFiles=/staging:/\n'
            'ExcludeFiles=/staging/boot/efi/ /staging/foo\n'
            'MakeDirectories=/boot/efi\n'
        )

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_reproducible_unknown_arch_default_sector_size(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        mock_Command_run.return_value = Mock(output='[]')
        repart = SystemdRepart('disk.raw', 'some-arch')
        repart.add_partition(
            RepartPartition(
                name='swap',
                partition_type='swap',
                label='SWAP',
                uuid='swap-uuid',
                filesystem='swap',
                mbsize=128,
            )
        )
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            repart.create(42)
            seed = '32ae06cc-58ea-5611-9ddc-6eee1d50f8d7'
        call_args = mock_Command_run.call_args[0][0]
        assert f'--seed={seed}' in call_args
        assert not [arg for arg in call_args if arg.startswith('--arch')]
        assert '--sector-size=512' in call_args
        assert (tmp_path / '01-swap.conf').read_text() == (
            '[Partition]\n'
            'Type=swap\n'
            'Label=SWAP\n'
            'UUID=swap-uuid\n'
            'Format=swap\n'
            'SizeMinBytes=128M\n'
            'SizeMaxBytes=128M\n'
        )

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_reproducible_mkfs_options(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)

        def command_run(call, **kwargs):
            if call[0] == 'mke2fs':
                return Mock(error='mke2fs 1.47.3 (8-Jul-2025)\n')
            return Mock(output='[]')

        mock_Command_run.side_effect = command_run
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='efi',
                partition_type='esp',
                label='EFI',
                uuid='c5c167b6-18d4-4a2a-bd63-35fd3799c2bc',
                filesystem='vfat',
            )
        )
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
                filesystem='ext4',
            )
        )
        with patch.dict(
            'os.environ',
            {
                'SOURCE_DATE_EPOCH': '0',
                'SYSTEMD_REPART_MKFS_OPTIONS_EXT4': '-I 256',
            },
            clear=True,
        ):
            with self._caplog.at_level(logging.WARNING):
                repart.create(42)
        assert not self._caplog.records
        assert mock_Command_run.call_args_list[0][0][0] == ['mke2fs', '-V']
        # the volume ID and the hash seed match the filesystem UUIDs
        # systemd-repart assigns, see test_get_filesystem_uuid
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SOURCE_DATE_EPOCH': '0',
            'SYSTEMD_REPART_MKFS_OPTIONS_VFAT': '--invariant -i 07D331C2',
            'SYSTEMD_REPART_MKFS_OPTIONS_EXT4': (
                '-I 256 -E nodiscard,lazy_itable_init=1,'
                'hash_seed=eb272619-2296-4fd3-b9a5-9151b07c10ed'
            ),
        }

    @patch('kiwi.storage.repart.CommandCapabilities.check_version')
    def test_check_mkfs_source_date_epoch_support(self, mock_check_version):
        mock_check_version.return_value = False
        with self._caplog.at_level(logging.WARNING):
            SystemdRepart._check_mkfs_source_date_epoch_support('ext4')
            SystemdRepart._check_mkfs_source_date_epoch_support('btrfs')
            SystemdRepart._check_mkfs_source_date_epoch_support('xfs')
        # mke2fs prints its version to stderr
        assert mock_check_version.call_args_list == [
            call(
                'mke2fs',
                (1, 47, 1),
                version_flags=['-V'],
                raise_on_error=False,
                silent=True,
                channel='stderr',
            ),
            call(
                'mkfs.btrfs',
                (7, 3),
                version_flags=['--version'],
                raise_on_error=False,
                silent=True,
                channel='stdout',
            ),
            call(
                'mkfs.xfs',
                (6, 18),
                version_flags=['-V'],
                raise_on_error=False,
                silent=True,
                channel='stdout',
            ),
        ]
        assert [record.getMessage() for record in self._caplog.records] == [
            'mke2fs is older than 1.47.1 or its version is unknown. It '
            'does not support SOURCE_DATE_EPOCH, the ext4 filesystem is '
            'not reproducible. Use e2fsprogs >= 1.47.1 for a bit '
            'identical disk image',
            'mkfs.btrfs is older than 7.3 or its version is unknown. It '
            'does not support SOURCE_DATE_EPOCH, the btrfs filesystem is '
            'not reproducible. Use btrfs-progs >= 7.3 for a bit '
            'identical disk image',
            'mkfs.xfs is older than 6.18 or its version is unknown. It '
            'does not support SOURCE_DATE_EPOCH, the xfs filesystem is '
            'not reproducible. Use xfsprogs >= 6.18 for a bit '
            'identical disk image',
        ]
        self._caplog.clear()
        mock_check_version.reset_mock()
        mock_check_version.return_value = True
        with self._caplog.at_level(logging.WARNING):
            SystemdRepart._check_mkfs_source_date_epoch_support('ext3')
        assert not self._caplog.records
        # filesystem without version requirement
        mock_check_version.reset_mock()
        SystemdRepart._check_mkfs_source_date_epoch_support('vfat')
        assert not mock_check_version.called

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_reproducible_deterministic_seed(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)

        def command_run(call, **kwargs):
            if call[0] == 'mkfs.xfs':
                return Mock(output='mkfs.xfs version 6.19.0\n', error='')
            return Mock(output='[]')

        mock_Command_run.side_effect = command_run
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
                filesystem='xfs',
            )
        )
        with patch.dict('os.environ', {}, clear=True):
            repart.create(42)
        # without SOURCE_DATE_EPOCH nothing changes
        assert mock_Command_run.call_args[1]['custom_env'] is None
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}, clear=True):
            repart.create(42)
        assert not [
            record
            for record in self._caplog.records
            if record.levelno >= logging.WARNING
        ]
        # mkfs.xfs needs no extra options, only DETERMINISTIC_SEED
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SOURCE_DATE_EPOCH': '0',
            'DETERMINISTIC_SEED': '1',
        }

    def test_get_reproducible_mkfs_options_other_filesystem(self):
        partition = RepartPartition(
            name='root',
            partition_type='root',
            label='ROOT',
            uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
            filesystem='xfs',
        )
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            assert SystemdRepart._get_reproducible_mkfs_options(partition) == []

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_btrfs_subvolumes(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        mock_Command_run.return_value = Mock(output='[]')
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='root-uuid',
                filesystem='btrfs',
                copy_files=[
                    '/staging:/@/.snapshots/1/snapshot',
                    '/staging/home:/@/home',
                ],
                exclude_files=['/staging/boot/efi/'],
                exclude_files_target=['/@/.snapshots/1/snapshot/home/'],
                make_directories=['/@/.snapshots/1/snapshot/boot/efi'],
                subvolumes=[
                    '/@',
                    '/@/.snapshots',
                    '/@/home',
                    '/@/.snapshots/1/snapshot:ro',
                ],
                default_subvolume='/@/.snapshots/1/snapshot',
            )
        )
        with patch.dict(
            'os.environ',
            {'SYSTEMD_REPART_MKFS_OPTIONS_BTRFS': '--nodesize 16k'},
            clear=True,
        ):
            with self._caplog.at_level(logging.DEBUG):
                repart.create(42)
        # the definition is logged line by line, the mkfs options are not
        definition = (tmp_path / '01-root.conf').read_text().splitlines()
        assert [record.getMessage() for record in self._caplog.records] == [
            'systemd-repart definition 01-root.conf',
            '--------------conf start------------',
            *definition,
            '--------------conf stop-------------',
            'Creating disk image with systemd-repart',
        ]
        assert all(
            record.levelno == logging.DEBUG
            for record in self._caplog.records[:-1]
        )
        assert 'SYSTEMD_REPART_MKFS_OPTIONS_BTRFS' not in self._caplog.text
        assert not [
            record
            for record in self._caplog.records
            if record.levelno >= logging.INFO
            and 'default-ro' in record.getMessage()
        ]
        # mkfs.btrfs expects the subvolume type as prefix, the
        # read-only default subvolume is therefore passed directly
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SYSTEMD_REPART_MKFS_OPTIONS_BTRFS': (
                '--nodesize 16k ' '--subvol default-ro:/@/.snapshots/1/snapshot'
            )
        }
        assert (tmp_path / '01-root.conf').read_text() == (
            '[Partition]\n'
            'Type=root\n'
            'Label=ROOT\n'
            'UUID=root-uuid\n'
            'Format=btrfs\n'
            'CopyFiles=/staging:/@/.snapshots/1/snapshot\n'
            'CopyFiles=/staging/home:/@/home\n'
            'ExcludeFiles=/staging/boot/efi/\n'
            'ExcludeFilesTarget=/@/.snapshots/1/snapshot/home/\n'
            'MakeDirectories=/@/.snapshots/1/snapshot/boot/efi\n'
            'Subvolumes=/@ /@/.snapshots /@/home\n'
        )

        # reproducible build: mkfs.btrfs derives its internal UUIDs
        # from the filesystem UUID with DETERMINISTIC_SEED
        mock_Command_run.side_effect = lambda call, **kwargs: (
            Mock(output='mkfs.btrfs, part of btrfs-progs v7.3\n', error='')
            if call[0] == 'mkfs.btrfs'
            else Mock(output='[]')
        )
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}, clear=True):
            repart.create(42)
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SOURCE_DATE_EPOCH': '0',
            'DETERMINISTIC_SEED': '1',
            'SYSTEMD_REPART_MKFS_OPTIONS_BTRFS': (
                '--subvol default-ro:/@/.snapshots/1/snapshot'
            ),
        }

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_btrfs_compression(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        mock_Command_run.return_value = Mock(output='[]')
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='root-uuid',
                filesystem='btrfs',
                compression='zstd',
                compression_level=3,
            )
        )
        repart.add_partition(
            RepartPartition(
                name='data',
                partition_type='linux-generic',
                label='DATA',
                uuid='data-uuid',
                filesystem='btrfs',
                compression='lzo',
            )
        )
        repart.create(42)
        assert (tmp_path / '01-root.conf').read_text() == (
            '[Partition]\n'
            'Type=root\n'
            'Label=ROOT\n'
            'UUID=root-uuid\n'
            'Format=btrfs\n'
            'Compression=zstd\n'
            'CompressionLevel=3\n'
        )
        assert (tmp_path / '02-data.conf').read_text() == (
            '[Partition]\n'
            'Type=linux-generic\n'
            'Label=DATA\n'
            'UUID=data-uuid\n'
            'Format=btrfs\n'
            'Compression=lzo\n'
        )

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_mkfs_options(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        mock_Command_run.return_value = Mock(output='[]')
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='efi',
                partition_type='esp',
                label='EFI',
                uuid='c5c167b6-18d4-4a2a-bd63-35fd3799c2bc',
                filesystem='vfat',
            )
        )
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
                filesystem='ext4',
                mkfs_options=['-O', '^has_journal', '-E', 'stride=8'],
            )
        )
        with patch.dict(
            'os.environ',
            {'SYSTEMD_REPART_MKFS_OPTIONS_EXT4': '-I 256'},
            clear=True,
        ):
            repart.create(42)
        # the extended options are passed in one -E option together
        # with the ones systemd-repart passes with its own -E option
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SYSTEMD_REPART_MKFS_OPTIONS_EXT4': (
                '-I 256 -O ^has_journal '
                '-E nodiscard,lazy_itable_init=1,stride=8'
            ),
        }
        # the mkfs definitions are not affected
        assert 'stride' not in (tmp_path / '02-root.conf').read_text()

        # reproducible build: the extended options follow the hash seed
        mock_Command_run.side_effect = lambda call, **kwargs: (
            Mock(error='mke2fs 1.47.3 (8-Jul-2025)\n')
            if call[0] == 'mke2fs'
            else Mock(output='[]')
        )
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}, clear=True):
            repart.create(42)
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SOURCE_DATE_EPOCH': '0',
            'SYSTEMD_REPART_MKFS_OPTIONS_VFAT': '--invariant -i 07D331C2',
            'SYSTEMD_REPART_MKFS_OPTIONS_EXT4': (
                '-O ^has_journal -E nodiscard,lazy_itable_init=1,'
                'hash_seed=eb272619-2296-4fd3-b9a5-9151b07c10ed,stride=8'
            ),
        }

    @patch('kiwi.storage.repart.Path.wipe')
    @patch('kiwi.storage.repart.Command.run')
    @patch('kiwi.storage.repart.Temporary')
    def test_create_mkfs_options_xfs(
        self, mock_Temporary, mock_Command_run, mock_wipe, tmp_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = str(tmp_path)
        mock_Command_run.return_value = Mock(output='[]')
        repart = SystemdRepart('disk.raw', 'x86_64', 512)
        repart.add_partition(
            RepartPartition(
                name='root',
                partition_type='root',
                label='ROOT',
                uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
                filesystem='xfs',
                mkfs_options=['-i', 'size=512', '-E', 'value'],
            )
        )
        with patch.dict('os.environ', {}, clear=True):
            repart.create(42)
        # the options are passed unchanged, -E is no mke2fs option here
        assert mock_Command_run.call_args[1]['custom_env'] == {
            'SYSTEMD_REPART_MKFS_OPTIONS_XFS': '-i size=512 -E value',
        }

    def test_get_custom_mkfs_options(self):
        partition = RepartPartition(
            name='root',
            partition_type='root',
            label='ROOT',
            uuid='e8871034-3f7f-4cb3-a772-4646679a9ecd',
            filesystem='ext3',
        )
        assert SystemdRepart._get_custom_mkfs_options(partition) == ([], [])
        partition = partition._replace(
            mkfs_options=[
                '-E',
                'stride=8',
                '-b',
                '1024',
                '-Estripe_width=16',
                '-E',
            ]
        )
        # an incomplete -E option at the end is kept for mke2fs to fail
        assert SystemdRepart._get_custom_mkfs_options(partition) == (
            ['-b', '1024', '-E'],
            ['stride=8', 'stripe_width=16'],
        )

    def test_get_subvolume_setup(self):
        partition = RepartPartition(
            name='root',
            partition_type='root',
            label='ROOT',
            uuid='root-uuid',
            filesystem='btrfs',
            subvolumes=['/@', '/@/home', '/@/ro:ro'],
            default_subvolume='/@',
        )
        assert SystemdRepart._get_subvolume_setup(partition) == (
            ['/@/home'],
            ['--subvol', 'default:/@', '--subvol', 'ro:/@/ro'],
        )
        assert SystemdRepart._get_subvolume_setup(
            partition._replace(subvolumes=None)
        ) == ([], [])


class TestRepartBtrfsLayout:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.volumes = [
            volume('home', 'home'),
            volume('var', 'var'),
            volume(
                'var/lib/docker',
                'var/lib/docker',
                attributes=['enable-for-filesystem-check'],
            ),
            volume('', '/', is_root_volume=True),
        ]

    def setup_method(self, cls):
        self.setup()

    def test_root_subvolume(self):
        layout = RepartBtrfsLayout(self.volumes, True)
        assert layout.root_volume_name == '@'
        assert layout.root_path == '/@'
        assert layout.snapshots_path is None
        assert layout.volumes == [
            RepartBtrfsVolume('/@/home', '/home'),
            RepartBtrfsVolume('/@/var', '/var'),
            RepartBtrfsVolume('/@/var/lib/docker', '/var/lib/docker', True),
        ]
        assert layout.get_mount_volumes() == layout.volumes
        assert layout.get_subvolumes() == [
            '/@',
            '/@/home',
            '/@/var',
            '/@/var/lib/docker',
        ]
        assert layout.get_default_subvolume() == '/@'
        assert layout.get_root_mount_option() is None
        # all volumes are stored below the root tree location
        assert layout.get_copy_files('/staging') == (['/staging:/@'], [])
        assert layout.get_make_directories() == layout.get_subvolumes()
        assert layout.get_path('/boot/efi') == '/@/boot/efi'
        assert layout.get_path('/var/lib/docker/x') == '/@/var/lib/docker/x'

    def test_root_subvolume_no_default_volume(self):
        self.volumes.append(volume('root', '/', is_root_volume=True))
        layout = RepartBtrfsLayout(
            self.volumes, True, default_volume_requested=False
        )
        assert layout.root_path == '/root'
        assert layout.get_default_subvolume() is None
        assert layout.get_root_mount_option() == 'subvol=root'

    def test_root_subvolume_implicit(self):
        with self._caplog.at_level(logging.WARNING):
            layout = RepartBtrfsLayout(self.volumes, None)
        assert layout.root_path == '/@'
        assert 'Implicitly creating root volume' in self._caplog.text

    def test_toplevel(self):
        with self._caplog.at_level(logging.WARNING):
            layout = RepartBtrfsLayout(self.volumes, False, True)
        assert 'root_is_snapper_snapshot has been disabled' in (
            self._caplog.text
        )
        assert layout.root_is_snapshot is False
        assert layout.root_path == '/'
        assert layout.get_subvolumes() == ['/home', '/var', '/var/lib/docker']
        assert layout.get_default_subvolume() is None
        assert layout.get_root_mount_option() is None
        assert layout.get_copy_files('/staging') == (['/staging:/'], [])
        assert layout.get_path('/boot') == '/boot'

    def test_snapshot(self):
        layout = RepartBtrfsLayout(
            self.volumes, True, True, True, default_volume_requested=False
        )
        assert layout.root_is_readonly_snapshot is True
        assert layout.root_path == '/@/.snapshots/1/snapshot'
        assert layout.snapshots_path == '/@/.snapshots'
        assert layout.get_mount_volumes() == [
            RepartBtrfsVolume('/@/home', '/home'),
            RepartBtrfsVolume('/@/var', '/var'),
            RepartBtrfsVolume('/@/.snapshots', '/.snapshots'),
            RepartBtrfsVolume('/@/var/lib/docker', '/var/lib/docker', True),
        ]
        assert layout.get_subvolumes() == [
            '/@',
            '/@/.snapshots',
            '/@/home',
            '/@/var',
            '/@/.snapshots/1/snapshot:ro',
            '/@/var/lib/docker',
        ]
        # a snapshot is always the default subvolume
        assert layout.get_default_subvolume() == '/@/.snapshots/1/snapshot'
        assert layout.get_root_mount_option() == (
            'subvol=@/.snapshots/1/snapshot'
        )
        # the volumes are not stored below the snapshot, the
        # nested docker volume is copied along with var
        assert layout.get_copy_files('/staging') == (
            [
                '/staging:/@/.snapshots/1/snapshot',
                '/staging/home:/@/home',
                '/staging/var:/@/var',
            ],
            [
                '/@/.snapshots/1/snapshot/home/',
                '/@/.snapshots/1/snapshot/var/',
            ],
        )
        assert layout.get_make_directories() == [
            '/@',
            '/@/.snapshots',
            '/@/home',
            '/@/var',
            '/@/.snapshots/1/snapshot',
            '/@/var/lib/docker',
            '/@/.snapshots/1/snapshot/.snapshots',
        ]
        assert layout.get_path('/boot') == '/@/.snapshots/1/snapshot/boot'
        assert layout.get_path('/home/user') == '/@/home/user'

    def test_volumes_with_toplevel_parent(self):
        layout = RepartBtrfsLayout(
            [
                volume('root', '/', is_root_volume=True),
                volume('boot', 'boot', parent='/'),
                volume('home', 'home', parent='/'),
            ],
            True,
            default_volume_requested=False,
        )
        assert layout.get_subvolumes() == ['/boot', '/home', '/root']
        assert layout.get_copy_files('/staging') == (
            [
                '/staging:/root',
                '/staging/boot:/boot',
                '/staging/home:/home',
            ],
            ['/root/boot/', '/root/home/'],
        )
        assert layout.get_path('/boot') == '/boot'
        assert layout.get_path('/boot/efi') == '/boot/efi'
        assert layout.get_path('/etc') == '/root/etc'
