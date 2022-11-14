import io
from pytest import raises
from mock import (
    Mock, patch, call, MagicMock
)
from kiwi.bootloader.config.systemd_boot import BootLoaderSystemdBoot

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError
)


class TestBootLoaderSystemdBoot:
    def setup(self):
        self.state = Mock()
        self.state.xml_data.get_name.return_value = 'image-name'
        self.state.get_image_version.return_value = 'image-version'
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

    def setup_method(self, cls):
        self.setup()

    def test_setup_loader_raises_invalid_target(self):
        with raises(KiwiBootLoaderTargetError):
            self.bootloader.setup_loader('iso')

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.systemd_boot.BootImageBase.get_boot_names')
    @patch('kiwi.bootloader.config.systemd_boot.Path.wipe')
    @patch('kiwi.bootloader.config.systemd_boot.Command.run')
    @patch('kiwi.bootloader.config.systemd_boot.BootLoaderTemplateSystemdBoot')
    @patch.object(BootLoaderSystemdBoot, '_write_config_file')
    @patch.object(BootLoaderSystemdBoot, '_get_template_parameters')
    @patch.object(BootLoaderSystemdBoot, '_write_kernel_cmdline_file')
    def test_setup_loader(
        self, mock_write_kernel_cmdline_file,
        mock_get_template_parameters, mock_write_config_file,
        mock_BootLoaderTemplateSystemdBoot, mock_Command_run,
        mock_Path_wipe, mock_BootImageBase_get_boot_names,
        mock_os_path_exists
    ):
        kernel_info = Mock()
        kernel_info.kernel_version = 'kernel-version'
        kernel_info.kernel_filename = 'kernel-filename'
        kernel_info.initrd_name = 'initrd-name'
        mock_os_path_exists.return_value = True
        mock_BootImageBase_get_boot_names.return_value = kernel_info
        self.bootloader.setup_loader('disk')
        mock_write_config_file.assert_called_once_with(
            mock_BootLoaderTemplateSystemdBoot.return_value.get_loader_template.return_value,
            'system_root_mount/boot/efi/loader/loader.conf',
            mock_get_template_parameters.return_value
        )
        assert self.bootloader._mount_system.called
        mock_write_kernel_cmdline_file.assert_called_once_with()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', 'system_root_mount', 'bootctl', 'install',
                    '--esp-path=/boot/efi',
                    '--no-variables',
                    '--entry-token', 'os-id'
                ]
            ),
            call(
                [
                    'chroot', 'system_root_mount', 'kernel-install', 'add',
                    'kernel-version', 'kernel-filename',
                    '/boot/initrd-name'
                ]
            )
        ]

    def test_set_loader_entry(self):
        # just pass
        self.bootloader.set_loader_entry('disk')

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
            'title': 'title'
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
            self.bootloader._write_kernel_cmdline_file()
            mock_open.assert_called_once_with(
                'system_root_mount/etc/kernel/cmdline', 'w'
            )
            file_handle.write.assert_called_once_with(self.bootloader.cmdline)
