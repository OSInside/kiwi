from pytest import raises

from kiwi.utils.os_release import OsRelease
from kiwi.exceptions import KiwiOSReleaseImportError


class TestOsRelease(object):
    def setup(self):
        self.os_release = OsRelease('../data')

    def setup_method(self, cls):
        self.setup()

    def test_setup_raises(self):
        with raises(KiwiOSReleaseImportError):
            OsRelease('does-not-exist')

    def test_get(self):
        assert self.os_release.get('ID') == 'opensuse-leap'
