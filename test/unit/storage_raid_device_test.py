from mock import patch

import mock

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiRaidSetupError
from kiwi.storage.raid_device import RaidDevice


class TestRaidDevice(object):
    def setup(self):
        storage_device = mock.Mock()
        storage_device.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        storage_device.is_loop = mock.Mock(
            return_value=True
        )
        self.raid = RaidDevice(storage_device)

    @raises(KiwiRaidSetupError)
    def test_create_degraded_raid_invalid_level(self):
        self.raid.create_degraded_raid('bogus-level')

    @raises(KiwiRaidSetupError)
    @patch('os.path.exists')
    def test_create_degraded_raid_no_free_device(self, mock_path):
        mock_path.return_value = True
        self.raid.create_degraded_raid('mirroring')

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.raid.raid_device = '/dev/md0'
        assert self.raid.get_device().get_device() == '/dev/md0'
        self.raid.raid_device = None

    @patch('kiwi.storage.raid_device.Command.run')
    @patch('os.path.exists')
    def test_create_degraded_raid(self, mock_path, mock_command):
        mock_path.return_value = False
        self.raid.create_degraded_raid('mirroring')
        mock_command.assert_called_once_with(
            [
                'mdadm', '--create', '--run', '/dev/md0',
                '--level', '1', '--raid-disks', '2',
                '/dev/some-device', 'missing'
            ]
        )
        self.raid.raid_device = None

    @patch('kiwi.storage.raid_device.Command.run')
    @patch_open
    def test_create_raid_config(self, mock_open, mock_command):
        self.raid.raid_device = '/dev/md0'
        command_call = mock.Mock()
        command_call.output = 'data'
        mock_command.return_value = command_call
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.raid.create_raid_config('mdadm.conf')
        mock_command.assert_called_once_with(
            ['mdadm', '-Db', '/dev/md0']
        )
        file_mock.write.assert_called_once_with('data')
        self.raid.raid_device = None

    def test_is_loop(self):
        assert self.raid.is_loop() is True

    @patch('kiwi.storage.raid_device.Command.run')
    @patch('kiwi.storage.raid_device.log.warning')
    def test_destructor(self, mock_log_warn, mock_command):
        self.raid.raid_device = '/dev/md0'
        mock_command.side_effect = Exception
        self.raid.__del__()
        mock_command.assert_called_once_with(
            ['mdadm', '--stop', '/dev/md0']
        )
        assert mock_log_warn.called
        self.raid.raid_device = None
