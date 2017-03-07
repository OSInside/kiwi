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
        description = XMLDescription(
            '../data/example_config.xml'
        )
        self.state = XMLState(
            description.load()
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
        self.bootloader.get_hypervisor_domain = mock.Mock(
            return_value='domU'
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
        mock_machine.return_value = 'x86_64'
        self.bootloader.get_hypervisor_domain.return_value = 'dom0'
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
    def test_setup_install_boot_images(self, mock_sync):
        data = mock.Mock()
        mock_sync.return_value = data
        self.bootloader.setup_install_boot_images(
            mbrid=None, lookup_path='lookup_dir'
        )
        mock_sync.assert_called_once_with(
            'lookup_dir/image/loader/',
            'root_dir/boot/x86_64/loader'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a']
        )

    @patch('kiwi.bootloader.config.isolinux.DataSync')
    def test_setup_live_boot_images(self, mock_sync):
        data = mock.Mock()
        mock_sync.return_value = data
        self.bootloader.setup_live_boot_images(
            mbrid=None
        )
        mock_sync.assert_called_once_with(
            'root_dir/image/loader/',
            'root_dir/boot/x86_64/loader'
        )
        data.sync_data.assert_called_once_with(
            options=['-z', '-a']
        )

    @raises(KiwiTemplateError)
    def test_setup_live_image_config_invalid_template(self):
        self.isolinux.get_message_template.side_effect = Exception
        self.bootloader.setup_live_image_config(mbrid=None)

    def test_setup_live_image_config(self):
        template_cfg = mock.Mock()
        template_msg = mock.Mock()
        self.isolinux.get_template.return_value = template_cfg
        self.isolinux.get_message_template.return_value = template_msg

        self.bootloader.setup_live_image_config(mbrid=None)
        self.isolinux.get_template.assert_called_once_with(
            True, False, None
        )
        self.isolinux.get_message_template.assert_called_once_with()
        assert template_cfg.substitute.called
        assert template_msg.substitute.called

    def test_setup_live_image_config_multiboot(self):
        self.bootloader.multiboot = True

        self.bootloader.setup_live_image_config(mbrid=None)
        self.isolinux.get_multiboot_template.assert_called_once_with(
            True, False, None
        )
