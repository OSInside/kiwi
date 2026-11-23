from unittest.mock import patch

from kiwi.archive.cpio import ArchiveCpio


class TestArchiveCpio:
    def setup(self):
        self.archive = ArchiveCpio('foo.cpio')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.archive.cpio.Command.run')
    def test_create(self, mock_command):
        self.archive.create('source-dir', ['/boot', '/var/cache'])
        find_command = (
            'find . -path ./boot -prune -or -path ./var/cache -prune -o -print'
        )
        cpio_command = 'cpio --quiet -o -H newc'
        mock_command.assert_called_once_with(
            [
                'bash',
                '-c',
                ''.join(
                    [
                        'cd source-dir && ',
                        find_command,
                        ' | ',
                        cpio_command,
                        ' > foo.cpio',
                    ]
                ),
            ]
        )

    @patch('kiwi.archive.cpio.Command.run')
    def test_extract(self, mock_command):
        self.archive.extract('dest-dir')
        bash_command = (
            'cd dest-dir && cat foo.cpio | cpio -i --make-directories'
        )
        mock_command.assert_called_once_with(['bash', '-c', bash_command])

    @patch('kiwi.archive.cpio.CommandCapabilities.check_version')
    @patch('kiwi.archive.cpio.Command.run')
    def test_create_reproducible(self, mock_command, mock_check_version):
        mock_check_version.return_value = True
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            self.archive.create('source-dir')
        mock_command.assert_called_once_with(
            [
                'bash',
                '-c',
                'cd source-dir && find . | LC_ALL=C sort | '
                'cpio --reproducible --quiet -o -H newc > foo.cpio',
            ]
        )
        mock_check_version.assert_called_once_with(
            'cpio', (2, 12), raise_on_error=False
        )
        mock_command.reset_mock()
        mock_check_version.return_value = False
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            self.archive.create('source-dir')
        mock_command.assert_called_once_with(
            [
                'bash',
                '-c',
                'cd source-dir && find . | cpio --quiet -o -H newc > foo.cpio',
            ]
        )
