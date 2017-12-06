from mock import patch

import mock

import kiwi

from .test_helper import raises, patch_open

from collections import namedtuple

from kiwi.exceptions import (
    KiwiBootLoaderZiplPlatformError,
    KiwiBootLoaderZiplSetupError,
    KiwiDiskGeometryError,
    KiwiTemplateError
)

from kiwi.bootloader.config.zipl import BootLoaderConfigZipl


class TestBootLoaderConfigZipl(object):
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
        self.xml_state.build_type.get_boottimeout = mock.Mock(
            return_value='200'
        )
        self.xml_state.build_type.get_target_blocksize = mock.Mock(
            return_value=None
        )
        self.xml_state.build_type.get_zipl_targettype = mock.Mock(
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
            self.xml_state, 'root_dir', {'targetbase': '/dev/loop0'}
        )

    @raises(KiwiBootLoaderZiplPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigZipl(mock.Mock(), 'root_dir')

    @patch('platform.machine')
    @raises(KiwiBootLoaderZiplSetupError)
    def test_post_init_no_target_base(self, mock_machine):
        mock_machine.return_value = 's390'
        BootLoaderConfigZipl(mock.Mock(), 'root_dir')

    @patch_open
    @patch('os.path.exists')
    @patch('kiwi.bootloader.config.zipl.Path.create')
    @patch('kiwi.bootloader.config.zipl.Command.run')
    def test_write(self, mock_command, mock_path, mock_exists, mock_open):
        mock_exists.return_value = True
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        self.bootloader.config = 'some-data'

        self.bootloader.write()

        mock_path.assert_called_once_with(
            'root_dir/boot/zipl'
        )
        mock_open.assert_called_once_with(
            'root_dir/boot/zipl/config', 'w'
        )
        file_mock.write.assert_called_once_with(
            'some-data'
        )
        mock_command.assert_called_once_with(
            [
                'mv',
                'root_dir/boot/initrd.vmx',
                'root_dir/boot/linux.vmx',
                'root_dir/boot/zipl'
            ]
        )

    def test_setup_disk_boot_images(self):
        # does nothing on s390
        self.bootloader.setup_disk_boot_images('uuid')

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @raises(KiwiTemplateError)
    def test_setup_disk_image_config_template_error(self, mock_command):
        self.template.substitute.side_effect = Exception
        self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @raises(KiwiDiskGeometryError)
    def test_setup_disk_image_config_dasd_invalid_offset(self, mock_command):
        command_results = [
            self.command_type(output='bogus data\n'),
            self.command_type(output='  blocks per track .....: 12\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @raises(KiwiDiskGeometryError)
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
        self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @raises(KiwiDiskGeometryError)
    def test_setup_disk_image_config_dasd_invalid_geometry(self, mock_command):
        command_results = [
            self.command_type(output='bogus data\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
        self.bootloader.setup_disk_image_config()

    @patch('kiwi.bootloader.config.zipl.Command.run')
    @raises(KiwiDiskGeometryError)
    def test_setup_disk_image_config_msdos_invalid_geometry(self, mock_command):
        self.bootloader.target_table_type = 'msdos'
        command_results = [
            self.command_type(output='bogus data\n')
        ]

        def side_effect(arg):
            return command_results.pop()

        mock_command.side_effect = side_effect
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

        self.bootloader.setup_disk_image_config(boot_options='foo')

        self.zipl.get_template.assert_called_once_with(True)
        self.template.substitute.assert_called_once_with(
            {
                'blocksize': '4096',
                'initrd_file': 'initrd.vmx',
                'offset': 168,
                'device': '/dev/loop0',
                'kernel_file': 'linux.vmx',
                'title': 'image-name_(_OEM_)',
                'geometry': '10017,15,12',
                'boot_options': 'cmdline foo',
                'target_type': 'CDL',
                'boot_timeout': '200',
                'failsafe_boot_options': 'cmdline ide=nodma apm=off '
                'noresume edd=off nomodeset 3 foo',
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

        self.bootloader.setup_disk_image_config()

        self.zipl.get_template.assert_called_once_with(True)
        self.template.substitute.assert_called_once_with(
            {
                'blocksize': '4096',
                'initrd_file': 'initrd.vmx',
                'offset': 129024,
                'device': '/dev/loop0',
                'kernel_file': 'linux.vmx',
                'title': 'image-name_(_OEM_)',
                'geometry': '242251,256,63',
                'boot_options': 'cmdline ',
                'target_type': 'CDL',
                'boot_timeout': '200',
                'failsafe_boot_options': 'cmdline ide=nodma apm=off noresume '
                'edd=off nomodeset 3 ',
                'default_boot': '1',
                'bootpath': '.'
            }
        )
