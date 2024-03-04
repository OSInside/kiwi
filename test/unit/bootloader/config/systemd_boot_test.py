import io
from pytest import raises
from unittest.mock import (
    Mock, patch, call, MagicMock
)
from kiwi.bootloader.config.systemd_boot import BootLoaderSystemdBoot

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError,
    KiwiKernelLookupError
)


class TestBootLoaderSystemdBoot:
    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def setup(self, mock_FirmWare):
        self.state = Mock()
        self.state.xml_data.get_name.return_value = 'image-name'
        self.state.get_image_version.return_value = 'image-version'
        self.state.build_type.get_efifatimagesize.return_value = None
        self.bootloader = BootLoaderSystemdBoot(self.state, 'root_dir')
        self.bootloader.custom_args['kernel'] = None
        self.bootloader.custom_args['initrd'] = None
        self.bootloader.custom_args['boot_options'] = {}
        self.bootloader.root_mount = Mock(
            mountpoint='system_root_mount'
        )
        self.bootloader._mount_system = Mock()
        self.bootloader.create_efi_path = Mock()
        self.bootloader.get_boot_path = Mock(
            return_value='bootpath'
        )
        self.bootloader.get_menu_entry_title = Mock(
            return_value='title'
        )

    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def setup_method(self, cls, mock_FirmWare):
        self.setup()

    def test_setup_loader_raises_invalid_target(self):
        with raises(KiwiBootLoaderTargetError):
            self.bootloader.setup_loader('iso')

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.systemd_boot.OsRelease')
    @patch('kiwi.bootloader.config.systemd_boot.glob.iglob')
    @patch('kiwi.bootloader.config.systemd_boot.BootImageBase.get_boot_names')
    @patch('kiwi.bootloader.config.systemd_boot.Path.wipe')
    @patch('kiwi.bootloader.config.systemd_boot.Path.create')
    @patch('kiwi.bootloader.config.systemd_boot.Command.run')
    @patch('kiwi.bootloader.config.systemd_boot.BootLoaderTemplateSystemdBoot')
    @patch.object(BootLoaderSystemdBoot, '_write_config_file')
    @patch.object(BootLoaderSystemdBoot, '_get_template_parameters')
    @patch.object(BootLoaderSystemdBoot, '_write_kernel_cmdline_file')
    def test_setup_loader(
        self, mock_write_kernel_cmdline_file,
        mock_get_template_parameters, mock_write_config_file,
        mock_BootLoaderTemplateSystemdBoot, mock_Command_run,
        mock_Path_create, mock_Path_wipe, mock_BootImageBase_get_boot_names,
        mock_iglob,
        mock_OsRelease,
        mock_os_path_exists
    ):
        mock_iglob.return_value = ['/lib/modules/5.3.18-59.10-default']
        os_release = Mock()
        os_release.get.return_value = 'opensuse-leap'
        mock_OsRelease.return_value = os_release
        kernel_info = Mock()
        kernel_info.kernel_version = 'kernel-version'
        kernel_info.kernel_filename = 'kernel-filename'
        kernel_info.initrd_name = 'initrd-name'
        mock_os_path_exists.return_value = True
        mock_BootImageBase_get_boot_names.return_value = kernel_info
        self.bootloader.setup_loader('disk')
        assert mock_write_config_file.call_args_list == [
            call(
                mock_BootLoaderTemplateSystemdBoot.
                return_value.get_loader_template.return_value,
                'system_root_mount/boot/efi/loader/loader.conf',
                mock_get_template_parameters.return_value
            ),
            call(
                mock_BootLoaderTemplateSystemdBoot.
                return_value.get_entry_template.return_value,
                'system_root_mount/boot/efi/loader/entries/'
                'opensuse-leap-5.3.18-59.10-default.conf',
                mock_get_template_parameters.return_value
            )
        ]

        assert self.bootloader._mount_system.called
        mock_write_kernel_cmdline_file.assert_called_once_with(
            'system_root_mount'
        )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', 'system_root_mount',
                    'bootctl', 'install',
                    '--esp-path=/boot/efi',
                    '--no-variables',
                    '--entry-token', 'os-id'
                ]
            ),
            call(
                [
                    'cp', 'kernel-filename',
                    'system_root_mount/boot/efi/os'
                ]
            ),
            call(
                [
                    'cp', 'system_root_mount/boot/initrd-name',
                    'system_root_mount/boot/efi/os'
                ]
            )
        ]

    @patch('kiwi.bootloader.config.systemd_boot.OsRelease')
    @patch('kiwi.bootloader.config.systemd_boot.glob.iglob')
    @patch.object(BootLoaderSystemdBoot, '_write_config_file')
    def test_set_loader_entry(
        self, mock_write_config_file, mock_iglob, mock_OsRelease
    ):
        mock_iglob.return_value = ['/lib/modules/5.3.18-59.10-default']
        os_release = Mock()
        os_release.get.return_value = 'opensuse-leap'
        mock_OsRelease.return_value = os_release
        self.bootloader.set_loader_entry('root_dir', 'disk')

    @patch('kiwi.bootloader.config.systemd_boot.OsRelease')
    @patch('kiwi.bootloader.config.systemd_boot.glob.iglob')
    def test_set_loader_entry_kernel_lookup_raises(
        self, mock_iglob, mock_OsRelease
    ):
        mock_iglob.return_value = None
        with raises(KiwiKernelLookupError):
            self.bootloader.set_loader_entry('root_dir', 'disk')

    def test_create_loader_image(self):
        self.bootloader.create_loader_image('disk')
        self.bootloader.create_efi_path.assert_called_once_with()

    def test_get_template_parameters(self):
        self.bootloader.timeout = 0
        assert self.bootloader._get_template_parameters() == {
            'kernel_file': 'vmlinuz',
            'initrd_file': 'initrd',
            'boot_options': '',
            'boot_timeout': 0,
            'bootpath': 'bootpath',
            'title': 'title',
            'default_entry': 'main.conf'
        }

    @patch('kiwi.bootloader.config.systemd_boot.Path.create')
    def test_write_config_file(self, mock_Path_create):
        template = Mock()
        template.substitute.return_value = 'data'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader._write_config_file(template, 'path/some-file', {})
            mock_Path_create.assert_called_once_with('path')
            mock_open.assert_called_once_with('path/some-file', 'w')
            file_handle.write.assert_called_once_with('data')

    def test_write_config_file_raises(self):
        template = Mock()
        template.substitute.side_effect = Exception
        with raises(KiwiTemplateError):
            self.bootloader._write_config_file(template, 'some-file', {})

    def test_write_kernel_cmdline_file(self):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.bootloader._write_kernel_cmdline_file('system_root_mount')
            mock_open.assert_called_once_with(
                'system_root_mount/etc/kernel/cmdline', 'w'
            )
            file_handle.write.assert_called_once_with(self.bootloader.cmdline)

    @patch('kiwi.bootloader.config.systemd_boot.Path.create')
    @patch('kiwi.bootloader.config.systemd_boot.Command.run')
    @patch('kiwi.bootloader.config.systemd_boot.LoopDevice')
    @patch('kiwi.bootloader.config.systemd_boot.Disk')
    @patch('kiwi.bootloader.config.systemd_boot.MountManager')
    @patch.object(BootLoaderSystemdBoot, '_run_bootctl')
    @patch.object(BootLoaderSystemdBoot, 'set_loader_entry')
    def test_create_embedded_fat_efi_image(
        self, mock_set_loader_entry, mock_run_bootctl, mock_MountManager,
        mock_Disk, mock_LoopDevice, mock_Command_run, mock_Path_create
    ):
        target = Mock()
        self.bootloader.target = target
        mock_Disk.return_value.__enter__.return_value.partition_map = {
            'efi': 'efi_device'
        }
        self.bootloader._create_embedded_fat_efi_image('ESP')
        assert mock_MountManager.call_args_list == [
            call(device='efi_device', mountpoint='root_dir/boot/efi'),
            call(device='/dev', mountpoint='root_dir/dev'),
            call(device='/proc', mountpoint='root_dir/proc'),
            call(device='/sys', mountpoint='root_dir/sys')
        ]
        assert mock_Command_run.call_args_list == [
            call(['qemu-img', 'create', 'ESP', '20M']),
            call(['sgdisk', '-n', ':1.0', '-t', '1:EF00', 'ESP']),
            call(
                ['mkdosfs', '-n', 'BOOT', 'efi_device']
            ),
            call(['dd', 'if=efi_device', 'of=ESP.img']),
            call(['mv', 'ESP.img', 'ESP'])
        ]
        mock_run_bootctl.assert_called_once_with('root_dir')
        mock_set_loader_entry.assert_called_once_with('root_dir', target.live)
