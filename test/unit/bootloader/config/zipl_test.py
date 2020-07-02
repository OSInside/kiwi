from mock import (
    patch, mock_open
)
from pytest import raises
from collections import namedtuple
import mock

import kiwi

from kiwi.bootloader.config.zipl import BootLoaderConfigZipl
from kiwi.exceptions import (
    KiwiBootLoaderZiplPlatformError,
    KiwiBootLoaderZiplSetupError,
    KiwiDiskGeometryError,
    KiwiTemplateError
)


class TestBootLoaderConfigZipl:
    @patch('kiwi.bootloader.config.zipl.FirmWare')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_firmware):
        self.command_type = namedtuple(
            'command_return_type', ['output']
        )

        mock_machine.return_value = 's390'

        self.firmware = mock.Mock()
        self.firmware.get_partition_table_type = mock.Mock(
            return_value='dasd'
        )
        mock_firmware.return_value = self.firmware

        self.zipl = mock.Mock()
        self.template = mock.Mock()
        self.zipl.get_template.return_value = self.template
        kiwi.bootloader.config.zipl.BootLoaderTemplateZipl = mock.Mock(
            return_value=self.zipl
        )

        self.xml_state = mock.Mock()
        self.xml_state.build_type.get_initrd_system = mock.Mock(
            return_value=None
        )
        self.xml_state.build_type.get_firmware = mock.Mock(
            return_value=None
        )
        self.xml_state.get_build_type_bootloader_timeout = mock.Mock(
            return_value='200'
        )
        self.xml_state.build_type.get_target_blocksize = mock.Mock(
            return_value=None
        )
        self.xml_state.get_build_type_bootloader_targettype = mock.Mock(
            return_value=None
        )
        self.xml_state.build_type.get_kernelcmdline = mock.Mock(
            return_value='cmdline'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='image-name'
        )
        self.xml_state.xml_data.get_displayname = mock.Mock(
            return_value=None
        )
        self.xml_state.build_type.get_image = mock.Mock(
            return_value='oem'
        )
        self.bootloader = BootLoaderConfigZipl(
            self.xml_state, 'root_dir', None, {'targetbase': '/dev/loop0'}
        )

    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        with raises(KiwiBootLoaderZiplPlatformError):
            BootLoaderConfigZipl(mock.Mock(), 'root_dir')

    @patch('platform.machine')
    def test_post_init_no_target_base(self, mock_machine):
        mock_machine.return_value = 's390'
        with raises(KiwiBootLoaderZiplSetupError):
            BootLoaderConfigZipl(mock.Mock(), 'root_dir')

    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.zipl.Path.create')
    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_write(
        self, mock_command, mock_path, mock_exists
    ):
        mock_exists.return_value = True

        self.bootloader.config = 'some-data'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.bootloader.write()

        mock_path.assert_called_once_with(
            'root_dir/boot/zipl'
        )
        m_open.assert_called_once_with(
            'root_dir/boot/zipl/config', 'w'
        )
        m_open.return_value.write.assert_called_once_with(
            'some-data'
        )

    def test_setup_disk_boot_images(self):
        # does nothing on s390
        self.bootloader.setup_disk_boot_images('uuid')

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_template_error(self, mock_command):
        self.template.substitute.side_effect = Exception
        with raises(KiwiTemplateError):
            self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_dasd_invalid_offset(self, mock_command):
        command_results = [
            self.command_type(output='bogus data\n'),
            self.command_type(output='  blocks per track .....: 12\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        with raises(KiwiDiskGeometryError):
            self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_msdos_invalid_offset(self, mock_command):
        self.bootloader.target_table_type = 'msdos'
        command_results = [
            self.command_type(output='bogus data\n'),
            self.command_type(
                output='/dev/sda: 242251 cylinders, 256 heads, '
                '63 sectors/track\n'
            )
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        with raises(KiwiDiskGeometryError):
            self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_dasd_invalid_geometry(self, mock_command):
        command_results = [
            self.command_type(output='bogus data\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        with raises(KiwiDiskGeometryError):
            self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_msdos_invalid_geometry(self, mock_command):
        self.bootloader.target_table_type = 'msdos'
        command_results = [
            self.command_type(output='bogus data\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        with raises(KiwiDiskGeometryError):
            self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_dasd(self, mock_command):
        command_results = [
            self.command_type(output='  blocks per track .....: 12\n'),
            self.command_type(output='  tracks per cylinder ..: 15\n'),
            self.command_type(output='  cylinders ............: 10017\n'),
            self.command_type(output=' 2 14 13 unused\n'),
            self.command_type(output='  blocks per track .....: 12\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect

        self.bootloader.setup_disk_image_config(
            kernel='image', initrd='initrd'
        )

        self.zipl.get_template.assert_called_once_with(True, 'CDL')
        self.template.substitute.assert_called_once_with(
            {
                'blocksize': '4096',
                'initrd_file': 'initrd',
                'offset': 168,
                'device': '/dev/loop0',
                'kernel_file': 'image',
                'title': 'image-name_(_OEM_)',
                'geometry': '10017,15,12',
                'boot_options': 'cmdline',
                'target_type': 'CDL',
                'boot_timeout': '200',
                'failsafe_boot_options': 'cmdline ide=nodma apm=off '
                'noresume edd=off nomodeset 3',
                'default_boot': '1',
                'bootpath': '.'
            }
        )

    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_setup_disk_image_config_fcp(self, mock_command):
        self.bootloader.target_table_type = 'msdos'
        command_results = [
            self.command_type(
                output='/dev/sda: 242251 cylinders, 256 heads, '
                '63 sectors/track\n'
            ),
            self.command_type(
                output='/dev/sda: 242251 cylinders, 256 heads, '
                '63 sectors/track\n'
            ),
            self.command_type(
                output='/dev/sda: 242251 cylinders, 256 heads, '
                '63 sectors/track\n'
            ),
            self.command_type(
                output='BYT; /dev/sda:312500000s:scsi:512:512:msdos:ATA '
                'WDC WD1600HLFS-7; 1:2048s:251660287s:251658240s:ext4::type=83;'
                ' 2:251660288s:312499999s:60839712s:linux-swap(v1)::type=82;'
            ),
            self.command_type(
                output='/dev/sda: 242251 cylinders, 256 heads, '
                '63 sectors/track\n'
            )
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect

        self.bootloader.setup_disk_image_config(
            kernel='image', initrd='initrd'
        )

        self.zipl.get_template.assert_called_once_with(True, 'CDL')
        self.template.substitute.assert_called_once_with(
            {
                'blocksize': '4096',
                'initrd_file': 'initrd',
                'offset': 129024,
                'device': '/dev/loop0',
                'kernel_file': 'image',
                'title': 'image-name_(_OEM_)',
                'geometry': '242251,256,63',
                'boot_options': 'cmdline',
                'target_type': 'CDL',
                'boot_timeout': '200',
                'failsafe_boot_options': 'cmdline ide=nodma apm=off noresume '
                'edd=off nomodeset 3',
                'default_boot': '1',
                'bootpath': '.'
            }
        )
