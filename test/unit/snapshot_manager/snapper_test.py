import os
import datetime
from unittest.mock import patch, call, Mock, mock_open
from pytest import raises, fixture

from lxml import etree
from xml.dom import minidom

from kiwi.snapshot_manager.snapper import SnapshotManagerSnapper

from kiwi.exceptions import KiwiSnapshotManagerSetupError


@fixture(autouse=True)
def no_mountpoints_on_host():
    """
    The bind mounts of the chroot environment snapper runs in create
    their mountpoints below the root directory, which is relative to
    the working directory tests running in parallel share. Mountpoints
    must not be created there
    """
    with patch('kiwi.mount_manager.Path.create'):
        yield


class TestSnapshotManagerSnapper:
    def setup(self):
        self.snapper = SnapshotManagerSnapper(
            '/dev/device',
            'root_dir',
            '/tmp/mountpoint',
            '@',
            {'quota_groups': True},
        )

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.snapper.post_init({'some-arg': 'some-val'})
        assert self.snapper.custom_args['some-arg'] == 'some-val'
        assert not self.snapper.custom_args['quota_groups']

    @patch('kiwi.snapshot_manager.snapper.MountManager')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    def test_create_first_snapshot_with_snapper_helper(
        self, mock_command, mock_mount
    ):
        def return_snapper_version(command=None, raise_on_error=None, *args):
            mock = Mock()
            snapperCmd = ['chroot', 'snapper', '--version']
            subCmd = [element for element in command if element in snapperCmd]
            if snapperCmd == subCmd:
                mock.output = 'snapper 0.12.1'
            mock.return_code = 0
            return mock

        mock_command.side_effect = return_snapper_version

        extra_mounts = self.snapper.create_first_snapshot()
        assert mock_mount.call_args_list == [
            call(
                device='/dev/device',
                attributes={
                    'subvol_path': '@/.snapshots',
                    'subvol_name': '@/.snapshots',
                },
                mountpoint='/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
            )
        ]
        assert mock_command.call_args_list == [
            call(['chroot', 'root_dir', 'snapper', '--version']),
            call(
                command=['mountpoint', '-q', 'root_dir/tmp/mountpoint'],
                raise_on_error=False,
            ),
            call(
                [
                    'mount',
                    '-n',
                    '--bind',
                    '/tmp/mountpoint',
                    'root_dir/tmp/mountpoint',
                ]
            ),
            call(
                [
                    'chroot',
                    'root_dir',
                    '/usr/lib/snapper/installation-helper',
                    '--root-prefix',
                    '/tmp/mountpoint/@',
                    '--step',
                    'filesystem',
                ],
                None,
                True,
                False,
                True,
            ),
            call(
                command=['mountpoint', '-q', 'root_dir/tmp/mountpoint'],
                raise_on_error=False,
            ),
        ]
        assert len(extra_mounts) == 1

    @patch('os.chmod')
    @patch('kiwi.snapshot_manager.snapper.MountManager')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    def test_create_first_snapshot_without_snapper_helper(
        self, mock_command, mock_mount, mock_os_chmod
    ):
        def return_snapper_version(command=None, raise_on_error=None, *args):
            mock = Mock()
            snapperCmd = ['chroot', 'snapper', '--version']
            subCmd = [element for element in command if element in snapperCmd]
            if snapperCmd == subCmd:
                mock.output = 'snapper 0.12.0'
            mock.return_code = 0
            return mock

        mock_command.side_effect = return_snapper_version

        extra_mounts = self.snapper.create_first_snapshot()

        mock_os_chmod.assert_called_once_with(
            '/tmp/mountpoint/@/.snapshots', 0o700
        )
        assert mock_mount.call_args_list == [
            call(
                device='/dev/device',
                attributes={
                    'subvol_path': '@/.snapshots',
                    'subvol_name': '@/.snapshots',
                },
                mountpoint='/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
            )
        ]
        assert mock_command.call_args_list == [
            call(['chroot', 'root_dir', 'snapper', '--version']),
            call(
                ['btrfs', 'subvolume', 'create', '/tmp/mountpoint/@/.snapshots']
            ),
            call(
                [
                    'btrfs',
                    'subvolume',
                    'create',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                ]
            ),
            call(
                [
                    'btrfs',
                    'subvolume',
                    'set-default',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                ]
            ),
        ]
        assert len(extra_mounts) == 1

    @patch('os.path.exists')
    @patch('shutil.copyfile')
    @patch('kiwi.snapshot_manager.snapper.SysConfig')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    def test_setup_first_snapshot_with_snapper_helper(
        self, mock_command, mock_sysconf, mock_copy, mock_os_exists
    ):
        def return_snapper_version(command=None, raise_on_error=None, *args):
            mock = Mock()
            snapperCmd = ['chroot', 'snapper', '--version']
            subCmd = [element for element in command if element in snapperCmd]
            if snapperCmd == subCmd:
                mock.output = 'snapper 0.13.0'
            mock.return_code = 0
            return mock

        mock_command.side_effect = return_snapper_version

        item = {'SNAPPER_CONFIGS': '""'}

        def getitem(key):
            return item[key]

        def setitem(key, value):
            item[key] = value

        def contains(key):
            return key in item

        def exists(name):
            if 'snapper/configs/root' in name:
                return False
            return True

        sysconf = Mock()
        sysconf.__contains__ = Mock(side_effect=contains)
        sysconf.__getitem__ = Mock(side_effect=getitem)
        sysconf.__setitem__ = Mock(side_effect=setitem)
        mock_sysconf.return_value = sysconf
        mock_os_exists.side_effect = exists

        self.snapper.setup_first_snapshot()

        snapshot_path = '/tmp/mountpoint/@/.snapshots/1/snapshot'
        assert mock_copy.call_args_list == [
            call(
                f'{snapshot_path}/etc/snapper/config-templates/default',
                f'{snapshot_path}/etc/snapper/configs/root',
            )
        ]

        assert mock_command.call_args_list == [
            call(
                [
                    'chroot',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'snapper',
                    '--version',
                ]
            ),
            call(
                command=[
                    'mountpoint',
                    '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot',
                ],
                raise_on_error=False,
            ),
            call(
                [
                    'mount',
                    '-n',
                    '--bind',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot',
                ]
            ),
            call(
                command=[
                    'mountpoint',
                    '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
                ],
                raise_on_error=False,
            ),
            call(
                [
                    'mount',
                    '-n',
                    '--bind',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
                ]
            ),
            call(
                [
                    'chroot',
                    'root_dir',
                    '/usr/lib/snapper/installation-helper',
                    '--root-prefix',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    '--step',
                    'config',
                    '--description',
                    'first root filesystem',
                ],
                None,
                True,
                False,
                True,
            ),
            call(
                command=[
                    'mountpoint',
                    '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
                ],
                raise_on_error=False,
            ),
            call(
                command=[
                    'mountpoint',
                    '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot',
                ],
                raise_on_error=False,
            ),
            call(['btrfs', 'qgroup', 'create', '1/0', '/tmp/mountpoint']),
            call(
                [
                    'chroot',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'snapper',
                    '--no-dbus',
                    'set-config',
                    'QGROUP=1/0',
                ],
                None,
                True,
                False,
                True,
            ),
            call(
                [
                    'chroot',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'snapper',
                    '--no-dbus',
                    'modify',
                    '--default',
                    '1',
                ],
                None,
                True,
                False,
                True,
            ),
        ]

    @patch('os.path.exists')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    @patch.object(datetime, 'datetime', Mock(wraps=datetime.datetime))
    def test_setup_first_snapshot_without_snapper_helper(
        self, mock_command, mock_os_exists
    ):
        self.snapper.post_init(None)

        def return_snapper_version(command=None, raise_on_error=None, *args):
            mock = Mock()
            snapperCmd = ['chroot', 'snapper', '--version']
            subCmd = [element for element in command if element in snapperCmd]
            if snapperCmd == subCmd:
                mock.output = 'snapper 0.11.0'
            mock.return_code = 0
            return mock

        mock_command.side_effect = return_snapper_version
        mock_os_exists.return_value = True

        xml_info = etree.tostring(
            etree.parse(
                '../data/info.xml', etree.XMLParser(remove_blank_text=True)
            )
        )
        datetime.datetime.now.return_value = datetime.datetime(2016, 1, 1)

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.snapper.setup_first_snapshot()

        assert m_open.call_args_list == [
            call('/tmp/mountpoint/@/.snapshots/1/snapshot/../info.xml', 'w')
        ]
        assert m_open.return_value.write.call_args_list == [
            call(minidom.parseString(xml_info).toprettyxml(indent="    "))
        ]
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'snapper',
                    '--version',
                ]
            ),
            call(
                [
                    'chroot',
                    '/tmp/mountpoint/@/.snapshots/1/snapshot',
                    'snapper',
                    '--no-dbus',
                    'modify',
                    '--default',
                    '1',
                ],
                None,
                True,
                False,
                True,
            ),
        ]

    @patch('os.path.exists')
    @patch('kiwi.snapshot_manager.snapper.SysConfig')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    def test_setup_first_snapshot_with_bad_sysconfig(
        self, mock_command, mock_sysconf, mock_os_exists
    ):
        def return_snapper_version(command=None, raise_on_error=None, *args):
            mock = Mock()
            snapperCmd = ['chroot', 'snapper', '--version']
            subCmd = [element for element in command if element in snapperCmd]
            if snapperCmd == subCmd:
                mock.output = 'snapper 0.13.0'
            mock.return_code = 0
            return mock

        mock_command.side_effect = return_snapper_version

        item = {'SNAPPER_CONFIGS': '"root foo"'}

        def getitem(key):
            return item[key]

        def setitem(key, value):
            item[key] = value

        def contains(key):
            return key in item

        sysconf = Mock()
        sysconf.__contains__ = Mock(side_effect=contains)
        sysconf.__getitem__ = Mock(side_effect=getitem)
        sysconf.__setitem__ = Mock(side_effect=setitem)
        mock_sysconf.return_value = sysconf
        mock_os_exists.return_value = True

        with raises(KiwiSnapshotManagerSetupError):
            self.snapper.setup_first_snapshot()

    def test_get_default_snapshot_name(self):
        default_snapshot = '/@/.snapshots/1/snapshot'
        assert self.snapper.get_default_snapshot_name() == default_snapshot

    @patch('kiwi.snapshot_manager.snapper.Path.create')
    def test_setup_first_snapshot_on_tree(self, mock_Path_create, tmp_path):
        # Path.create is patched for all tests of this module
        mock_Path_create.side_effect = lambda path: os.makedirs(
            path, exist_ok=True
        )
        snapshot_root = tmp_path / 'root'
        template = snapshot_root / 'usr/share/snapper/config-templates/default'
        template.parent.mkdir(parents=True)
        template.write_text('SUBVOLUME="/"\n')
        snapshots_dir = tmp_path / '.snapshots'
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '86400'}):
            SnapshotManagerSnapper.setup_first_snapshot_on_tree(
                str(snapshot_root), str(snapshots_dir)
            )
        assert (snapshot_root / 'etc/snapper/configs/root').read_text() == (
            'SUBVOLUME="/"\n'
        )
        assert (snapshot_root / 'etc/sysconfig/snapper').read_text() == (
            'SNAPPER_CONFIGS="root"\n'
        )
        info = minidom.parse(str(snapshots_dir / '1/info.xml'))
        assert [
            (node.tagName, node.firstChild.data)
            for node in info.documentElement.childNodes
            if node.nodeType == node.ELEMENT_NODE
        ] == [
            ('type', 'single'),
            ('num', '1'),
            ('description', 'first root filesystem'),
            ('date', '1970-01-02 00:00:00'),
        ]

        # an existing config is kept, without snapper template and
        # without SOURCE_DATE_EPOCH only info.xml is written
        (snapshot_root / 'etc/snapper/configs/root').write_text('custom\n')
        with patch.dict('os.environ', {}, clear=True):
            SnapshotManagerSnapper.setup_first_snapshot_on_tree(
                str(snapshot_root), str(snapshots_dir)
            )
        assert (snapshot_root / 'etc/snapper/configs/root').read_text() == (
            'custom\n'
        )
        template.unlink()
        other_root = tmp_path / 'other'
        SnapshotManagerSnapper.setup_first_snapshot_on_tree(
            str(other_root), str(snapshots_dir)
        )
        assert not other_root.exists()
        assert (snapshots_dir / '1/info.xml').exists()
