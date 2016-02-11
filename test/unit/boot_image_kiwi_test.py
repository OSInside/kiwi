import sys
import mock
from nose.tools import *
from mock import patch
from mock import call

import kiwi

import nose_helper

from kiwi.boot_image_kiwi import BootImageKiwi
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.exceptions import *


class TestBootImageKiwi(object):
    @patch('kiwi.boot_image_base.mkdtemp')
    @patch('kiwi.boot_image_base.os.path.exists')
    def setup(self, mock_exists, mock_mkdtemp):
        mock_exists.return_value = True
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )

        self.manager = mock.Mock()
        self.system = mock.Mock()
        self.setup = mock.Mock()
        self.profile = mock.Mock()
        self.defaults = mock.Mock()
        self.system.setup_repositories = mock.Mock(
            return_value=self.manager
        )
        kiwi.boot_image_kiwi.System = mock.Mock(
            return_value=self.system
        )
        kiwi.boot_image_kiwi.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        kiwi.boot_image_kiwi.Profile = mock.Mock(
            return_value=self.profile
        )
        mock_mkdtemp.return_value = 'boot-directory'
        self.task = BootImageKiwi(
            self.xml_state, 'some-target-dir'
        )

    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    def test_prepare(self, mock_boot_path):
        mock_boot_path.return_value = '../data'
        self.task.prepare()
        self.system.setup_repositories.assert_called_once_with()
        self.system.install_bootstrap.assert_called_once_with(
            self.manager
        )
        self.system.install_system.assert_called_once_with(
            self.manager
        )
        self.setup.import_shell_environment.assert_called_once_with(
            self.profile
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.import_overlay_files.assert_called_once_with(
            follow_links=True
        )
        self.setup.call_config_script.assert_called_once_with()
        self.system.pinch_system.assert_called_once_with(
            manager=self.manager, force=True
        )
        self.setup.call_image_script.assert_called_once_with()

    @raises(KiwiConfigFileNotFound)
    @patch('os.path.exists')
    def test_prepare_no_boot_description_found(self, mock_os_path):
        mock_os_path.return_value = False
        self.task.prepare()

    @patch('kiwi.boot_image_kiwi.ArchiveCpio')
    @patch('kiwi.boot_image_kiwi.Compress')
    @patch('kiwi.boot_image_kiwi.Path.create')
    @patch('kiwi.boot_image_kiwi.Path.wipe')
    @patch('kiwi.boot_image_kiwi.Command.run')
    @patch('kiwi.boot_image_base.BootImageBase.is_prepared')
    @patch('kiwi.boot_image_kiwi.mkdtemp')
    def test_create_initrd(
        self, mock_mkdtemp, mock_prepared, mock_command, mock_wipe,
        mock_create, mock_compress, mock_cpio
    ):
        mock_mkdtemp.return_value = 'temp-boot-directory'
        mock_prepared.return_value = True
        mbrid = mock.Mock()
        mbrid.write = mock.Mock()
        cpio = mock.Mock()
        compress = mock.Mock()
        mock_cpio.return_value = cpio
        mock_compress.return_value = compress
        self.task.create_initrd(mbrid)
        mock_command.assert_called_once_with(
            ['rsync', '-zav', 'boot-directory/', 'temp-boot-directory']
        )
        mock_cpio.assert_called_once_with(
            self.task.target_dir + '/LimeJeOS-openSUSE-13.2.initrd'
        )
        mock_compress.assert_called_once_with(
            self.task.target_dir + '/LimeJeOS-openSUSE-13.2.initrd'
        )
        mock_wipe.assert_called_once_with(
            'temp-boot-directory/boot'
        )
        mock_create.assert_called_once_with(
            'temp-boot-directory/boot'
        )
        mbrid.write.assert_called_once_with(
            'temp-boot-directory/boot/mbrid'
        )
        cpio.create.assert_called_once_with(
            source_dir=self.task.temp_boot_root_directory,
            exclude=['/var/cache', '/image', '/usr/lib/grub2']
        )
        compress.xz.assert_called_once_with()
