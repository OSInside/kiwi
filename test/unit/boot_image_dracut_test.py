import sys
import mock

from mock import patch
from mock import call

import kiwi

from .test_helper import *

from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.exceptions import *


class TestBootImageKiwi(object):
    @patch('kiwi.boot.image.base.mkdtemp')
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists, mock_mkdtemp):
        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )
        self.setup = mock.Mock()
        self.profile = mock.Mock()
        self.manager = mock.Mock()
        self.system_prepare = mock.Mock()
        self.system_prepare.setup_repositories = mock.Mock(
            return_value=self.manager
        )
        kiwi.boot.image.dracut.SystemPrepare = mock.Mock(
            return_value=self.system_prepare
        )
        kiwi.boot.image.dracut.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        kiwi.boot.image.dracut.Profile = mock.Mock(
            return_value=self.profile
        )
        mock_mkdtemp.return_value = 'boot-directory'
        self.boot_image = BootImageDracut(
            self.xml_state, 'some-target-dir'
        )

    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    def test_prepare(self, mock_boot_path):
        mock_boot_path.return_value = '../data'
        self.boot_image.prepare()
        self.system_prepare.setup_repositories.assert_called_once_with()
        self.system_prepare.install_bootstrap.assert_called_once_with(
            self.manager
        )
        self.system_prepare.install_system.assert_called_once_with(
            self.manager
        )
        assert self.profile.add.call_args_list[0] == call(
            'kiwi_initrdname', 'initrd-oemboot-suse-13.2'
        )
        self.setup.import_shell_environment.assert_called_once_with(
            self.profile
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.call_image_script.assert_called_once_with()

    @raises(KiwiConfigFileNotFound)
    @patch('os.path.exists')
    def test_prepare_no_boot_description_found(self, mock_os_path):
        mock_os_path.return_value = False
        self.boot_image.prepare()

    @patch('kiwi.boot.image.dracut.Compress')
    @patch('kiwi.boot.image.dracut.Kernel.get_kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    def test_create_initrd(
        self, mock_prepared, mock_command, mock_get_kernel, mock_compress
    ):
        kernel = mock.Mock()
        kernel.version = '1.2.3'
        mock_get_kernel.return_value = kernel
        compress = mock.Mock()
        mock_compress.return_value = compress
        self.boot_image.create_initrd()
        assert mock_command.call_args_list == [
            call([
                'chroot', 'boot-directory',
                'dracut', '--force', '--no-hostonly',
                '--no-hostonly-cmdline', '--no-compress',
                'LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd', '1.2.3'
            ]),
            call([
                'mv',
                'boot-directory/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd',
                'some-target-dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd'
            ])
        ]
        mock_compress.assert_called_once_with(
            self.boot_image.target_dir +
            '/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd'
        )
        compress.xz.assert_called_once_with()
