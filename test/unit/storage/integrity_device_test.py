import logging
import io
from textwrap import dedent
from pytest import (
    raises, fixture
)
from unittest.mock import (
    patch, Mock, call, MagicMock
)

from kiwi.storage.integrity_device import (
    IntegrityDevice,
    integrity_credentials_type
)
from kiwi.exceptions import KiwiOffsetError

import kiwi.defaults as defaults


class TestIntegrityDevice:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.getsize')
    def setup(self, mock_os_path_getsize):
        mock_os_path_getsize.return_value = 42
        metadata_file = Mock()
        metadata_file.name = 'metadata_file'
        storage_device = Mock()
        storage_device.get_device = Mock(
            return_value='/dev/some-device'
        )
        storage_device.is_loop = Mock(
            return_value=True
        )

        self.integrity = IntegrityDevice(
            storage_device, defaults.INTEGRITY_ALGORITHM
        )

        self.integrity_hmac = IntegrityDevice(
            storage_device, defaults.INTEGRITY_ALGORITHM,
            integrity_credentials_type(
                keydescription=None,
                keyfile='/etc/pki/storage/dm-integrity-hmac-secret.bin',
                keyfile_algorithm=defaults.INTEGRITY_KEY_ALGORITHM,
                options=['legacy_hmac']
            )
        )

        self.integrity.integrity_metadata_file = metadata_file

    @patch('os.path.getsize')
    def setup_method(self, cls, mock_os_path_getsize):
        self.setup()

    @patch('kiwi.storage.integrity_device.MappedDevice')
    def test_get_device(self, mock_MappedDevice):
        self.integrity.integrity_device = '/dev/some-device'
        assert self.integrity.get_device() == mock_MappedDevice.return_value
        self.integrity.integrity_device = None
        assert self.integrity.get_device() is None

    def test_is_loop(self):
        assert self.integrity.is_loop() is True

    @patch('kiwi.storage.integrity_device.Command.run')
    def test_create_dm_integrity(self, mock_Command_run):
        self.integrity.create_dm_integrity()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'integritysetup', '-v', '--batch-mode', 'format',
                    '--integrity', 'sha256', '--sector-size', '512',
                    '/dev/some-device'
                ]
            ),
            call(
                [
                    'integritysetup', '-v', '--batch-mode', 'open',
                    '--integrity', 'sha256',
                    '/dev/some-device', 'integrityRoot'
                ]
            )
        ]

    @patch('kiwi.storage.integrity_device.Command.run')
    def test_create_dm_integrity_with_hmac(self, mock_Command_run):
        self.integrity_hmac.create_dm_integrity()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'integritysetup', '-v', '--batch-mode', 'format',
                    '--integrity', 'hmac-sha256', '--sector-size', '512',
                    '--integrity-legacy-hmac',
                    '--integrity-key-file',
                    '/etc/pki/storage/dm-integrity-hmac-secret.bin',
                    '--integrity-key-size', '42',
                    '/dev/some-device'
                ]
            ),
            call(
                [
                    'integritysetup', '-v', '--batch-mode', 'open',
                    '--integrity', 'hmac-sha256',
                    '--integrity-key-file',
                    '/etc/pki/storage/dm-integrity-hmac-secret.bin',
                    '--integrity-key-size', '42',
                    '/dev/some-device', 'integrityRoot'
                ]
            )
        ]

    @patch('kiwi.storage.integrity_device.Command.run')
    @patch('kiwi.storage.integrity_device.BlockID')
    def test_create_integrity_metadata(
        self, mock_BlockID, mock_Command_run
    ):
        mock_BlockID.return_value.get_filesystem.return_value = 'xfs'
        mock_Command_run.return_value.output = dedent('''\n
            Info for integrity device /dev/mapper/loop0p4.
            superblock_version 4
            log2_interleave_sectors 15
            integrity_tag_size 32
            journal_sections 212
            provided_data_sectors 2234096
            sector_size 512
            log2_blocks_per_bitmap 15
            flags fix_padding
        ''')
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.integrity.create_integrity_metadata()
        assert file_handle.write.call_args_list == [
            call(b'1 xfs rw integrity'),
            call(b'\xff'),
            call(b'2234096 512 2 internal_hash:sha256 fix_padding'),
            call(b'\xff'),
            call(b'\x00')
        ]

    @patch('kiwi.storage.integrity_device.Command.run')
    @patch('kiwi.storage.integrity_device.BlockID')
    def test_create_integrity_metadata_with_hmac(
        self, mock_BlockID, mock_Command_run
    ):
        mock_BlockID.return_value.get_filesystem.return_value = 'xfs'
        mock_Command_run.return_value.output = dedent('''\n
            Info for integrity device /dev/mapper/loop0p4.
            superblock_version 4
            log2_interleave_sectors 15
            integrity_tag_size 32
            journal_sections 212
            provided_data_sectors 2234096
            sector_size 512
            log2_blocks_per_bitmap 15
            flags fix_padding
        ''')
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.integrity_hmac.create_integrity_metadata()
        assert file_handle.write.call_args_list == [
            call(b'1 xfs rw integrity'),
            call(b'\xff'),
            call(
                b'2234096 512 2 internal_hash:'
                b'hmac(sha256)::dm-integrity-hmac-secret fix_padding'
            ),
            call(b'\xff'),
            call(b'\x00')
        ]

    @patch('kiwi.storage.integrity_device.Signature')
    def test_sign_integrity_metadata(self, mock_Signature):
        self.integrity.sign_integrity_metadata()
        mock_Signature.return_value.sign.assert_called_once_with()

    @patch('os.path.getsize')
    def test_write_integrity_metadata_raises(self, mock_os_path_getsize):
        mock_os_path_getsize.return_value = 8192
        with raises(KiwiOffsetError):
            self.integrity.write_integrity_metadata()

    @patch('os.path.getsize')
    def test_write_integrity_metadata(self, mock_os_path_getsize):
        mock_os_path_getsize.return_value = 4096
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.integrity.write_integrity_metadata()
        assert mock_open.call_args_list == [
            call('metadata_file', 'rb'),
            call('/dev/some-device', 'r+b')
        ]
        file_handle.seek.assert_called_once_with(
            -defaults.DM_METADATA_OFFSET, 2
        )
        file_handle.write.assert_called_once_with(
            file_handle.read.return_value
        )

    @patch('kiwi.storage.integrity_device.BlockID')
    def test_create_integritytab(self, mock_BlockID):
        mock_BlockID.return_value.get_blkid.return_value = 'id'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.integrity.create_integritytab('integritytab')
            file_handle.write.assert_called_once_with(
                'integrityRoot PARTUUID=id - integrity-algorithm=sha256\n'
            )

    @patch('kiwi.storage.integrity_device.BlockID')
    def test_create_integritytab_with_keyfile(self, mock_BlockID):
        mock_BlockID.return_value.get_blkid.return_value = 'id'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.integrity_hmac.create_integritytab('integritytab')
            file_handle.write.assert_called_once_with(
                'integrityRoot PARTUUID=id '
                '/etc/pki/storage/dm-integrity-hmac-secret.bin '
                'integrity-algorithm=hmac-sha256\n'
            )

    @patch('kiwi.storage.integrity_device.Command.run')
    @patch('kiwi.storage.integrity_device.log.warning')
    def test_context_manager_exit(self, mock_log_warn, mock_Command_run):
        mock_Command_run.side_effect = Exception
        with self._caplog.at_level(logging.ERROR):
            with IntegrityDevice(
                Mock(), defaults.INTEGRITY_ALGORITHM
            ) as integrity:
                integrity.integrity_device = '/dev/mapper/integrityRoot'
        mock_Command_run.assert_called_once_with(
            ['integritysetup', 'close', 'integrityRoot']
        )
