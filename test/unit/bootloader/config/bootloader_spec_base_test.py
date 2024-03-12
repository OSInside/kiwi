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

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    @patch('kiwi.bootloader.config.bootloader_spec_base.glob.iglob')
    def test_get_entry_name_kernel_lookup_raises(
        self, mock_iglob, mock_OsRelease
    ):
        mock_iglob.return_value = None
        with raises(KiwiKernelLookupError):
            self.bootloader.get_entry_name()

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    @patch('kiwi.bootloader.config.bootloader_spec_base.glob.iglob')
    def test_get_entry_name_kiwi_policy(
        self, mock_iglob, mock_OsRelease
    ):
        glob_return_value = [
            ['/lib/modules/5.3.18-59.10-default'],
            []
        ]

        def get_glob(args):
            return glob_return_value.pop(0)

        mock_iglob.side_effect = get_glob
        os_release = Mock()
        os_release.get.return_value = 'opensuse-leap'
        mock_OsRelease.return_value = os_release
        assert self.bootloader.get_entry_name() == \
            'opensuse-leap-5.3.18-59.10-default.conf'

    @patch('kiwi.bootloader.config.bootloader_spec_base.OsRelease')
    @patch('kiwi.bootloader.config.bootloader_spec_base.glob.iglob')
    def test_get_entry_name_os_policy(
        self, mock_iglob, mock_OsRelease
    ):
        glob_return_value = [
            ['/lib/modules/5.3.18-59.10-default'],
            ['/boot/loader/entries/bc8499a-5.3.18-59.10-default.conf']
        ]

        def get_glob(args):
            return glob_return_value.pop(0)

        mock_iglob.side_effect = get_glob
        assert self.bootloader.get_entry_name() == \
            'bc8499a-5.3.18-59.10-default.conf'
