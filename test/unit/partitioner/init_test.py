import logging
from mock import (
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

    @patch('platform.machine')
    def test_partitioner_not_implemented(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        with raises(KiwiPartitionerSetupError):
            Partitioner('foo', Mock())

    @patch('platform.machine')
    def test_partitioner_for_arch_not_implemented(self, mock_machine):
        mock_machine.return_value = 'some-arch'
        with raises(KiwiPartitionerSetupError):
            Partitioner('foo', Mock())

    @patch('kiwi.partitioner.PartitionerGpt')
    @patch('platform.machine')
    def test_partitioner_x86_64_gpt(self, mock_machine, mock_gpt):
        mock_machine.return_value = 'x86_64'
        storage_provider = Mock()
        Partitioner('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_x86_64_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'x86_64'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_i686_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'i686'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_i586_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'i586'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerDasd')
    @patch('platform.machine')
    def test_partitioner_s390_dasd(self, mock_machine, mock_dasd):
        mock_machine.return_value = 's390'
        storage_provider = Mock()
        Partitioner('dasd', storage_provider)
        mock_dasd.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerDasd')
    @patch('platform.machine')
    def test_partitioner_s390_dasd_with_custom_start_sector(
        self, mock_machine, mock_dasd
    ):
        mock_machine.return_value = 's390'
        storage_provider = Mock()
        with self._caplog.at_level(logging.WARNING):
            Partitioner('dasd', storage_provider, 4096)
            mock_dasd.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_s390_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 's390'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_ppc_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'ppc64'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerGpt')
    @patch('platform.machine')
    def test_partitioner_ppc_gpt(self, mock_machine, mock_gpt):
        mock_machine.return_value = 'ppc64'
        storage_provider = Mock()
        Partitioner('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerGpt')
    @patch('platform.machine')
    def test_partitioner_arm_gpt(self, mock_machine, mock_gpt):
        mock_machine.return_value = 'aarch64'
        storage_provider = Mock()
        Partitioner('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider, None)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_arm_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'armv7l'
        storage_provider = Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider, None)
