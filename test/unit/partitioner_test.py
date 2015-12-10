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
    def test_partitioner_gpt_new(self, mock_gpt):
        storage_provider = mock.Mock()
        Partitioner('gpt', storage_provider)
        mock_gpt.assert_called_once_with(storage_provider)

    @patch('kiwi.partitioner.PartitionerMsDos')
    def test_partitioner_msdos_new(self, mock_dos):
        storage_provider = mock.Mock()
        Partitioner('msdos', storage_provider)
        mock_dos.assert_called_once_with(storage_provider)
