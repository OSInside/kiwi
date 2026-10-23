from unittest.mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.defaults import Defaults
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase
from kiwi.exceptions import KiwiKernelLookupError


class TestBootLoaderSpecBase:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def setup(self, mock_FirmWare):
        Defaults.set_platform_name('x86_64')
        description = XMLDescription(
            '../data/example_config.xml'
        )
        self.state = XMLState(
            description.load()
        )
        self.bootloader = BootLoaderSpecBase(
            self.state, 'root_dir'
        )

    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def setup_method(self, cls, mock_FirmWare):
        self.setup()

    @patch.object(BootLoaderSpecBase, 'setup_loader')
    def test_setup_disk_image_config(self, mock_setup_loader):
        self.bootloader.get_boot_cmdline = Mock(return_value='')
        self.bootloader.setup_disk_image_config(
            'boot_uuid', 'root_uuid', 'hypervisor',
            'kernel', 'initrd', boot_options={
                'root_device': 'rootdev', 'boot_device': 'bootdev'
            }
        )
        mock_setup_loader.assert_called_once_with('disk')

    def test_setup_install_image_config(self):
        # just pass
        self.bootloader.setup_install_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )

    def test_setup_live_image_config(self):
        # just pass
        self.bootloader.setup_live_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )

    @patch.object(BootLoaderSpecBase, 'create_loader_image')
    def test_setup_disk_boot_images(self, mock_create_loader_image):
        self.bootloader.setup_disk_boot_images('uuid')
        mock_create_loader_image.assert_called_once_with('disk')

    @patch.object(BootLoaderSpecBase, 'create_loader_image')
    def test_setup_install_boot_images(self, mock_create_loader_image):
        self.bootloader.setup_install_boot_images('mbrid')
        mock_create_loader_image.assert_called_once_with('install(iso)')

    @patch.object(BootLoaderSpecBase, 'create_loader_image')
    def test_setup_live_boot_images(self, mock_create_loader_image):
        self.bootloader.setup_live_boot_images('mbrid')
        mock_create_loader_image.assert_called_once_with('live(iso)')

    def test_setup_loader(self):
        with raises(NotImplementedError):
            self.bootloader.setup_loader('target')

    def test_set_loader_entry(self):
        with raises(NotImplementedError):
            self.bootloader.set_loader_entry('root_dir', 'target')

    def test_create_loader_image(self):
        with raises(NotImplementedError):
            self.bootloader.create_loader_image('target')

    def test_write(self):
        # just pass
        self.bootloader.write()

    def test_setup_sysconfig_bootloader(self):
        # just pass
        self.bootloader.setup_sysconfig_bootloader()

    def test_write_meta_data(self):
        # just pass
        self.bootloader.write_meta_data()

    def _setup_root_tree(self, root_dir, kernel_versions, entries):
        for kernel_version in kernel_versions:
            modules_dir = root_dir / 'lib' / 'modules' / kernel_version
            modules_dir.mkdir(parents=True)
            (modules_dir / 'vmlinuz').touch()
        entries_dir = root_dir / self.bootloader.entries_dir.lstrip('/')
        entries_dir.mkdir(parents=True)
        for entry in entries:
            (entries_dir / entry).touch()
        self.bootloader.root_dir = str(root_dir)

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    def test_get_entry_name_kernel_lookup_raises(
        self, mock_OsRelease, tmp_path
    ):
        self._setup_root_tree(tmp_path, [], [])
        with raises(KiwiKernelLookupError):
            self.bootloader.get_entry_name()

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    def test_get_entry_name_kiwi_policy(self, mock_OsRelease, tmp_path):
        # the entry belongs to the latest kernel, not to the first
        # one by name
        self._setup_root_tree(
            tmp_path, ['5.3.18-59.10-default', '5.3.18-59.9-default'], []
        )
        os_release = Mock()
        os_release.get.return_value = 'opensuse-leap'
        mock_OsRelease.return_value = os_release
        assert self.bootloader.get_entry_name() == \
            'opensuse-leap-5.3.18-59.10-default.conf'

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    def test_get_entry_name_os_policy(self, mock_OsRelease, tmp_path):
        self._setup_root_tree(
            tmp_path, ['5.3.18-59.10-default', '5.3.18-59.9-default'], [
                'bc8499a-5.3.18-59.9-default.conf',
                'bc8499a-5.3.18-59.10-default.conf'
            ]
        )
        assert self.bootloader.get_entry_name() == \
            'bc8499a-5.3.18-59.10-default.conf'

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    def test_get_entry_name_os_policy_of_other_kernel(
        self, mock_OsRelease, tmp_path
    ):
        # only the entry of an earlier kernel exists, its naming
        # policy is applied to the latest kernel
        self._setup_root_tree(
            tmp_path, ['5.3.18-59.10-default', '5.3.18-59.9-default'], [
                'bc8499a-5.3.18-59.9-default.conf'
            ]
        )
        assert self.bootloader.get_entry_name() == \
            'bc8499a-5.3.18-59.10-default.conf'

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    def test_get_entry_name_os_policy_without_version(
        self, mock_OsRelease, tmp_path
    ):
        self._setup_root_tree(
            tmp_path, ['5.3.18-59.10-default'], ['default.conf']
        )
        assert self.bootloader.get_entry_name() == 'default.conf'
