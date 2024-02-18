import logging
from unittest.mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.partitioner import Partitioner

from kiwi.exceptions import KiwiPartitionerSetupError


class TestPartitioner:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_partitioner_not_implemented(self):
        with raises(KiwiPartitionerSetupError):
            Partitioner.new('foo', Mock())

    def test_partitioner_for_arch_not_implemented(self):
        with raises(KiwiPartitionerSetupError):
            Partitioner.new('foo', Mock())

    @patch('kiwi.partitioner.gpt.PartitionerGpt')
    def test_partitioner_gpt(self, mock_gpt):
        storage_provider = Mock()
        Partitioner.new('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider, None, False)

    @patch('kiwi.partitioner.msdos.PartitionerMsDos')
    def test_partitioner_msdos(self, mock_dos):
        storage_provider = Mock()
        Partitioner.new('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None, False)

    @patch('kiwi.partitioner.dasd.PartitionerDasd')
    def test_partitioner_dasd(self, mock_dasd):
        storage_provider = Mock()
        Partitioner.new('dasd', storage_provider)
        mock_dasd.assert_called_once_with(storage_provider, None, False)

    @patch('kiwi.partitioner.dasd.PartitionerDasd')
    def test_partitioner_dasd_with_custom_start_sector(self, mock_dasd):
        storage_provider = Mock()
        with self._caplog.at_level(logging.WARNING):
            Partitioner.new('dasd', storage_provider, 4096)
            mock_dasd.assert_called_once_with(storage_provider, None, False)
