import logging
from mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.utils.compress import Compress

from kiwi.exceptions import (
    KiwiFileNotFound,
    KiwiCompressionFormatUnknown
)


class TestCompress:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.compress = Compress('some-file', True)

    def test_source_file_not_found(self):
        with raises(KiwiFileNotFound):
            Compress('some-file')

    @patch('kiwi.command.Command.run')
    def test_xz(self, mock_command):
        assert self.compress.xz() == 'some-file.xz'
        mock_command.assert_called_once_with(
            [
                'xz', '-f', '--threads=0', '--keep',
                'some-file'
            ]
        )
        assert self.compress.compressed_filename == 'some-file.xz'

    @patch('kiwi.command.Command.run')
    def test_xz_with_custom_options(self, mock_command):
        assert self.compress.xz(options=['foo', 'bar']) == 'some-file.xz'
        mock_command.assert_called_once_with(
            [
                'xz', '-f', 'foo', 'bar', '--keep',
                'some-file'
            ]
        )
        assert self.compress.compressed_filename == 'some-file.xz'

    @patch('kiwi.command.Command.run')
    def test_gzip(self, mock_command):
        assert self.compress.gzip() == 'some-file.gz'
        mock_command.assert_called_once_with(
            ['gzip', '-f', '-9', '--keep', 'some-file']
        )
        assert self.compress.compressed_filename == 'some-file.gz'

    @patch('kiwi.command.Command.run')
    @patch('kiwi.utils.compress.Temporary.new_file')
    @patch('kiwi.utils.compress.Compress.get_format')
    def test_uncompress(self, mock_format, mock_temp, mock_command):
        mock_format.return_value = 'xz'
        self.compress.uncompress()
        mock_command.assert_called_once_with(
            ['xz', '-d', 'some-file']
        )
        assert self.compress.uncompressed_filename == 'some-file'

    @patch('kiwi.command.Command.run')
    @patch('kiwi.utils.compress.Temporary.new_file')
    @patch('kiwi.utils.compress.Compress.get_format')
    def test_uncompress_temporary(self, mock_format, mock_temp, mock_command):
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_temp.return_value = tempfile
        mock_format.return_value = 'xz'
        self.compress.uncompress(temporary=True)
        mock_command.assert_called_once_with(
            ['bash', '-c', 'xz -c -d some-file > tempfile']
        )
        assert self.compress.uncompressed_filename == 'tempfile'

    @patch('kiwi.utils.compress.Compress.get_format')
    def test_uncompress_unknown_format(self, mock_format):
        mock_format.return_value = None
        with raises(KiwiCompressionFormatUnknown):
            self.compress.uncompress()

    @patch('kiwi.path.Path.which')
    def test_get_format(self, mock_which):
        mock_which.return_value = 'ziptool'
        xz = Compress('../data/xz_data.xz')
        assert xz.get_format() == 'xz'
        gzip = Compress('../data/gz_data.gz')
        assert gzip.get_format() == 'gzip'

    @patch('kiwi.command.Command.run')
    def test_get_format_invalid_format(self, mock_run):
        mock_run.side_effect = ValueError("nothing")
        invalid = Compress("../data/gz_data.gz")
        invalid.supported_zipper = ["mock_zip"]

        with self._caplog.at_level(logging.DEBUG):
            assert invalid.get_format() is None
            mock_run.assert_called_once_with(
                ['mock_zip', '-l', '../data/gz_data.gz']
            )
            assert 'Error running "mock_zip -l ../data/gz_data.gz", got a'
            ' ValueError: nothing' in self._caplog.text
