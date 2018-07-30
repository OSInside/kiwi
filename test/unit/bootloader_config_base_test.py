from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import KiwiBootLoaderTargetError
from kiwi.bootloader.config.base import BootLoaderConfigBase


class TestBootLoaderConfigBase(object):
    def setup(self):
        description = XMLDescription(
            '../data/example_config.xml'
        )
        self.state = XMLState(
            description.load()
        )
        self.bootloader = BootLoaderConfigBase(
            self.state, 'root_dir'
        )

    @raises(NotImplementedError)
    def test_write(self):
        self.bootloader.write()

    @raises(NotImplementedError)
    def test_setup_disk_image_config(self):
        self.bootloader.setup_disk_image_config(
            'boot_uuid', 'root_uuid', 'hypervisor',
            'kernel', 'initrd', 'options'
        )

    @raises(NotImplementedError)
    def test_setup_install_image_config(self):
        self.bootloader.setup_install_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )

    @raises(NotImplementedError)
    def test_setup_live_image_config(self):
        self.bootloader.setup_live_image_config(
            'mbrid', 'hypervisor', 'kernel', 'initrd'
        )

    @raises(NotImplementedError)
    def test_setup_disk_boot_images(self):
        self.bootloader.setup_disk_boot_images('uuid')

    @raises(NotImplementedError)
    def test_setup_install_boot_images(self):
        self.bootloader.setup_install_boot_images('mbrid')

    @raises(NotImplementedError)
    def test_setup_live_boot_images(self):
        self.bootloader.setup_live_boot_images('mbrid')

    @raises(NotImplementedError)
    def test_setup_sysconfig_bootloader(self):
        self.bootloader.setup_sysconfig_bootloader()

    @patch('kiwi.path.Path.create')
    def test_create_efi_path(self, mock_path):
        self.bootloader.create_efi_path()
        mock_path.assert_called_once_with('root_dir/boot/efi/EFI/BOOT')

    @patch('kiwi.path.Path.create')
    def test_create_efi_path_with_prefix(self, mock_path):
        self.bootloader.create_efi_path('')
        mock_path.assert_called_once_with('root_dir//EFI/BOOT')

    def test_get_boot_theme(self):
        assert self.bootloader.get_boot_theme() == 'openSUSE'

    def test_get_boot_timeout_seconds_default_applies(self):
        assert self.bootloader.get_boot_timeout_seconds() == 10

    @patch('kiwi.xml_parse.type_.get_boottimeout')
    def test_get_boot_timeout_seconds(self, mock_get_boottimeout):
        mock_get_boottimeout.return_value = 0
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

    @patch('kiwi.xml_parse.type_.get_firmware')
    def test_get_boot_cmdline_firmware_ec2(self, mock_firmware):
        mock_firmware.return_value = 'ec2'
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=UUID=uuid rw'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    def test_get_boot_cmdline_initrd_system_is_dracut(self, mock_initrd):
        mock_initrd.return_value = 'dracut'
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=UUID=uuid rw'

    @patch('kiwi.xml_parse.type_.get_initrd_system')
    def test_get_boot_cmdline_initrd_system_is_dracut_with_overlay(
        self, mock_initrd
    ):
        mock_initrd.return_value = 'dracut'
        self.state.build_type.get_overlayroot = mock.Mock(
            return_value=True
        )
        assert self.bootloader.get_boot_cmdline('uuid') == \
            'splash root=overlay:UUID=uuid'

    @patch('kiwi.xml_parse.type_.get_firmware')
    @patch('kiwi.logger.log.warning')
    def test_get_boot_cmdline_firmware_ec2_no_uuid(
        self, mock_log_warn, mock_firmware
    ):
        mock_firmware.return_value = 'ec2'
        self.bootloader.get_boot_cmdline()
        assert mock_log_warn.called

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
    @patch('kiwi.logger.log.warning')
    def test_get_install_image_boot_default_failsafe_but_no_failsafe_entry(
        self, mock_warn, mock_installprovidefailsafe, mock_installboot
    ):
        mock_installprovidefailsafe.return_value = False
        mock_installboot.return_value = 'failsafe-install'
        assert self.bootloader.get_install_image_boot_default() == '1'
        assert mock_warn.call_args_list == [
            call(
                'Failsafe install requested but failsafe menu entry is disabled'
            ),
            call('Switching to standard install')
        ]

    @raises(KiwiBootLoaderTargetError)
    def test_get_boot_path_raises(self):
        self.bootloader.get_boot_path('foo')

    @raises(KiwiBootLoaderTargetError)
    @patch('kiwi.bootloader.config.base.DiskSetup')
    @patch('kiwi.xml_parse.type_.get_filesystem')
    @patch('kiwi.xml_state.XMLState.get_volumes')
    def test_get_boot_path_btrfs_boot_is_a_volume_error(
        self, mock_volumes, mock_fs, mock_disk_setup
    ):
        volume = mock.Mock()
        volume.name = 'boot'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        disk_setup = mock.Mock()
        disk_setup.need_boot_partition = mock.Mock(
            return_value=False
        )
        mock_disk_setup.return_value = disk_setup
        self.bootloader.get_boot_path()

    @patch('kiwi.bootloader.config.base.DiskSetup')
    @patch('kiwi.xml_parse.type_.get_filesystem')
    @patch('kiwi.xml_parse.type_.get_btrfs_root_is_snapshot')
    @patch('kiwi.xml_state.XMLState.get_volumes')
    def test_get_boot_path_btrfs_no_snapshot(
        self, mock_volumes, mock_snapshot, mock_fs, mock_disk_setup
    ):
        volume = mock.Mock()
        volume.name = 'some-volume'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        mock_snapshot.return_value = False
        disk_setup = mock.Mock()
        disk_setup.need_boot_partition = mock.Mock(
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
        volume = mock.Mock()
        volume.name = 'some-volume'
        mock_volumes.return_value = [volume]
        mock_fs.return_value = 'btrfs'
        mock_snapshot.return_value = True
        disk_setup = mock.Mock()
        disk_setup.need_boot_partition = mock.Mock(
            return_value=False
        )
        mock_disk_setup.return_value = disk_setup
        assert self.bootloader.get_boot_path() == \
            '/boot'

    def test_quote_title(self):
        assert self.bootloader.quote_title('aaa bbb [foo]') == 'aaa_bbb_(foo)'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_title() == \
            'LimeJeOS-openSUSE-13.2 [ OEM ]'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title_plain(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_title(plain=True) == \
            'LimeJeOS-openSUSE-13.2'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_title_by_displayname(self, mock_displayname):
        mock_displayname.return_value = 'my_title'
        assert self.bootloader.get_menu_entry_title() == \
            'my_title'

    @patch('kiwi.xml_parse.image.get_displayname')
    def test_get_menu_entry_install_title(self, mock_displayname):
        mock_displayname.return_value = None
        assert self.bootloader.get_menu_entry_install_title() == \
            'LimeJeOS-openSUSE-13.2'

    @patch('kiwi.xml_parse.type_.get_vga')
    def test_get_gfxmode_default(self, mock_get_vga):
        mock_get_vga.return_value = None
        assert self.bootloader.get_gfxmode('isolinux') == '800 600'
        assert self.bootloader.get_gfxmode('grub2') == '800x600'

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
