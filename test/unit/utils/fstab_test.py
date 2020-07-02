import io
import logging
from pytest import fixture
from unittest.mock import (
    MagicMock, patch, call
)
from kiwi.utils.fstab import Fstab


class TestFstab(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.fstab = Fstab()
        with self._caplog.at_level(logging.WARNING):
            self.fstab.read('../data/fstab')
            assert format(
                'Mountpoint for "LABEL=bar /home xfs defaults 0 0" '
                'in use by "LABEL=foo /home ext4 defaults 0 0", skipped'
            ) in self._caplog.text

    def test_get_devices(self):
        assert self.fstab.get_devices() == [
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/',
                device_path='/dev/disk/'
                'by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                device_spec='UUID=bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='acl,user_xattr'
            ),
            self.fstab.fstab_entry_type(
                fstype='swap',
                mountpoint='swap',
                device_path='/dev/disk/'
                'by-uuid/daa5a8c3-5c72-4343-a1d4-bb74ec4e586e',
                device_spec='UUID=daa5a8c3-5c72-4343-a1d4-bb74ec4e586e',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device_path='/dev/disk/by-uuid/FCF7-B051',
                device_spec='UUID=FCF7-B051',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='xfs',
                mountpoint='/boot',
                device_path='/dev/disk/by-label/BOOT',
                device_spec='LABEL=BOOT',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device_path='/dev/disk/by-label/foo',
                device_spec='LABEL=foo',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/bar',
                device_path='/dev/disk/by-partuuid/3c8bd108-01',
                device_spec='PARTUUID=3c8bd108-01',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/foo',
                device_path='/dev/mynode',
                device_spec='/dev/mynode',
                options='defaults'
            )
        ]

    def test_export_and_canonical_order(self):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            self.fstab.export('filename')
            file_handle = mock_open.return_value.__enter__.return_value
            mock_open.assert_called_once_with(
                'filename', 'w'
            )
            assert file_handle.write.call_args_list == [
                call(
                    'UUID=daa5a8c3-5c72-4343-a1d4-bb74ec4e586e swap '
                    'swap defaults 0 0\n'
                ),
                call(
                    'UUID=bd604632-663b-4d4c-b5b0-8d8686267ea2 / '
                    'ext4 acl,user_xattr 0 0\n'
                ),
                call('PARTUUID=3c8bd108-01 /bar ext4 defaults 0 0\n'),
                call('LABEL=BOOT /boot xfs defaults 0 0\n'),
                call('/dev/mynode /foo ext4 defaults 0 0\n'),
                call('LABEL=foo /home ext4 defaults 0 0\n'),
                call('UUID=FCF7-B051 /boot/efi vfat defaults 0 0\n')
            ]
