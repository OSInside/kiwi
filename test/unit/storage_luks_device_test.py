from mock import patch
from mock import call
import mock

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiLuksSetupError
from kiwi.storage.luks_device import LuksDevice


class TestLuksDevice(object):
    def setup(self):
        storage_device = mock.Mock()
        storage_device.get_byte_size = mock.Mock(
            return_value=1048576
        )
        storage_device.get_uuid = mock.Mock(
            return_value='0815'
        )
        storage_device.get_device = mock.Mock(
            return_value='/dev/some-device'
        )
        storage_device.is_loop = mock.Mock(
            return_value=True
        )
        self.luks = LuksDevice(storage_device)

    @raises(KiwiLuksSetupError)
    def test_create_crypto_luks_empty_passphrase(self):
        self.luks.create_crypto_luks('')

    @raises(KiwiLuksSetupError)
    def test_create_crypto_luks_unsupported_os_options(self):
        self.luks.create_crypto_luks('passphrase', 'some-os')

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.luks.luks_device = '/dev/mapper/luksRoot'
        assert self.luks.get_device().get_device() == '/dev/mapper/luksRoot'
        self.luks.luks_device = None

    @patch('kiwi.storage.luks_device.Command.run')
    @patch('kiwi.storage.luks_device.NamedTemporaryFile')
    @patch_open
    def test_create_crypto_luks(self, mock_open, mock_tmpfile, mock_command):
        tmpfile = mock.Mock()
        tmpfile.name = 'tmpfile'
        mock_tmpfile.return_value = tmpfile
        self.luks.create_crypto_luks('passphrase', 'sle12')
        assert mock_command.call_args_list == [
            call([
                'dd', 'if=/dev/urandom', 'bs=1M', 'count=1',
                'of=/dev/some-device'
            ]),
            call([
                'cryptsetup', '-q', '--key-file', 'tmpfile',
                '--cipher', 'aes-xts-plain64',
                '--key-size', '256', '--hash', 'sha1',
                'luksFormat', '/dev/some-device'
            ]),
            call([
                'cryptsetup', '--key-file', 'tmpfile', 'luksOpen',
                '/dev/some-device', 'luksRoot'
            ])
        ]
        self.luks.luks_device = None

    @patch_open
    def test_create_crypttab(self, mock_open):
        self.luks.luks_device = '/dev/mapper/luksRoot'
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.luks.create_crypttab('crypttab')
        file_mock.write.assert_called_once_with('luks UUID=0815\n')
        self.luks.luks_device = None

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
