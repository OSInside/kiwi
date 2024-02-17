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
        find_command = \
            'find . -path ./boot -prune -or -path ./var/cache -prune -o -print'
        cpio_command = 'cpio --quiet -o -H newc'
        mock_command.assert_called_once_with(
            [
                'bash', '-c',
                ''.join(
                    [
                        'cd source-dir && ', find_command, ' | ',
                        cpio_command, ' > foo.cpio'
                    ]
                )
            ]
        )

    @patch('kiwi.archive.cpio.Command.run')
    def test_extract(self, mock_command):
        self.archive.extract('dest-dir')
        bash_command = \
            'cd dest-dir && cat foo.cpio | cpio -i --make-directories'
        mock_command.assert_called_once_with(
            ['bash', '-c', bash_command]
        )
