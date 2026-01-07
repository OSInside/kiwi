import datetime
from unittest.mock import (
    patch, call, Mock, mock_open
)
from pytest import (
    raises
)

from lxml import etree
from xml.dom import minidom

from kiwi.snapshot_manager.snapper import SnapshotManagerSnapper

from kiwi.exceptions import (
    KiwiSnapshotManagerSetupError
)


class TestSnapshotManagerSnapper:
    def setup(self):
        self.snapper = SnapshotManagerSnapper(
            '/dev/device', 'root_dir', '/tmp/mountpoint', '@',
            {'quota_groups': True}
        )

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.snapper.post_init({'some-arg': 'some-val'})
        assert self.snapper.custom_args['some-arg'] == 'some-val'
        assert not self.snapper.custom_args['quota_groups']

    @patch('kiwi.snapshot_manager.snapper.MountManager')
    @patch('kiwi.snapshot_manager.snapper.Command.run')
    def test_create_first_snapshot_with_snapper_helper(self, mock_command, mock_mount):
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
                attributes={'subvol_path': '@/.snapshots', 'subvol_name': '@/.snapshots'},
                mountpoint='/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots'
            )
        ]
        assert mock_command.call_args_list == [
            call(['chroot', 'root_dir', 'snapper', '--version']),
            call(
                command=['mountpoint', '-q', 'root_dir/tmp/mountpoint'],
                raise_on_error=False
            ),
            call([
                'mount', '-n', '--bind', '/tmp/mountpoint',
                'root_dir/tmp/mountpoint'
            ]),
            call([
                'chroot', 'root_dir', '/usr/lib/snapper/installation-helper',
                '--root-prefix', '/tmp/mountpoint/@', '--step', 'filesystem'
            ], None, True, False, True),
            call(
                command=['mountpoint', '-q', 'root_dir/tmp/mountpoint'],
                raise_on_error=False
            )
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

        mock_os_chmod.assert_called_once_with('/tmp/mountpoint/@/.snapshots', 0o700)
        assert mock_mount.call_args_list == [
            call(
                device='/dev/device',
                attributes={'subvol_path': '@/.snapshots', 'subvol_name': '@/.snapshots'},
                mountpoint='/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots'
            )
        ]
        assert mock_command.call_args_list == [
            call(['chroot', 'root_dir', 'snapper', '--version']),
            call([
                'btrfs', 'subvolume', 'create', '/tmp/mountpoint/@/.snapshots'
            ]),
            call([
                'btrfs', 'subvolume', 'create',
                '/tmp/mountpoint/@/.snapshots/1/snapshot'
            ]),
            call([
                'btrfs', 'subvolume', 'set-default',
                '/tmp/mountpoint/@/.snapshots/1/snapshot'
            ])
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
                f'{snapshot_path}/etc/snapper/configs/root'
            )
        ]

        assert mock_command.call_args_list == [
            call([
                'chroot', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'snapper', '--version'
            ]),
            call(
                command=[
                    'mountpoint', '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot'
                ], raise_on_error=False
            ),
            call([
                'mount', '-n', '--bind',
                '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot'
            ]),
            call(
                command=[
                    'mountpoint', '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots'
                ], raise_on_error=False
            ),
            call([
                'mount', '-n', '--bind',
                '/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots',
                'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots'
            ]),
            call([
                'chroot', 'root_dir', '/usr/lib/snapper/installation-helper',
                '--root-prefix', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                '--step', 'config', '--description', 'first root filesystem'
            ], None, True, False, True),
            call(
                command=[
                    'mountpoint', '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot/.snapshots'
                ], raise_on_error=False
            ),
            call(
                command=[
                    'mountpoint', '-q',
                    'root_dir/tmp/mountpoint/@/.snapshots/1/snapshot'
                ], raise_on_error=False
            ),
            call(['btrfs', 'qgroup', 'create', '1/0', '/tmp/mountpoint']),
            call([
                'chroot', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'snapper', '--no-dbus', 'set-config', 'QGROUP=1/0'
            ], None, True, False, True),
            call([
                'chroot', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'snapper', '--no-dbus', 'modify', '--default', '1'
            ], None, True, False, True)
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

        xml_info = etree.tostring(etree.parse(
            '../data/info.xml', etree.XMLParser(remove_blank_text=True)
        ))
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
            call([
                'chroot', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'snapper', '--version'
            ]),
            call([
                'chroot', '/tmp/mountpoint/@/.snapshots/1/snapshot',
                'snapper', '--no-dbus', 'modify', '--default', '1'
            ], None, True, False, True)
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
