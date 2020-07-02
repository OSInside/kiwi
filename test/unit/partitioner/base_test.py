from mock import Mock
from pytest import raises

from kiwi.partitioner.base import PartitionerBase


class TestPartitionerBase:
    def setup(self):
        disk_provider = Mock()
        disk_provider.get_device = Mock(
            return_value='/dev/loop0'
        )
        self.partitioner = PartitionerBase(disk_provider)

    def test_get_id(self):
        assert self.partitioner.get_id() == 0

    def test_create(self):
        with raises(NotImplementedError):
            self.partitioner.create('name', 100, 'type', ['flag'])

    def test_set_flag(self):
        with raises(NotImplementedError):
            self.partitioner.set_flag(1, 'flag')

    def test_set_hybrid_mbr(self):
        with raises(NotImplementedError):
            self.partitioner.set_hybrid_mbr()

    def test_set_mbr(self):
        with raises(NotImplementedError):
            self.partitioner.set_mbr()

    def test_resize_table(self):
        with raises(NotImplementedError):
            self.partitioner.resize_table()
