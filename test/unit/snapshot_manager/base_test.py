from pytest import raises

from kiwi.snapshot_manager.base import SnapshotManagerBase


class TestSnapshotManagerBase:
    def setup(self):
        self.manager = SnapshotManagerBase(
            '/dev/device', 'root_dir', 'mountpoint', '@', None
        )

    def setup_method(self, cls):
        self.setup()

    def test_create_first_snapshot(self):
        with raises(NotImplementedError):
            self.manager.create_first_snapshot()

    def test_setup_first_snapshot(self):
        with raises(NotImplementedError):
            self.manager.setup_first_snapshot()

    def test_get_default_snapshot_name(self):
        with raises(NotImplementedError):
            self.manager.get_default_snapshot_name()
