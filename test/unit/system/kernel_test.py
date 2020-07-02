import mock
import os
from mock import patch
from pytest import raises

from kiwi.system.kernel import Kernel

from kiwi.exceptions import KiwiKernelLookupError


class TestKernel:
    @patch('os.listdir')
    def setup(self, mock_listdir):
        mock_listdir.return_value = ['1.2.3-default']
        self.kernel = Kernel('root-dir')
        assert self.kernel.kernel_names == [
            'uImage-1.2.3-default',
            'Image-1.2.3-default',
            'zImage-1.2.3-default',
            'vmlinuz-1.2.3-default',
            'image-1.2.3-default',
            'vmlinux-1.2.3-default'
        ]

    def test_get_kernel_raises_if_no_kernel_found(self):
        self.kernel.kernel_names = []
        with raises(KiwiKernelLookupError):
            self.kernel.get_kernel(raise_on_not_found=True)

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

    @patch('kiwi.system.kernel.Kernel.get_kernel')
    @patch('kiwi.command.Command.run')
    def test_copy_kernel(self, mock_run, mock_get_kernel):
        result = mock.MagicMock()
        result.version = '42'
        result.filename = 'kernel'
        mock_get_kernel.return_value = result
        self.kernel.copy_kernel('target-dir')
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
        self.kernel.copy_xen_hypervisor('target-dir')
        mock_run.assert_called_once_with(
            ['cp', 'some/xen.gz', 'target-dir/hypervisor-xen.gz']
        )
