from nose.tools import *
from mock import patch
from mock import call

import mock

import kiwi

import nose_helper

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import *
from kiwi.bootloader_config_isolinux import BootLoaderConfigIsoLinux


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
        kiwi.bootloader_config_isolinux.Path = mock.Mock()
        kiwi.bootloader_config_base.Path = mock.Mock()
        self.isolinux = mock.Mock()
        kiwi.bootloader_config_isolinux.BootLoaderTemplateIsoLinux = mock.Mock(
            return_value=self.isolinux
        )
        self.bootloader = BootLoaderConfigIsoLinux(
            self.state, 'source_dir'
        )
        self.bootloader.get_hypervisor_domain = mock.Mock(
            return_value='domU'
        )

    @raises(KiwiBootLoaderIsoLinuxPlatformError)
    @patch('platform.machine')
    def test_post_init_invalid_platform(self, mock_machine):
        mock_machine.return_value = 'unsupported-arch'
        BootLoaderConfigIsoLinux(mock.Mock(), 'source_dir')

    @patch('os.path.exists')
    def test_post_init_dom0(self, mock_exists):
        self.bootloader.get_hypervisor_domain.return_value = 'dom0'
        mock_exists.return_value = True

        self.bootloader.post_init()
        assert self.bootloader.multiboot is True

    @patch('__builtin__.open')
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
            call('source_dir/boot/x86_64/loader/isolinux.cfg', 'w'),
            call('source_dir/boot/x86_64/loader/isolinux.msg', 'w')
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
        self.isolinux.get_install_template.assert_called_once_with(True, False)
        self.isolinux.get_install_message_template.assert_called_once_with()
        assert template_cfg.substitute.called
        assert template_msg.substitute.called

    def test_setup_install_image_config_multiboot(self):
        self.bootloader.multiboot = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_multiboot_install_template.assert_called_once_with(
            True, False
        )

    @patch('os.path.exists')
    def test_setup_install_image_config_with_theme(self, mock_exists):
        mock_exists.return_value = True

        self.bootloader.setup_install_image_config(mbrid=None)
        self.isolinux.get_install_template.assert_called_once_with(True, True)

    @raises(KiwiTemplateError)
    def test_setup_install_image_config_invalid_template(self):
        self.isolinux.get_install_message_template.side_effect = Exception
        self.bootloader.setup_install_image_config(mbrid=None)

    @patch('kiwi.bootloader_config_isolinux.Command.run')
    def test_setup_install_boot_images(self, mock_command):
        self.bootloader.setup_install_boot_images(
            mbrid=None, lookup_path='lookup_dir'
        )
        mock_command.assert_called_once_with(
            [
                'rsync', '-zav', 'lookup_dir/image/loader/',
                'source_dir/boot/x86_64/loader'
            ]
        )

    @patch('kiwi.bootloader_config_isolinux.Command.run')
    def test_setup_live_boot_images(self, mock_command):
        self.bootloader.setup_live_boot_images(
            mbrid=None
        )
        mock_command.assert_called_once_with(
            [
                'rsync', '-zav', 'source_dir/image/loader/',
                'source_dir/boot/x86_64/loader'
            ]
        )

    def test_setup_live_image_config(self):
        # TODO
        self.bootloader.setup_live_image_config(mbrid=None)
