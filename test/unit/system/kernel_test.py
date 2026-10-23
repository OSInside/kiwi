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


class TestKernelSelection:
    """
    Kernel lookup in a root tree with more than one kernel
    """
    def _install(self, root_dir, version, image, modules_dir='lib/modules'):
        (root_dir / modules_dir / version).mkdir(parents=True, exist_ok=True)
        if image.startswith('boot/'):
            (root_dir / 'boot').mkdir(exist_ok=True)
            (root_dir / image).touch()
        elif image:
            (root_dir / modules_dir / version / image).touch()

    def test_version_key(self):
        versions = [
            '6.10.1-1-default',
            '6.4.0-150600.23.7-default',
            '6.9.12-1-default',
            '6.4.0-150600.23.25-default',
            '5.14.21-150500.55.19-default'
        ]
        assert sorted(versions, key=Kernel.version_key) == [
            '5.14.21-150500.55.19-default',
            '6.4.0-150600.23.7-default',
            '6.4.0-150600.23.25-default',
            '6.9.12-1-default',
            '6.10.1-1-default'
        ]

    def test_latest_version_wins_over_name_order(self, tmp_path):
        self._install(tmp_path, '6.9.12-1-default', 'boot/vmlinuz-6.9.12-1-default')
        self._install(tmp_path, '6.10.1-1-default', 'boot/vmlinuz-6.10.1-1-default')
        kernel = Kernel(str(tmp_path))
        assert kernel.get_kernel_versions() == [
            '6.10.1-1-default', '6.9.12-1-default'
        ]
        data = kernel.get_kernel()
        assert data.version == '6.10.1-1-default'
        assert data.filename == \
            f'{tmp_path}/boot/vmlinuz-6.10.1-1-default'

    def test_latest_version_wins_over_image_name(self, tmp_path):
        # Image is looked up before vmlinuz, still the later kernel
        # is used
        self._install(tmp_path, '6.4.0-1-default', 'boot/Image-6.4.0-1-default')
        self._install(tmp_path, '6.4.0-2-default', 'boot/vmlinuz-6.4.0-2-default')
        assert Kernel(str(tmp_path)).get_kernel().version == '6.4.0-2-default'

    def test_modules_dir_without_kernel_is_skipped(self, tmp_path):
        # a later modules directory without a kernel image, e.g left
        # behind by a removed kernel, does not change the version
        self._install(tmp_path, '6.4.0-1-default', 'vmlinuz')
        self._install(tmp_path, '6.4.0-9-default', '')
        data = Kernel(str(tmp_path)).get_kernel()
        assert data.version == '6.4.0-1-default'
        assert data.filename == \
            f'{tmp_path}/lib/modules/6.4.0-1-default/vmlinuz'

    def test_usrmerge_and_boot_in_root_path(self, tmp_path):
        # lib is a link to usr/lib, a version is listed once. The path
        # of the root tree does not affect the version
        root_dir = tmp_path / 'boot' / 'image-root'
        root_dir.mkdir(parents=True)
        self._install(root_dir, '6.4.0-1-default', 'vmlinuz', 'usr/lib/modules')
        self._install(root_dir, '6.4.0-2-default', 'vmlinuz', 'usr/lib/modules')
        (root_dir / 'lib').symlink_to('usr/lib')
        kernel = Kernel(str(root_dir))
        assert kernel.get_kernel_versions() == [
            '6.4.0-2-default', '6.4.0-1-default'
        ]
        assert kernel.get_kernel().version == '6.4.0-2-default'

    def test_get_version_in_name(self, tmp_path):
        self._install(tmp_path, '6.1', 'vmlinuz')
        self._install(tmp_path, '6.10', 'vmlinuz')
        kernel = Kernel(str(tmp_path))
        assert kernel.get_version_in_name('initramfs-6.10.img') == '6.10'
        assert kernel.get_version_in_name('initramfs-6.1.img') == '6.1'
        assert kernel.get_version_in_name('initramfs-5.0.img') is None
