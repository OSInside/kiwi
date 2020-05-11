import kiwi
import mock
from mock import (
    patch, call, mock_open
)
from pytest import (
    raises, fixture
)
from kiwi.bootloader.config.isolinux import BootLoaderConfigIsoLinux

from kiwi.exceptions import KiwiTemplateError


class TestBootLoaderConfigIsoLinux:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        self.state = mock.Mock()
        self.state.get_build_type_bootloader_console = mock.Mock(
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
        self.state.get_build_type_bootloader_timeout = mock.Mock(
            return_value=None
        )
        self.state.build_type.get_install_continue_on_timeout = mock.Mock(
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

    @patch('platform.machine')
    def test_post_init_ix86_platform(self, mock_machine):
        mock_machine.return_value = 'i686'
        bootloader = BootLoaderConfigIsoLinux(self.state, 'root_dir')
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

    @patch('os.path.exists')
    def test_write(self, mock_exists):
        mock_exists.return_value = True
        self.bootloader.config = 'some-data'
        self.bootloader.config_message = 'some-message-data'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.bootloader.write()

        assert m_open.call_args_list == [
            call('root_dir/boot/x86_64/loader/isolinux.cfg', 'w'),
            call('root_dir/boot/x86_64/loader/isolinux.msg', 'w')
        ]
        assert m_open.return_value.write.call_args_list == [
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
            True, False, None, True
        )
        self.isolinux.get_install_message_template.assert_called_once_with()
        assert template_cfg.substitute.called
        assert template_msg.substitute.called

    def test_setup_install_image_config_multiboot(self):
        self.bootloader.multiboot = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_multiboot_install_template.assert_called_once_with(
            True, False, None, True
        )

    @patch('os.path.exists')
    def test_setup_install_image_config_with_theme(self, mock_exists):
        mock_exists.return_value = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_install_template.assert_called_once_with(
            True, True, None, True
        )

    def test_setup_install_image_config_invalid_template(self):
        self.isolinux.get_install_message_template.side_effect = Exception
        with raises(KiwiTemplateError):
            self.bootloader.setup_install_image_config(mbrid=None)

    def test_setup_install_boot_images(self):
        assert self.bootloader.setup_install_boot_images(mbrid=None) is None

    def test_setup_live_boot_images(self):
        assert self.bootloader.setup_live_boot_images(mbrid=None) is None

    def test_setup_live_image_config_invalid_template(self):
        self.isolinux.get_message_template.side_effect = Exception
        with raises(KiwiTemplateError):
            self.bootloader.setup_live_image_config(mbrid=None)

    def test_setup_live_image_config(self):
        template_parameters = {
            'initrd_file': 'initrd',
            'default_boot': 'Bob',
            'title': 'Bob',
            'gfxmode': '800 600',
            'boot_options': 'splash root=live:CDLABEL=CDROM'
            ' rd.live.image rd.live.overlay.persistent',
            'boot_timeout': 100,
            'failsafe_boot_options': 'splash ide=nodma apm=off'
            ' noresume edd=off nomodeset 3'
            ' root=live:CDLABEL=CDROM rd.live.image'
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
