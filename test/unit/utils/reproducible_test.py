import os
from unittest.mock import patch

from kiwi.utils.reproducible import Reproducible


class TestReproducible:
    def test_get_source_date_epoch(self):
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            assert Reproducible.get_source_date_epoch() == 42
        with patch.dict('os.environ', {}, clear=True):
            assert Reproducible.get_source_date_epoch() is None

    def test_get_seeded_uuid(self):
        with patch.dict('os.environ', {}, clear=True):
            assert Reproducible.get_seeded_uuid('seed') is None
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            uuid_a = Reproducible.get_seeded_uuid('a')
            assert uuid_a == Reproducible.get_seeded_uuid('a')
            assert uuid_a != Reproducible.get_seeded_uuid('b')
            assert uuid_a == '3b164b19-8aea-56b8-a69b-c59a581dc1f6'
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '43'}):
            assert uuid_a != Reproducible.get_seeded_uuid('a')

    def test_get_seeded_hex(self):
        with patch.dict('os.environ', {}, clear=True):
            assert Reproducible.get_seeded_hex('seed') is None
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            hex_a = Reproducible.get_seeded_hex('a')
            assert len(hex_a) == 64
            assert hex_a == Reproducible.get_seeded_hex('a')
            assert hex_a != Reproducible.get_seeded_hex('b')

    def test_clamp_mtime(self, tmp_path):
        old_file = tmp_path / 'old'
        old_file.write_text('old')
        os.utime(old_file, (10, 10))
        sub_dir = tmp_path / 'sub'
        sub_dir.mkdir()
        new_file = sub_dir / 'new'
        new_file.write_text('new')
        link = tmp_path / 'link'
        link.symlink_to('does-not-exist')
        with patch.dict('os.environ', {}, clear=True):
            Reproducible.clamp_mtime(str(tmp_path))
            assert new_file.stat().st_mtime > 42
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            Reproducible.clamp_mtime(str(tmp_path))
        assert old_file.stat().st_mtime == 10
        assert new_file.stat().st_mtime == 42
        assert sub_dir.stat().st_mtime == 42
        assert tmp_path.stat().st_mtime == 42
        assert os.lstat(link).st_mtime == 42

    @patch('kiwi.utils.reproducible.os.cpu_count')
    @patch('kiwi.utils.reproducible.CommandCapabilities.check_version')
    def test_get_xz_options(self, mock_check_version, mock_cpu_count):
        options = ['--threads=0', '-9']
        mock_cpu_count.return_value = 8
        with patch.dict('os.environ', {}, clear=True):
            # without SOURCE_DATE_EPOCH the options are kept as they are
            result = Reproducible.get_xz_options(options)
            assert result == options
            assert result is not options
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '42'}):
            # explicit threads count, xz output is independent of the host
            assert Reproducible.get_xz_options(['--threads=4']) == [
                '--threads=4'
            ]
            assert not mock_check_version.called
            # xz >= 5.4 always uses multi-threaded mode for --threads=0
            mock_check_version.return_value = True
            assert Reproducible.get_xz_options(options) == options
            mock_check_version.assert_called_once_with(
                'xz', (5, 4), raise_on_error=False
            )
            # older xz uses single-threaded mode for --threads=0 on a
            # host with one CPU, an explicit thread count is used
            mock_check_version.return_value = False
            for threads in (['--threads=0'], ['-T0'], ['-T', '0']):
                assert Reproducible.get_xz_options(
                    ['-9'] + threads + ['--threads', '0', '-e']
                ) == ['-9', '--threads=8', '--threads=8', '-e']
            # at least two threads are needed for multi-threaded mode
            for cpu_count in (1, None):
                mock_cpu_count.return_value = cpu_count
                assert Reproducible.get_xz_options(options) == [
                    '--threads=2',
                    '-9',
                ]
