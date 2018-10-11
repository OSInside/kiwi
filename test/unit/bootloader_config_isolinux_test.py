from mock import patch
from mock import call

import mock

import kiwi

from .test_helper import raises, patch_open

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import (
    KiwiBootLoaderIsoLinuxPlatformError,
    KiwiTemplateError
)
from kiwi.bootloader.config.isolinux import BootLoaderConfigIsoLinux


class TestBootLoaderConfigIsoLinux(object):
    @patch('os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.state = mock.Mock()
        self.state.build_type.get_bootloader_console = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_mediacheck = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_volid = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_flags = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_hybridpersistent = mock.Mock(
            return_value=True
        )
        self.state.build_type.get_hybridpersistent_filesystem = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_boottimeout = mock.Mock(
            return_value=None
        )
        self.state.get_initrd_system = mock.Mock(
            return_value='dracut'
        )
        self.state.build_type.get_kernelcmdline = mock.Mock(
            return_value='splash'
        )
        self.state.build_type.get_firmware = mock.Mock(
            return_value='efi'
        )
        self.state.build_type.get_initrd_system = mock.Mock(
            return_value=None
        )
        self.state.build_type.build_type.get_installboot = mock.Mock(
            return_value=None
        )
        self.state.xml_data.get_displayname = mock.Mock(
            return_value='Bob'
        )
        self.state.xml_data.get_name = mock.Mock(
            return_value='LimeJeOS-openSUSE-13.2'
        )
        self.state.build_type.get_image = mock.Mock(
            return_value='oem'
        )
        preferences = mock.Mock()
        preferences.get_bootloader_theme = mock.Mock(
            return_value=['openSUSE']
        )
        self.state.get_preferences_sections = mock.Mock(
            return_value=[preferences]
        )
        self.state.is_xen_server = mock.Mock(
            return_value=False
        )
        self.state.is_xen_guest = mock.Mock(
            return_value=False
        )
        kiwi.bootloader.config.isolinux.Path = mock.Mock()
        kiwi.bootloader.config.base.Path = mock.Mock()
        self.isolinux = mock.Mock()
        kiwi.bootloader.config.isolinux.BootLoaderTemplateIsoLinux = mock.Mock(
            return_value=self.isolinux
        )
        self.bootloader = BootLoaderConfigIsoLinux(
            self.state, 'root_dir'
        )

    @raises(KiwiBootLoaderIsoLinuxPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigIsoLinux(mock.Mock(), 'root_dir')

    @patch('platform.machine')
    def test_post_init_ix86_platform(self, mock_machine):
        xml_state = XMLState(
            XMLDescription('../data/example_config.xml').load()
        )
        mock_machine.return_value = 'i686'
        bootloader = BootLoaderConfigIsoLinux(xml_state, 'root_dir')
        assert bootloader.arch == 'ix86'

    @patch('os.path.exists')
    @patch('platform.machine')
    def test_post_init_dom0(self, mock_machine, mock_exists):
        self.state.is_xen_server = mock.Mock(
            return_value=True
        )
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.bootloader.post_init(None)
        assert self.bootloader.multiboot is True

    @patch_open
    @patch('os.path.exists')
    def test_write(self, mock_exists, mock_open):
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
        self.bootloader.config_message = 'some-message-data'

        self.bootloader.write()
        assert mock_open.call_args_list == [
            call('root_dir/boot/x86_64/loader/isolinux.cfg', 'w'),
            call('root_dir/boot/x86_64/loader/isolinux.msg', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('some-data'),
            call('some-message-data')
        ]

    def test_setup_install_image_config(self):
        template_cfg = mock.Mock()
        template_msg = mock.Mock()
        self.isolinux.get_install_template.return_value = template_cfg
        self.isolinux.get_install_message_template.return_value = template_msg

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_install_template.assert_called_once_with(
            True, False, None
        )
        self.isolinux.get_install_message_template.assert_called_once_with()
        assert template_cfg.substitute.called
        assert template_msg.substitute.called

    def test_setup_install_image_config_multiboot(self):
        self.bootloader.multiboot = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_multiboot_install_template.assert_called_once_with(
            True, False, None
        )

    @patch('os.path.exists')
    def test_setup_install_image_config_with_theme(self, mock_exists):
        mock_exists.return_value = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_install_template.assert_called_once_with(
            True, True, None
        )

    @raises(KiwiTemplateError)
    def test_setup_install_image_config_invalid_template(self):
        self.isolinux.get_install_message_template.side_effect = Exception
        self.bootloader.setup_install_image_config(mbrid=None)

    @patch('kiwi.bootloader.config.isolinux.DataSync')
    @patch('kiwi.bootloader.config.isolinux.shutil')
    @patch('kiwi.bootloader.config.isolinux.Command.run')
    @patch('os.path.exists')
    def test_setup_install_boot_images(
        self, mock_exists, mock_command, mock_shutil, mock_sync
    ):
        mock_exists.return_value = True
        data = mock.Mock()
        mock_sync.return_value = data
        self.bootloader.setup_install_boot_images(
            mbrid=None
        )
        assert mock_shutil.copy.call_args_list == [
            call(
                'root_dir/usr/share/syslinux/isolinux.bin',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/isolinux.bin',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/isolinux.bin',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/ldlinux.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/ldlinux.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/ldlinux.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/libcom32.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/libcom32.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/libcom32.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/libutil.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/libutil.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/libutil.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/gfxboot.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/gfxboot.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/gfxboot.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/gfxboot.com',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/gfxboot.com',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/gfxboot.com',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/menu.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/menu.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/menu.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/chain.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/chain.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/chain.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/syslinux/mboot.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/syslinux/modules/bios/mboot.c32',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/lib/ISOLINUX/mboot.c32',
                'root_dir/image/loader/'
            )
        ]
        assert mock_command.call_args_list == [
            call(
                command=[
                    'bash', '-c',
                    'cp root_dir/boot/memtest* ' +
                    'root_dir/image/loader//memtest'
                ], raise_on_error=False
            ),
            call(
                [
                    'bash', '-c',
                    'cp root_dir/etc/bootsplash/themes/openSUSE/' +
                    'cdrom/* root_dir/image/loader/'
                ]
            ),
            call(
                [
                    'gfxboot',
                    '--config-file', 'root_dir/image/loader//gfxboot.cfg',
                    '--change-config', 'install::autodown=0'
                ]
            ),
            call(
                [
                    'cp',
                    'root_dir/etc/bootsplash/themes/openSUSE/' +
                    'bootloader/message', 'root_dir/image/loader/'
                ]
            )
        ]
        mock_sync.assert_called_once_with(
            'root_dir/image/loader/',
            'root_dir/boot/x86_64/loader'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a']
        )

    @patch.object(BootLoaderConfigIsoLinux, 'setup_install_boot_images')
    def test_setup_live_boot_images(self, mock_install_boot_images):
        self.bootloader.setup_live_boot_images(
            mbrid=None, lookup_path='lookup_dir'
        )
        mock_install_boot_images.assert_called_once_with(
            None, 'lookup_dir'
        )

    @raises(KiwiTemplateError)
    def test_setup_live_image_config_invalid_template(self):
        self.isolinux.get_message_template.side_effect = Exception
        self.bootloader.setup_live_image_config(mbrid=None)

    def test_setup_live_image_config(self):
        template_parameters = {
            'initrd_file': 'initrd',
            'default_boot': 'Bob',
            'title': 'Bob',
            'gfxmode': '800 600',
            'boot_options': 'splash root=live:CDLABEL=CDROM' +
            ' rd.live.image rd.live.overlay.persistent',
            'boot_timeout': 100,
            'failsafe_boot_options': 'splash ide=nodma apm=off' +
            ' noresume edd=off nomodeset 3' +
            ' root=live:CDLABEL=CDROM rd.live.image' +
            ' rd.live.overlay.persistent',
            'kernel_file': 'linux'
        }
        template_cfg = mock.Mock()
        template_msg = mock.Mock()
        self.isolinux.get_template.return_value = template_cfg
        self.isolinux.get_message_template.return_value = template_msg

        self.bootloader.setup_live_image_config(mbrid=None)
        self.isolinux.get_template.assert_called_once_with(
            True, False, None, None
        )
        self.isolinux.get_message_template.assert_called_once_with()
        template_cfg.substitute.assert_called_once_with(template_parameters)
        template_msg.substitute.assert_called_once_with(template_parameters)

    def test_setup_live_image_config_multiboot(self):
        self.bootloader.multiboot = True

        self.bootloader.setup_live_image_config(mbrid=None)
        self.isolinux.get_multiboot_template.assert_called_once_with(
            True, False, None, None
        )
