import logging
from unittest.mock import (
    patch, Mock, mock_open
)
from pytest import (
    raises, fixture
)

from kiwi.storage.raid_device import RaidDevice

from kiwi.exceptions import KiwiRaidSetupError


class TestRaidDevice:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        storage_device = Mock()
        storage_device.get_device = Mock(
            return_value='/dev/some-device'
        )
        storage_device.is_loop = Mock(
            return_value=True
        )
        self.raid = RaidDevice(storage_device)

    def setup_method(self, cls):
        self.setup()

    def test_create_degraded_raid_invalid_level(self):
        with raises(KiwiRaidSetupError):
            self.raid.create_degraded_raid('bogus-level')

    @patch('os.path.exists')
    def test_create_degraded_raid_no_free_device(self, mock_path):
        mock_path.return_value = True
        with raises(KiwiRaidSetupError):
            self.raid.create_degraded_raid('mirroring')

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.raid.raid_device = '/dev/md0'
        assert self.raid.get_device().get_device() == '/dev/md0'
        self.raid.raid_device = None

    def test_get_device_no_mapped_device(self):
        assert self.raid.get_device() is None

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
    def test_create_raid_config(self, mock_command):
        self.raid.raid_device = '/dev/md0'
        command_call = Mock()
        command_call.output = 'data'
        mock_command.return_value = command_call

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.raid.create_raid_config('mdadm.conf')

        mock_command.assert_called_once_with(
            ['mdadm', '-Db', '/dev/md0']
        )
        m_open.return_value.write.assert_called_once_with('data')
        self.raid.raid_device = None

    @patch('kiwi.storage.raid_device.Command.run')
    def test_create_raid_config_without_raid_device(self, mock_command):
        self.raid.raid_device = None

        with raises(KiwiRaidSetupError) as raid_err_ctx:
            self.raid.create_raid_config('mdadm.conf')

        assert "No raid device" in str(raid_err_ctx.value)
        mock_command.assert_not_called()

    def test_is_loop(self):
        assert self.raid.is_loop() is True

    @patch('kiwi.storage.raid_device.Command.run')
    @patch('kiwi.storage.raid_device.log.warning')
    def test_context_manager_exit(self, mock_log_warn, mock_command):
        mock_command.side_effect = Exception
        with self._caplog.at_level(logging.ERROR):
            with RaidDevice(Mock()) as raid:
                raid.raid_device = '/dev/md0'
        mock_command.assert_called_once_with(
            ['mdadm', '--stop', '/dev/md0']
        )
