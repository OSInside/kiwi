from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.partitioner import Partitioner
from kiwi.exceptions import *


class TestPartitioner(object):
    @patch('platform.machine')
    @raises(KiwiPartitionerSetupError)
    def test_partitioner_not_implemented(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        Partitioner('foo', mock.Mock())

    @patch('platform.machine')
    @raises(KiwiPartitionerSetupError)
    def test_partitioner_for_arch_not_implemented(self, mock_machine):
        mock_machine.return_value = 'some-arch'
        Partitioner('foo', mock.Mock())

    @patch('kiwi.partitioner.PartitionerGpt')
    @patch('platform.machine')
    def test_partitioner_x86_64_gpt(self, mock_machine, mock_gpt):
        mock_machine.return_value = 'x86_64'
        storage_provider = mock.Mock()
        Partitioner('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_x86_64_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'x86_64'
        storage_provider = mock.Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_i686_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'i686'
        storage_provider = mock.Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_i586_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 'i586'
        storage_provider = mock.Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerDasd')
    @patch('platform.machine')
    def test_partitioner_s390_dasd(self, mock_machine, mock_dasd):
        mock_machine.return_value = 's390'
        storage_provider = mock.Mock()
        Partitioner('dasd', storage_provider)
        mock_dasd.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    @patch('platform.machine')
    def test_partitioner_s390_msdos(self, mock_machine, mock_dos):
        mock_machine.return_value = 's390'
        storage_provider = mock.Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider)
