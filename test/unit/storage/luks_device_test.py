import logging
import io
from unittest.mock import (
    patch, call, MagicMock, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.exceptions import KiwiLuksSetupError
from kiwi.storage.luks_device import LuksDevice


class TestLuksDevice:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        storage_device = Mock()
        storage_device.get_byte_size = Mock(
            return_value=1048576
        )
        storage_device.get_uuid = Mock(
            return_value='0815'
        )
        storage_device.get_device = Mock(
            return_value='/dev/some-device'
        )
        storage_device.is_loop = Mock(
            return_value=True
        )
        self.luks = LuksDevice(storage_device)

    def setup_method(self, cls):
        self.setup()

    def test_create_crypto_luks_unsupported_os_options(self):
        with raises(KiwiLuksSetupError):
            self.luks.create_crypto_luks('passphrase', 'some-os')

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.luks.luks_device = '/dev/mapper/luksRoot'
        assert self.luks.get_device().get_device() == '/dev/mapper/luksRoot'
        self.luks.luks_device = None

    @patch('os.path.exists')
    def test_get_device_none(self, mock_path):
        mock_path.return_value = True
        self.luks.luks_device = None
        assert self.luks.get_device() is None

    @patch('kiwi.storage.luks_device.Command.run')
    @patch('os.chmod')
    def test_create_crypto_luks_empty_passphrase(
        self, mock_os_chmod, mock_command
    ):
        with patch('builtins.open', create=True):
            self.luks.create_crypto_luks(
                passphrase='', osname='sle12',
                keyfile='some-keyfile', root_dir='root'
            )
            assert mock_command.call_args_list == [
                call(
                    [
                        'dd', 'if=/dev/urandom', 'bs=1M', 'count=1',
                        'of=/dev/some-device'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '-q', '--key-file', '/dev/zero',
                        '--cipher', 'aes-xts-plain64',
                        '--key-size', '256', '--hash', 'sha1',
                        '--keyfile-size', '32',
                        'luksFormat', '/dev/some-device'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '--key-file', '/dev/zero',
                        '--keyfile-size', '32',
                        'luksAddKey', '/dev/some-device', 'root/some-keyfile'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '--key-file', '/dev/zero',
                        '--keyfile-size', '32',
                        'luksOpen', '/dev/some-device', 'luksRoot'
                    ]
                )
            ]
            self.luks.luks_device = None

    @patch('kiwi.storage.luks_device.LuksDevice')
    @patch('kiwi.storage.luks_device.Command.run')
    @patch('kiwi.storage.luks_device.Temporary.new_file')
    @patch('os.chmod')
    def test_create_crypto_luks(
        self, mock_os_chmod, mock_tmpfile, mock_command, mock_LuksDevice
    ):
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_tmpfile.return_value = tmpfile
        with patch('builtins.open', create=True):
            self.luks.create_crypto_luks(
                passphrase='passphrase', osname='sle12',
                keyfile='some-keyfile', root_dir='root'
            )
            assert mock_command.call_args_list == [
                call(
                    [
                        'dd', 'if=/dev/urandom', 'bs=1M', 'count=1',
                        'of=/dev/some-device'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '-q', '--key-file', 'tmpfile',
                        '--cipher', 'aes-xts-plain64',
                        '--key-size', '256', '--hash', 'sha1',
                        'luksFormat', '/dev/some-device'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '--key-file', 'tmpfile', 'luksAddKey',
                        '/dev/some-device', 'root/some-keyfile'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '--key-file', 'tmpfile', 'luksOpen',
                        '/dev/some-device', 'luksRoot'
                    ]
                )
            ]
            mock_LuksDevice.create_random_keyfile.assert_called_once_with(
                'root/some-keyfile'
            )
            assert self.luks.luks_keyfile == 'some-keyfile'
            self.luks.luks_device = ''

    def test_create_crypttab(self):
        self.luks.luks_device = '/dev/mapper/luksRoot'
        self.luks.luks_keyfile = None
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.luks.create_crypttab('crypttab')
            file_handle.write.assert_called_once_with(
                'luks UUID=0815\n'
            )
            self.luks.luks_device = None
        self.luks.luks_keyfile = 'some-keyfile'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.luks.create_crypttab('crypttab')
            file_handle.write.assert_called_once_with(
                'luks UUID=0815 /some-keyfile\n'
            )
            self.luks.luks_device = None

    @patch('os.urandom')
    @patch('os.chmod')
    def test_create_random_keyfile(self, mock_os_chmod, mock_os_urandom):
        secret = b'secret'
        mock_os_urandom.return_value = secret
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            LuksDevice.create_random_keyfile('some-file')
            file_handle.write.assert_called_once_with(secret)
            mock_os_chmod.assert_called_once_with('some-file', 0o600)

    def test_is_loop(self):
        assert self.luks.is_loop() is True

    @patch('kiwi.storage.luks_device.Command.run')
    @patch('kiwi.storage.luks_device.log.warning')
    def test_context_manager_exit(self, mock_log_warn, mock_command):
        mock_command.side_effect = Exception
        with self._caplog.at_level(logging.ERROR):
            with LuksDevice(Mock()) as luks:
                luks.luks_device = '/dev/mapper/luksRoot'
        mock_command.assert_called_once_with(
            ['cryptsetup', 'luksClose', 'luksRoot']
        )
