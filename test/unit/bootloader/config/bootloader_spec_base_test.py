from mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.defaults import Defaults
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase


class TestBootLoaderSpecBase:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
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

    def setup_method(self, cls):
        self.setup()

    @patch.object(BootLoaderSpecBase, 'setup_loader')
    @patch.object(BootLoaderSpecBase, 'set_loader_entry')
    def test_setup_disk_image_config(
        self, mock_setup_loader, mock_set_loader_entry
    ):
        self.bootloader.get_boot_cmdline = Mock(return_value='')
        self.bootloader.setup_disk_image_config(
            'boot_uuid', 'root_uuid', 'hypervisor',
            'kernel', 'initrd', boot_options={
                'root_device': 'rootdev', 'boot_device': 'bootdev'
            }
        )
        mock_setup_loader.assert_called_once_with('disk')
        mock_set_loader_entry.assert_called_once_with('disk')

    @patch.object(BootLoaderSpecBase, 'setup_loader')
    @patch.object(BootLoaderSpecBase, 'set_loader_entry')
    def test_setup_install_image_config(
        self, mock_setup_loader, mock_set_loader_entry
    ):
        self.bootloader.setup_install_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )
        mock_setup_loader.assert_called_once_with('install(iso)')
        mock_set_loader_entry.assert_called_once_with('install(iso)')

    @patch.object(BootLoaderSpecBase, 'setup_loader')
    @patch.object(BootLoaderSpecBase, 'set_loader_entry')
    def test_setup_live_image_config(
        self, mock_setup_loader, mock_set_loader_entry
    ):
        self.bootloader.setup_live_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )
        mock_setup_loader.assert_called_once_with('live(iso)')
        mock_set_loader_entry.assert_called_once_with('live(iso)')

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
            self.bootloader.set_loader_entry('target')

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
