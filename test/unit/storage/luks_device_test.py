import io
from mock import (
    patch, call, MagicMock, Mock
)
from pytest import raises

from kiwi.exceptions import KiwiLuksSetupError
from kiwi.storage.luks_device import LuksDevice


class TestLuksDevice:
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

    def test_create_crypto_luks_empty_passphrase(self):
        with raises(KiwiLuksSetupError):
            self.luks.create_crypto_luks('')

    def test_create_crypto_luks_unsupported_os_options(self):
        with raises(KiwiLuksSetupError):
            self.luks.create_crypto_luks('passphrase', 'some-os')

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.luks.luks_device = '/dev/mapper/luksRoot'
        assert self.luks.get_device().get_device() == '/dev/mapper/luksRoot'
        self.luks.luks_device = None

    @patch('kiwi.storage.luks_device.Command.run')
    @patch('kiwi.storage.luks_device.NamedTemporaryFile')
    def test_create_crypto_luks(self, mock_tmpfile, mock_command):
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_tmpfile.return_value = tmpfile
        with patch('builtins.open', create=True):
            self.luks.create_crypto_luks(
                passphrase='passphrase', os='sle12', keyfile='some-keyfile'
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
                        '/dev/some-device', 'some-keyfile'
                    ]
                ),
                call(
                    [
                        'cryptsetup', '--key-file', 'tmpfile', 'luksOpen',
                        '/dev/some-device', 'luksRoot'
                    ]
                )
            ]
            self.luks.luks_device = None

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
    def test_create_random_keyfile(self, mock_os_urandom):
        secret = b'secret'
        mock_os_urandom.return_value = secret
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            LuksDevice.create_random_keyfile('some-file')
            file_handle.write.assert_called_once_with(secret)

    def test_is_loop(self):
        assert self.luks.is_loop() is True

    @patch('kiwi.storage.luks_device.Command.run')
    @patch('kiwi.storage.luks_device.log.warning')
    def test_destructor(self, mock_log_warn, mock_command):
        self.luks.luks_device = '/dev/mapper/luksRoot'
        mock_command.side_effect = Exception
        self.luks.__del__()
        mock_command.assert_called_once_with(
            ['cryptsetup', 'luksClose', 'luksRoot']
        )
        assert mock_log_warn.called
        self.luks.luks_device = None
