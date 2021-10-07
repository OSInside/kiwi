import logging
from mock import (
    patch, call, Mock, MagicMock
)
from pytest import (
    raises, fixture
)

from kiwi.defaults import Defaults
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import KiwiBootLoaderTargetError
from kiwi.bootloader.config.base import BootLoaderConfigBase


class TestBootLoaderConfigBase:
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
        self.bootloader = BootLoaderConfigBase(
            self.state, 'root_dir'
        )

    def test_write(self):
        with raises(NotImplementedError):
            self.bootloader.write()

    def test_setup_disk_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_disk_image_config(
                'boot_uuid', 'root_uuid', 'hypervisor',
                'kernel', 'initrd', 'options'
            )

    def test_setup_install_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_install_image_config(
                'mbrid', 'hypervisor', 'kernel', 'initrd'
            )

    def test_setup_live_image_config(self):
        with raises(NotImplementedError):
            self.bootloader.setup_live_image_config(
                'mbrid', 'hypervisor', 'kernel', 'initrd'
            )

    def test_setup_disk_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_disk_boot_images('uuid')

    def test_setup_install_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_install_boot_images('mbrid')

    def test_setup_live_boot_images(self):
        with raises(NotImplementedError):
            self.bootloader.setup_live_boot_images('mbrid')

    def test_setup_sysconfig_bootloader(self):
        with raises(NotImplementedError):
            self.bootloader.setup_sysconfig_bootloader()

    @patch('kiwi.path.Path.create')
    def test_create_efi_path(self, mock_path):
        self.bootloader.create_efi_path()
        mock_path.assert_called_once_with('root_dir/boot/efi/EFI/BOOT')

    @patch('kiwi.path.Path.create')
    def test_create_efi_path_with_prefix(self, mock_path):
        self.bootloader.create_efi_path('')
        mock_path.assert_called_once_with('root_dir/EFI/BOOT')

    def test_get_boot_theme(self):
        assert self.bootloader.get_boot_theme() == 'openSUSE'

    def test_get_boot_timeout_seconds_default_applies(self):
        assert self.bootloader.get_boot_timeout_seconds() == 10

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_boot_timeout_seconds(self, mock_get_bootloader):
        bootloader = Mock()
        bootloader.get_timeout.return_value = 0
        mock_get_bootloader.return_value = [bootloader]
        assert self.bootloader.get_boot_timeout_seconds() == 0

    @patch('kiwi.xml_parse.type_.get_installprovidefailsafe')
    def test_failsafe_boot_entry_requested(
        self, mock_installprovidefailsafe
    ):
        mock_installprovidefailsafe.return_value = True
        assert self.bootloader.failsafe_boot_entry_requested() is True
        mock_installprovidefailsafe.return_value = False
        assert self.bootloader.failsafe_boot_entry_requested() is False

    def test_get_boot_cmdline(self):
        assert self.bootloader.get_boot_cmdline() == 'splash'

    @patch('kiwi.xml_parse.type_.get_kernelcmdline')
    def test_get_boot_cmdline_custom_root(self, mock_cmdline):
        mock_cmdline.return_value = 'root=/dev/myroot'
        assert self.bootloader.get_boot_cmdline() == 'root=/dev/myroot'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    @patch('kiwi.bootloader.config.base.BlockID')
    def test_get_boot_cmdline_initrd_system_is_dracut(
        self, mock_BlockID, mock_initrd
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'uuid'
        mock_BlockID.return_value = block_operation
        mock_initrd.return_value = 'dracut'
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=UUID=uuid'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    @patch('kiwi.bootloader.config.base.BlockID')
    def test_get_boot_cmdline_initrd_system_is_dracut_with_overlay(
        self, mock_BlockID, mock_initrd
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'uuid'
        mock_BlockID.return_value = block_operation
        mock_initrd.return_value = 'dracut'
        self.state.build_type.get_overlayroot = Mock(
            return_value=True
        )
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=overlay:UUID=uuid'

    @patch('kiwi.xml_parse.type_.get_installboot')
    def test_get_install_image_boot_default(self, mock_installboot):
        mock_installboot.return_value = None
        assert self.bootloader.get_install_image_boot_default() == '0'
        assert self.bootloader.get_install_image_boot_default('isolinux') == \
            'Boot_from_Hard_Disk'
        mock_installboot.return_value = 'failsafe-install'
        assert self.bootloader.get_install_image_boot_default() == '2'
        assert self.bootloader.get_install_image_boot_default('isolinux') == \
            'Failsafe_--_Install_Bob'
        mock_installboot.return_value = 'install'
        assert self.bootloader.get_install_image_boot_default() == '1'
        assert self.bootloader.get_install_image_boot_default('isolinux') == \
            'Install_Bob'

    @patch('kiwi.xml_parse.type_.get_installboot')
    @patch('kiwi.xml_parse.type_.get_installprovidefailsafe')
    def test_get_install_image_boot_default_failsafe_but_no_failsafe_entry(
        self, mock_installprovidefailsafe, mock_installboot
    ):
        mock_installprovidefailsafe.return_value = False
        mock_installboot.return_value = 'failsafe-install'
        with self._caplog.at_level(logging.WARNING):
            assert self.bootloader.get_install_image_boot_default() == '1'
            assert 'Failsafe install requested but failsafe '
            'menu entry is disabled' in self._caplog.text
            assert 'Switching to standard install' in self._caplog.text

    def test_get_boot_path_raises(self):
        with raises(KiwiBootLoaderTargetError):
            self.bootloader.get_boot_path('foo')

    @patch('kiwi.bootloader.config.base.DiskSetup')
    @patch('kiwi.xml_parse.type_.get_filesystem')
    @patch('kiwi.xml_state.XMLState.get_volumes')
    def test_get_boot_path_btrfs_boot_is_a_volume_error(
        self, mock_volumes, mock_fs, mock_disk_setup
    ):
        volume = Mock()
        volume.name = 'boot'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        disk_setup = Mock()
        disk_setup.need_boot_partition = Mock(
            return_value=False
        )
        mock_disk_setup.return_value = disk_setup
        with raises(KiwiBootLoaderTargetError):
            self.bootloader.get_boot_path()

    @patch('kiwi.bootloader.config.base.DiskSetup')
    @patch('kiwi.xml_parse.type_.get_filesystem')
    @patch('kiwi.xml_parse.type_.get_btrfs_root_is_snapshot')
    @patch('kiwi.xml_state.XMLState.get_volumes')
    def test_get_boot_path_btrfs_no_snapshot(
        self, mock_volumes, mock_snapshot, mock_fs, mock_disk_setup
    ):
        volume = Mock()
        volume.name = 'some-volume'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        mock_snapshot.return_value = False
        disk_setup = Mock()
        disk_setup.need_boot_partition = Mock(
            return_value=False
        )
        mock_disk_setup.return_value = disk_setup
        assert self.bootloader.get_boot_path() == \
            '/boot'

    @patch('kiwi.bootloader.config.base.DiskSetup')
    @patch('kiwi.xml_parse.type_.get_filesystem')
    @patch('kiwi.xml_parse.type_.get_btrfs_root_is_snapshot')
    @patch('kiwi.xml_state.XMLState.get_volumes')
    def test_get_boot_path_btrfs_snapshot(
        self, mock_volumes, mock_snapshot, mock_fs, mock_disk_setup
    ):
        volume = Mock()
        volume.name = 'some-volume'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        mock_snapshot.return_value = True
        disk_setup = Mock()
        disk_setup.need_boot_partition = Mock(
            return_value=False
        )
        mock_disk_setup.return_value = disk_setup
        assert self.bootloader.get_boot_path() == \
            '/boot'

    def test_get_boot_path_iso(self):
        assert self.bootloader.get_boot_path(target='iso') == \
            '/boot/x86_64/loader'

    def test_quote_title(self):
        assert self.bootloader.quote_title('aaa bbb [foo]') == 'aaa_bbb_(foo)'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_title() == \
            'LimeJeOS [ OEM ]'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title_plain(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_title(plain=True) == \
            'LimeJeOS'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title_by_displayname(self, mock_displayname):
        mock_displayname.return_value = 'my_title'
        assert self.bootloader.get_menu_entry_title() == \
            'my_title'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_install_title(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_install_title() == \
            'LimeJeOS'

    @patch('kiwi.xml_parse.type_.get_vga')
    def test_get_gfxmode_default(self, mock_get_vga):
        mock_get_vga.return_value = None
        assert self.bootloader.get_gfxmode('isolinux') == '800 600'
        assert self.bootloader.get_gfxmode('grub2') == 'auto'

    @patch('kiwi.xml_parse.type_.get_vga')
    def test_get_gfxmode(self, mock_get_vga):
        mock_get_vga.return_value = '0x318'
        assert self.bootloader.get_gfxmode('isolinux') == '1024 768'
        assert self.bootloader.get_gfxmode('grub2') == '1024x768'

    @patch('kiwi.xml_parse.type_.get_vga')
    def test_get_gfxmode_other_loader(self, mock_get_vga):
        mock_get_vga.return_value = '0x318'
        assert self.bootloader.get_gfxmode('some-loader') == \
            mock_get_vga.return_value

    @patch('kiwi.bootloader.config.base.MountManager')
    def test_mount_system_s390(self, mock_MountManager):
        tmp_mount = MagicMock()
        proc_mount = MagicMock()
        dev_mount = MagicMock()
        root_mount = MagicMock()
        root_mount.mountpoint = 'root_mount_point'
        root_mount.device = 'rootdev'
        boot_mount = MagicMock()
        boot_mount.device = 'bootdev'

        mount_managers = [
            proc_mount, dev_mount, tmp_mount, boot_mount, root_mount
        ]

        def mount_managers_effect(**args):
            return mount_managers.pop()

        self.bootloader.arch = 's390x'

        mock_MountManager.side_effect = mount_managers_effect
        self.bootloader._mount_system(
            'rootdev', 'bootdev'
        )
        assert mock_MountManager.call_args_list == [
            call(device='rootdev'),
            call(device='bootdev', mountpoint='root_mount_point/boot/zipl'),
            call(device='/dev', mountpoint='root_mount_point/dev'),
            call(device='/proc', mountpoint='root_mount_point/proc')
        ]

    @patch('kiwi.bootloader.config.base.MountManager')
    def test_mount_system(self, mock_MountManager):
        tmp_mount = MagicMock()
        proc_mount = MagicMock()
        dev_mount = MagicMock()
        root_mount = MagicMock()
        root_mount.mountpoint = 'root_mount_point'
        root_mount.device = 'rootdev'
        boot_mount = MagicMock()
        boot_mount.device = 'bootdev'
        efi_mount = MagicMock()
        efi_mount.device = 'efidev'
        volume_mount = MagicMock()

        mount_managers = [
            proc_mount, dev_mount, tmp_mount, volume_mount,
            efi_mount, boot_mount, root_mount
        ]

        def mount_managers_effect(**args):
            return mount_managers.pop()

        mock_MountManager.side_effect = mount_managers_effect
        self.bootloader.root_filesystem_is_overlay = True
        self.bootloader._mount_system(
            'rootdev', 'bootdev', 'efidev', {
                'boot/grub2': {
                    'volume_options': 'subvol=@/boot/grub2',
                    'volume_device': 'device'
                }
            }
        )
        assert mock_MountManager.call_args_list == [
            call(device='rootdev'),
            call(device='bootdev', mountpoint='root_mount_point/boot'),
            call(device='efidev', mountpoint='root_mount_point/boot/efi'),
            call(device='device', mountpoint='root_mount_point/boot/grub2'),
            call(device='/tmp', mountpoint='root_mount_point/tmp'),
            call(device='/dev', mountpoint='root_mount_point/dev'),
            call(device='/proc', mountpoint='root_mount_point/proc')
        ]
        root_mount.mount.assert_called_once_with()
        boot_mount.mount.assert_called_once_with()
        efi_mount.mount.assert_called_once_with()
        volume_mount.mount.assert_called_once_with(
            options=['subvol=@/boot/grub2']
        )
        proc_mount.bind_mount.assert_called_once_with()
        dev_mount.bind_mount.assert_called_once_with()

        del self.bootloader

        volume_mount.umount.assert_called_once_with()
        tmp_mount.umount.assert_called_once_with()
        dev_mount.umount.assert_called_once_with()
        proc_mount.umount.assert_called_once_with()
        efi_mount.umount.assert_called_once_with()
        boot_mount.umount.assert_called_once_with()
        root_mount.umount.assert_called_once_with()

    def test_write_meta_data(self):
        # just pass
        self.bootloader.write_meta_data()
