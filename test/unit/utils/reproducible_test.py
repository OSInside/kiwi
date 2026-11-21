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
