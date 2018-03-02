import mock

from .test_helper import raises

from kiwi.partitioner.base import PartitionerBase


class TestPartitionerBase(object):
    def setup(self):
        disk_provider = mock.Mock()
        disk_provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        self.partitioner = PartitionerBase(disk_provider)

    def test_get_id(self):
        assert self.partitioner.get_id() == 0

    @raises(NotImplementedError)
    def test_create(self):
        self.partitioner.create('name', 100, 'type', ['flag'])

    @raises(NotImplementedError)
    def test_set_flag(self):
        self.partitioner.set_flag(1, 'flag')

    @raises(NotImplementedError)
    def test_set_hybrid_mbr(self):
        self.partitioner.set_hybrid_mbr()

    @raises(NotImplementedError)
    def test_set_mbr(self):
        self.partitioner.set_mbr()

    @raises(NotImplementedError)
    def test_resize_table(self):
        self.partitioner.resize_table()
