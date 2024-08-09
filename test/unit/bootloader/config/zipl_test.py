import io
from pytest import raises
from unittest.mock import (
    Mock, patch, call, MagicMock
)
from kiwi.bootloader.config.zipl import BootLoaderZipl
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase
from kiwi.command import CommandT

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError,
    KiwiDiskGeometryError
)


class TestBootLoaderZipl:
    @patch('kiwi.bootloader.config.bootloader_spec_base.FirmWare')
    def setup(self, mock_FirmWare):
        self.firmware = Mock()
        mock_FirmWare.return_value = self.firmware
        self.state = Mock()
        self.state.get_build_type_bootloader_targettype.return_value = 'CDL'
        self.state.build_type.get_target_blocksize.return_value = 4096
        self.state.xml_data.get_name.return_value = 'image-name'
        self.state.get_image_version.return_value = 'image-version'
        self.state.build_type.get_efifatimagesize.return_value = None
        self.bootloader = BootLoaderZipl(self.state, 'root_dir')
        self.bootloader.custom_args['kernel'] = None
        self.bootloader.custom_args['initrd'] = None
        self.bootloader.custom_args['boot_options'] = {}
        self.bootloader.custom_args['targetbase'] = '/dev/disk'
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
    @patch('kiwi.bootloader.config.zipl.BootImageBase.get_boot_names')
    @patch('kiwi.bootloader.config.zipl.Path.wipe')
    @patch('kiwi.bootloader.config.zipl.Path.create')
    @patch('kiwi.bootloader.config.zipl.Command.run')
    @patch('kiwi.bootloader.config.zipl.BootLoaderTemplateZipl')
    @patch('kiwi.bootloader.config.zipl.Temporary.new_file')
    @patch.object(BootLoaderZipl, '_write_config_file')
    @patch.object(BootLoaderZipl, '_get_template_parameters')
    @patch.object(BootLoaderSpecBase, 'get_entry_name')
    def test_setup_loader(
        self, mock_get_entry_name, mock_get_template_parameters,
        mock_write_config_file, mock_Temporary_new_file,
        mock_BootLoaderTemplateZipl, mock_Command_run,
        mock_Path_create, mock_Path_wipe, mock_BootImageBase_get_boot_names,
        mock_os_path_exists
    ):
        temporary = Mock()
        temporary.name = 'system_root_mount/kiwi_zipl.conf_'
        mock_Temporary_new_file.return_value = temporary
        mock_get_entry_name.return_value = \
            'opensuse-leap-5.3.18-59.10-default.conf'

        mock_get_template_parameters.return_value = {
            'targetbase': '/dev/loop'
        }
        kernel_info = Mock()
        kernel_info.kernel_version = 'kernel-version'
        kernel_info.kernel_filename = 'kernel-filename'
        kernel_info.initrd_name = 'initrd-name'
        mock_os_path_exists.return_value = True
        mock_BootImageBase_get_boot_names.return_value = kernel_info
        self.bootloader.setup_loader('disk')
        assert mock_write_config_file.call_args_list == [
            call(
                mock_BootLoaderTemplateZipl.
                return_value.get_loader_template.return_value,
                'system_root_mount/kiwi_zipl.conf_',
                mock_get_template_parameters.return_value
            ),
            call(
                mock_BootLoaderTemplateZipl.
                return_value.get_entry_template.return_value,
                'system_root_mount/boot/loader/entries/'
                'opensuse-leap-5.3.18-59.10-default.conf',
                mock_get_template_parameters.return_value
            )
        ]
        assert self.bootloader._mount_system.called
        mock_Command_run.assert_called_once_with(
            [
                'chroot', 'system_root_mount', 'zipl',
                '--noninteractive',
                '--config', '/kiwi_zipl.conf_',
                '--blsdir', '/boot/loader/entries',
                '--verbose'
            ]
        )

    @patch.object(BootLoaderZipl, '_get_disk_geometry')
    @patch.object(BootLoaderZipl, '_get_partition_start')
    def test_get_template_parameters(
        self, mock_get_partition_start, mock_get_disk_geometry
    ):
        mock_get_partition_start.return_value = '42'
        mock_get_disk_geometry.return_value = '123,53,9'
        self.bootloader.timeout = 0
        self.bootloader.disk_type = 'CDL'
        self.bootloader.disk_blocksize = 4096
        assert self.bootloader._get_template_parameters() == {
            'kernel_file': 'vmlinuz',
            'initrd_file': 'initrd',
            'boot_options': '',
            'boot_timeout': 0,
            'bootpath': 'bootpath',
            'targetbase': 'targetbase=/dev/disk',
            'targettype': 'CDL',
            'targetblocksize': '4096',
            'targetoffset': '42',
            'targetgeometry': 'targetgeometry=123,53,9',
            'title': 'title',
            'default_entry': ''
        }

    @patch('kiwi.bootloader.config.zipl.Path.create')
    @patch.object(BootLoaderZipl, '_get_template_parameters')
    def test_write_config_file(
        self, mock_get_template_parameters, mock_Path_create
    ):
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

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_get_disk_geometry(self, mock_Command_run):
        command_return_values = [
            CommandT(
                output='  cylinders ............: 10017\n',
                error='', returncode=0
            ),
            CommandT(
                output='  tracks per cylinder ..: 15\n',
                error='', returncode=0
            ),
            CommandT(
                output='  blocks per track .....: 12\n',
                error='', returncode=0
            )
        ]

        def command_run(arg):
            return command_return_values.pop(0)

        self.firmware.get_partition_table_type.return_value = 'dasd'
        mock_Command_run.side_effect = command_run
        assert self.bootloader._get_disk_geometry() == '10017,15,12'

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_get_partition_start_dasd(self, mock_Command_run):
        self.firmware.get_partition_table_type.return_value = 'dasd'
        command_return_values = [
            CommandT(
                output='  blocks per track .....: 12\n',
                error='', returncode=0
            ),
            CommandT(
                output=' /dev/loop01 2 6401 6400 1 Linux native\n',
                error='', returncode=0
            )
        ]

        def command_run(arg):
            return command_return_values.pop(0)

        mock_Command_run.side_effect = command_run
        assert self.bootloader._get_partition_start() == '24'
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'bash', '-c',
                    'fdasd -f -p /dev/disk | grep "blocks per track"'
                ]
            ),
            call(
                [
                    'bash', '-c',
                    'fdasd -f -s -p /dev/disk | grep "^ " |'
                    ' head -n 1 | tr -s " "'
                ]
            )
        ]

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_get_partition_start_not_dasd(self, mock_Command_run):
        self.firmware.get_partition_table_type.return_value = 'msdos'
        command = Mock()
        command.output = '  2048'
        mock_Command_run.return_value = command
        assert self.bootloader._get_partition_start() == '2048'
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'sfdisk --dump /dev/disk | grep "1 :" |'
                ' cut -f1 -d, | cut -f2 -d='
            ]
        )

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @patch.object(BootLoaderZipl, '_get_dasd_disk_geometry_element')
    def test_get_partition_start_raises(
        self, mock_get_dasd_disk_geometry_element, mock_Command_run
    ):
        self.firmware.get_partition_table_type.return_value = 'dasd'
        mock_Command_run.return_value = CommandT(
            output='bogus data', error='', returncode=0
        )
        with raises(KiwiDiskGeometryError):
            self.bootloader._get_partition_start()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_get_dasd_disk_geometry_element_raises(
        self, mock_Command_run
    ):
        self.bootloader.target_table_type = 'dasd'
        mock_Command_run.return_value = CommandT(
            output='bogus data', error='', returncode=0
        )
        with raises(KiwiDiskGeometryError):
            self.bootloader._get_dasd_disk_geometry_element(
                '/dev/disk', 'tracks per cylinder'
            )
