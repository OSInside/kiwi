import logging
from unittest.mock import (
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


class BootLoaderConfigTestImpl(BootLoaderConfigBase):
    def setup_install_image_config(self, mbrid, hypervisor, kernel, initrd):
        return super().setup_install_image_config(mbrid, hypervisor, kernel, initrd)

    def setup_disk_image_config(
            self, boot_uuid=None, root_uuid=None, hypervisor=None, kernel=None,
            initrd=None, boot_options=...):
        return super().setup_disk_image_config(
            boot_uuid, root_uuid, hypervisor, kernel, initrd, boot_options
        )

    def write(self):
        return super().write()

    def setup_live_image_config(self, mbrid, hypervisor, kernel, initrd):
        return super().setup_live_image_config(
            mbrid, hypervisor, kernel, initrd
        )

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        return super().setup_install_boot_images(mbrid, lookup_path)

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        return super().setup_disk_boot_images(boot_uuid, lookup_path)

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        return super().setup_live_boot_images(mbrid, lookup_path)

    def setup_sysconfig_bootloader(self):
        return super().setup_sysconfig_bootloader()


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
        self.bootloader = BootLoaderConfigTestImpl(
            self.state, 'root_dir'
        )

    def setup_method(self, cls):
        self.setup()

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
        assert self.bootloader.get_boot_cmdline(None) == 'splash'

    @patch('kiwi.xml_parse.type_.get_kernelcmdline')
    def test_get_boot_cmdline_custom_root(self, mock_cmdline):
        mock_cmdline.return_value = 'root=/dev/myroot'
        with self._caplog.at_level(logging.WARNING):
            assert self.bootloader.get_boot_cmdline(
                '/dev/myroot'
            ) == 'root=/dev/myroot'
            assert 'Kernel root device explicitly set via kernelcmdline' \
                in self._caplog.text

    @patch('kiwi.xml_parse.type_.get_kernelcmdline')
    @patch('kiwi.bootloader.config.base.BlockID')
    def test_get_boot_cmdline_custom_root_overlay_write(
        self, mock_BlockID, mock_cmdline
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'mock'
        mock_BlockID.return_value = block_operation
        mock_cmdline.return_value = 'rd.root.overlay.write=/dev/myrw'
        self.state.build_type.get_overlayroot = Mock(
            return_value=True
        )
        with self._caplog.at_level(logging.WARNING):
            assert self.bootloader.get_boot_cmdline(
                '/dev/myroot'
            ) == 'rd.root.overlay.write=/dev/myrw root=overlay:PARTUUID=mock'
            assert 'Overlay write device explicitly set via kernelcmdline' \
                in self._caplog.text

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
    def test_get_boot_cmdline_initrd_system_is_dracut_partuuid(
        self, mock_BlockID, mock_initrd
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'uuid'
        mock_BlockID.return_value = block_operation
        mock_initrd.return_value = 'dracut'
        self.bootloader.xml_state.build_type.set_devicepersistency(
            'by-partuuid'
        )
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=PARTUUID=uuid'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    @patch('kiwi.bootloader.config.base.BlockID')
    def test_get_boot_cmdline_initrd_system_is_dracut_label(
        self, mock_BlockID, mock_initrd
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'label'
        mock_BlockID.return_value = block_operation
        mock_initrd.return_value = 'dracut'
        self.bootloader.xml_state.build_type.set_devicepersistency(
            'by-label'
        )
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=LABEL=label'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    @patch('kiwi.bootloader.config.base.BlockID')
    def test_get_boot_cmdline_initrd_system_is_dracut_with_overlay(
        self, mock_BlockID, mock_initrd
    ):
        block_operation = Mock()
        block_operation.get_blkid.return_value = 'mock'
        mock_BlockID.return_value = block_operation
        mock_initrd.return_value = 'dracut'
        self.state.build_type.get_overlayroot = Mock(
            return_value=True
        )
        assert self.bootloader.get_boot_cmdline('/dev/ro', '/dev/rw') == \
            'splash rd.root.overlay.write=/dev/disk/by-uuid/mock root=overlay:PARTUUID=mock'

    @patch('kiwi.xml_parse.type_.get_installboot')
    def test_get_install_image_boot_default(self, mock_installboot):
        mock_installboot.return_value = None
        assert self.bootloader.get_install_image_boot_default() == '0'
        mock_installboot.return_value = 'failsafe-install'
        assert self.bootloader.get_install_image_boot_default() == '2'
        mock_installboot.return_value = 'install'
        assert self.bootloader.get_install_image_boot_default() == '1'

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
        assert self.bootloader.get_gfxmode('grub2') == 'auto'

    @patch('kiwi.xml_parse.type_.get_vga')
    def test_get_gfxmode(self, mock_get_vga):
        mock_get_vga.return_value = '0x318'
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
        sys_mount = MagicMock()
        dev_mount = MagicMock()
        root_mount = MagicMock()
        root_mount.mountpoint = 'root_mount_point'
        root_mount.device = 'rootdev'
        boot_mount = MagicMock()
        boot_mount.device = 'bootdev'

        mount_managers = [
            proc_mount, sys_mount, dev_mount, tmp_mount, boot_mount, root_mount
        ]

        def mount_managers_effect(**args):
            return mount_managers.pop()

        self.bootloader.arch = 's390x'
        self.bootloader.bootloader = 'grub2_s390x_emu'

        mock_MountManager.side_effect = mount_managers_effect
        self.bootloader._mount_system(
            'rootdev', 'bootdev'
        )
        assert mock_MountManager.call_args_list == [
            call(device='rootdev'),
            call(device='bootdev', mountpoint='root_mount_point/boot/zipl'),
            call(device='/dev', mountpoint='root_mount_point/dev'),
            call(device='/proc', mountpoint='root_mount_point/proc'),
            call(device='/sys', mountpoint='root_mount_point/sys')
        ]

    @patch('kiwi.bootloader.config.base.MountManager')
    @patch('kiwi.bootloader.config.base.SystemSetup')
    def test_mount_system(self, mock_SystemSetup, mock_MountManager):
        setup = Mock()
        mock_SystemSetup.return_value = setup
        tmp_mount = MagicMock()
        proc_mount = MagicMock()
        sys_mount = MagicMock()
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
            proc_mount, sys_mount, dev_mount, tmp_mount, volume_mount,
            efi_mount, boot_mount, root_mount
        ]

        def mount_managers_effect(**args):
            return mount_managers.pop()

        mock_MountManager.side_effect = mount_managers_effect

        with BootLoaderConfigTestImpl(self.state, 'root_dir') as bootloader:
            bootloader.root_filesystem_is_overlay = True
            bootloader._mount_system(
                'rootdev', 'bootdev', 'efidev', {
                    'boot/grub2': {
                        'volume_options': 'subvol=@/boot/grub2',
                        'volume_device': 'device'
                    }
                }, root_volume_name='root'
            )
            assert mock_MountManager.call_args_list == [
                call(device='rootdev'),
                call(device='bootdev', mountpoint='root_mount_point/boot'),
                call(device='efidev', mountpoint='root_mount_point/boot/efi'),
                call(device='device', mountpoint='root_mount_point/boot/grub2'),
                call(device='/tmp', mountpoint='root_mount_point/tmp'),
                call(device='/dev', mountpoint='root_mount_point/dev'),
                call(device='/proc', mountpoint='root_mount_point/proc'),
                call(device='/sys', mountpoint='root_mount_point/sys')
            ]
            root_mount.mount.assert_called_once_with(
                options=['subvol=root']
            )
            boot_mount.mount.assert_called_once_with()
            efi_mount.mount.assert_called_once_with()
            volume_mount.mount.assert_called_once_with(
                options=['subvol=@/boot/grub2']
            )
            proc_mount.bind_mount.assert_called_once_with()
            sys_mount.bind_mount.assert_called_once_with()
            dev_mount.bind_mount.assert_called_once_with()

        setup.setup_selinux_file_contexts.assert_called_once_with()

        volume_mount.umount.assert_called_once_with()
        tmp_mount.umount.assert_called_once_with()
        dev_mount.umount.assert_called_once_with()
        proc_mount.umount.assert_called_once_with()
        sys_mount.umount.assert_called_once_with()
        efi_mount.umount.assert_called_once_with()
        boot_mount.umount.assert_called_once_with()
        root_mount.umount.assert_called_once_with()

    def test_write_meta_data(self):
        # just pass
        self.bootloader.write_meta_data()
