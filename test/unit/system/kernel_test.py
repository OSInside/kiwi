import unittest.mock as mock
import os
from unittest.mock import patch
from pytest import raises

from kiwi.system.kernel import Kernel

from kiwi.exceptions import KiwiKernelLookupError


class TestKernel:
    @patch('os.listdir')
    @patch('os.path.isdir')
    def setup(self, mock_path_isdir, mock_listdir):
        mock_path_isdir.return_value = True
        mock_listdir.return_value = ['1.2.3-default']
        self.kernel = Kernel('root-dir')

    @patch('os.listdir')
    @patch('os.path.isdir')
    def setup_method(self, cls, mock_path_isdir, mock_listdir):
        self.setup()

    def test_get_kernel_raises_if_no_kernel_found(self):
        self.kernel.kernel_names = []
        with raises(KiwiKernelLookupError):
            self.kernel.get_kernel(raise_on_not_found=True)

    def test_get_kernel_returns_none(self):
        self.kernel.kernel_names = []
        assert self.kernel.get_kernel() is None

    @patch('os.path.exists')
    @patch('os.path.realpath')
    def test_get_kernel(self, mock_os_path_realpath, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        kernel = self.kernel.get_kernel()
        assert kernel.filename == 'root-dir/boot/uImage-1.2.3-default'
        assert kernel.version == '1.2.3-default'
        assert kernel.name == os.path.basename(
            mock_os_path_realpath.return_value
        )

    @patch('os.path.exists')
    def test_get_xen_hypervisor(self, mock_os):
        mock_os.return_value = True
        data = self.kernel.get_xen_hypervisor()
        assert data.filename == 'root-dir/boot/xen.gz'
        assert data.name == 'xen.gz'

    @patch('os.path.exists')
    def test_get_xen_hypervisor_not_found(self, mock_os):
        mock_os.return_value = False
        assert self.kernel.get_xen_hypervisor() is None

    @patch('kiwi.system.kernel.Kernel.get_kernel')
    @patch('kiwi.command.Command.run')
    def test_copy_kernel(self, mock_run, mock_get_kernel):
        result = mock.MagicMock()
        result.version = '42'
        result.filename = 'kernel'
        mock_get_kernel.return_value = result
        assert self.kernel.copy_kernel('target-dir') is None
        mock_run.assert_called_once_with(
            ['cp', 'kernel', 'target-dir/kernel-42.kernel']
        )

    @patch('kiwi.system.kernel.Kernel.get_xen_hypervisor')
    @patch('kiwi.command.Command.run')
    def test_copy_xen_hypervisor(self, mock_run, mock_get_xen):
        result = mock.MagicMock()
        result.name = 'xen.gz'
        result.filename = 'some/xen.gz'
        mock_get_xen.return_value = result
        assert self.kernel.copy_xen_hypervisor('target-dir') is None
        mock_run.assert_called_once_with(
            ['cp', 'some/xen.gz', 'target-dir/hypervisor-xen.gz']
        )
