import io
from unittest.mock import (
    patch, call, MagicMock, Mock
)
from pytest import raises

from kiwi.storage.clone_device import CloneDevice

from kiwi.exceptions import KiwiRaidSetupError


class TestCloneDevice:
    def setup(self):
        self.storage_device = Mock()
        self.storage_device.get_device = Mock(
            return_value='/dev/source-device'
        )
        self.target_device = Mock()
        self.target_device.get_device = Mock(
            return_value='/dev/target-device'
        )
        self.clone_id = Mock()
        self.clone_device = CloneDevice(
            self.storage_device, 'root_dir'
        )

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.storage.clone_device.Command.run')
    @patch('kiwi.storage.clone_device.BlockID')
    @patch('kiwi.storage.clone_device.FileSystem.new')
    def test_clone_filesystem(
        self, mock_FileSystem_new, mock_BlockID, mock_Command_run
    ):
        self.clone_id.get_filesystem.return_value = 'ext3'
        mock_BlockID.return_value = self.clone_id

        self.clone_device.clone([self.target_device])

        mock_Command_run.assert_called_once_with(
            ['dd', 'if=/dev/source-device', 'of=/dev/target-device', 'bs=1M']
        )
        mock_FileSystem_new.assert_called_once_with(
            'ext3', self.target_device
        )
        mock_FileSystem_new.return_value.__enter__ \
            .return_value.set_uuid.assert_called_once_with()

    @patch('kiwi.storage.clone_device.Command.run')
    @patch('kiwi.storage.clone_device.BlockID')
    def test_clone_lvm(self, mock_BlockID, mock_Command_run):
        self.clone_id.get_filesystem.return_value = 'LVM2_member'
        mock_BlockID.return_value = self.clone_id

        self.clone_device.clone([self.target_device])

        assert mock_Command_run.call_args_list == [
            call(
                [
                    'dd', 'if=/dev/source-device', 'of=/dev/target-device',
                    'bs=1M'
                ]
            ),
            call(
                ['vgimportclone', '/dev/target-device']
            )
        ]

    @patch('kiwi.storage.clone_device.Command.run')
    @patch('kiwi.storage.clone_device.BlockID')
    @patch('uuid.uuid4')
    def test_clone_luks(self, mock_uuid4, mock_BlockID, mock_Command_run):
        self.clone_id.get_filesystem.return_value = 'crypto_LUKS'
        mock_BlockID.return_value = self.clone_id
        mock_uuid4.return_value = 'some-UUID'

        self.clone_device.clone([self.target_device])

        assert mock_Command_run.call_args_list == [
            call(
                [
                    'dd', 'if=/dev/source-device', 'of=/dev/target-device',
                    'bs=1M'
                ]
            ),
            call(
                [
                    'cryptsetup', '-q', 'luksUUID',
                    '/dev/target-device', '--uuid', 'some-UUID'
                ]
            )
        ]

    @patch('kiwi.storage.clone_device.Command.run')
    @patch('kiwi.storage.clone_device.BlockID')
    @patch('kiwi.storage.clone_device.FileSystem.new')
    @patch('kiwi.storage.clone_device.MappedDevice')
    def test_clone_raid(
        self, mock_MappedDevice, mock_FileSystem_new,
        mock_BlockID, mock_Command_run
    ):
        self.clone_id.get_filesystem.return_value = 'linux_raid_member'
        mock_BlockID.return_value = self.clone_id
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.readline.return_value = \
                'ARRAY /dev/md0 metadata=1.2 name=asterix:0 UUID=...'

            self.clone_device.clone([self.target_device])

            mock_open.assert_called_once_with('root_dir/etc/mdadm.conf')

        mock_FileSystem_new.assert_called_once_with(
            mock_BlockID.return_value.get_filesystem.return_value,
            mock_MappedDevice.return_value
        )
        mock_FileSystem_new.return_value.__enter__ \
            .return_value.set_uuid.assert_called_once_with()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'dd', 'if=/dev/source-device', 'of=/dev/target-device',
                    'bs=1M'
                ]
            ),
            call(
                ['mdadm', '--stop', '/dev/md0']
            ),
            call(
                [
                    'mdadm', '--assemble', '--update=uuid',
                    '--name', 'asterix:0', '/dev/md0', '/dev/target-device'
                ]
            ),
            call(
                ['mdadm', '--stop', '/dev/md0']
            ),
            call(
                ['mdadm', '--assemble', '/dev/md0', '/dev/source-device']
            )
        ]

    @patch('kiwi.storage.clone_device.Command.run')
    @patch('kiwi.storage.clone_device.BlockID')
    def test_clone_raid_raises(self, mock_BlockID, mock_Command_run):
        self.clone_id.get_filesystem.return_value = 'linux_raid_member'
        mock_BlockID.return_value = self.clone_id
        with patch('builtins.open', create=True) as mock_open:
            mock_open.side_effect = Exception
            with raises(KiwiRaidSetupError):
                self.clone_device.clone([self.target_device])
