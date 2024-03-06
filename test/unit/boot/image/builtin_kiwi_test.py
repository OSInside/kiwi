import sys
from unittest.mock import (
    patch, call, Mock, MagicMock
)
from pytest import raises

import kiwi

from ...test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.boot.image.builtin_kiwi import BootImageKiwi
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState

from kiwi.exceptions import KiwiConfigFileNotFound


class TestBootImageKiwi:
    @patch('kiwi.boot.image.builtin_kiwi.Temporary')
    @patch('kiwi.boot.image.builtin_kiwi.os.path.exists')
    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    def setup(self, mock_boot_path, mock_exists, mock_Temporary):
        mock_Temporary.return_value.new_dir.return_value.name = \
            'boot-root-directory'
        mock_boot_path.return_value = '../data'
        Defaults.set_platform_name('x86_64')
        mock_exists.return_value = True
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )
        self.setup = Mock()
        self.profile = Mock()
        self.profile.dot_profile = dict()
        kiwi.boot.image.builtin_kiwi.SystemSetup = Mock(
            return_value=self.setup
        )
        kiwi.boot.image.builtin_kiwi.Profile = Mock(
            return_value=self.profile
        )
        self.boot_image = BootImageKiwi(
            self.xml_state, 'some-target-dir'
        )

    @patch('kiwi.boot.image.builtin_kiwi.Temporary')
    @patch('kiwi.boot.image.builtin_kiwi.os.path.exists')
    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    def setup_method(self, cls, mock_boot_path, mock_exists, mock_Temporary):
        self.setup()

    def test_include_file(self):
        # is a nop for builtin kiwi initrd and does nothing
        self.boot_image.include_file('/root/a')

    @patch('kiwi.defaults.Defaults.get_boot_image_description_path')
    @patch('kiwi.boot.image.builtin_kiwi.Temporary')
    @patch('kiwi.boot.image.builtin_kiwi.SystemPrepare')
    def test_prepare(self, mock_SystemPrepare, mock_Temporary, mock_boot_path):
        system_prepare = Mock()
        manager = MagicMock()
        system_prepare.setup_repositories = Mock(
            return_value=manager
        )
        mock_SystemPrepare.return_value.__enter__.return_value = system_prepare
        mock_Temporary.return_value.new_dir.return_value.name = \
            'boot-root-directory'
        mock_boot_path.return_value = '../data'
        self.boot_image.prepare()
        system_prepare.setup_repositories.assert_called_once_with(
            signing_keys=None, target_arch=None
        )
        system_prepare.install_bootstrap.assert_called_once_with(
            manager.__enter__.return_value
        )
        system_prepare.install_system.assert_called_once_with(
            manager.__enter__.return_value
        )
        assert self.profile.add.call_args_list[0] == call(
            'kiwi_initrdname', 'initrd-oemboot-suse-13.2'
        )
        self.profile.create.assert_called_once_with(
            'boot-root-directory/.profile'
        )
        self.setup.import_description.assert_called_once_with()
        self.setup.import_overlay_files.assert_called_once_with(
            follow_links=True
        )
        self.setup.call_config_script.assert_called_once_with()
        system_prepare.pinch_system.assert_called_once_with(
            manager=manager.__enter__.return_value, force=True
        )
        self.setup.call_image_script.assert_called_once_with()

    @patch('os.path.exists')
    @patch('kiwi.boot.image.builtin_kiwi.Temporary')
    def test_prepare_no_boot_description_found(
        self, mock_Temporary, mock_os_path
    ):
        mock_Temporary.return_value.new_dir.return_value.name = \
            'boot-root-directory'
        mock_os_path.return_value = False
        with raises(KiwiConfigFileNotFound):
            self.boot_image.post_init()

    @patch('kiwi.boot.image.builtin_kiwi.ArchiveCpio')
    @patch('kiwi.boot.image.builtin_kiwi.Compress')
    @patch('kiwi.boot.image.builtin_kiwi.Path.create')
    @patch('kiwi.boot.image.builtin_kiwi.Path.wipe')
    @patch('kiwi.boot.image.builtin_kiwi.DataSync')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    @patch('kiwi.boot.image.builtin_kiwi.os.chmod')
    @patch('kiwi.boot.image.builtin_kiwi.Temporary')
    def test_create_initrd(
        self, mock_Temporary, mock_os_chmod,
        mock_prepared, mock_sync, mock_wipe, mock_create,
        mock_compress, mock_cpio
    ):
        data = Mock()
        mock_sync.return_value = data
        mock_Temporary.return_value.new_dir.return_value.name = \
            'temp-boot-directory'
        mock_prepared.return_value = True
        self.boot_image.boot_root_directory = 'boot-root-directory'
        mbrid = Mock()
        mbrid.write = Mock()
        cpio = Mock()
        compress = Mock()
        mock_cpio.return_value = cpio
        mock_compress.return_value = compress
        self.boot_image.create_initrd(mbrid)
        mock_sync.assert_called_once_with(
            'boot-root-directory/', 'temp-boot-directory'
        )
        mock_os_chmod.assert_called_once_with(
            'temp-boot-directory', 0o755
        )
        data.sync_data.assert_called_once_with(options=['--archive', '--hard-links', '--xattrs', '--acls', '--one-file-system', '--inplace'])
        mock_cpio.assert_called_once_with(
            ''.join(
                [
                    self.boot_image.target_dir,
                    '/LimeJeOS.x86_64-1.13.2.initrd'
                ]
            )
        )
        mock_compress.assert_called_once_with(
            ''.join(
                [
                    self.boot_image.target_dir,
                    '/LimeJeOS.x86_64-1.13.2.initrd'
                ]
            )
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
            source_dir='temp-boot-directory',
            exclude=[
                '/var/cache/kiwi', '/image', '/usr/lib/grub*',
                '/usr/share/doc', '/usr/share/man', '/home', '/media', '/srv'
            ]
        )
        compress.xz.assert_called_once_with(
            ['--check=crc32', '--lzma2=dict=1MiB', '--threads=0']
        )
        mock_cpio.reset_mock()
        mock_compress.reset_mock()
        self.boot_image.create_initrd(mbrid, 'foo')
        mock_cpio.assert_called_once_with(
            self.boot_image.target_dir + '/foo'
        )
        mock_compress.assert_called_once_with(
            self.boot_image.target_dir + '/foo'
        )

    @patch('kiwi.boot.image.builtin_kiwi.Path.wipe')
    @patch('os.path.exists')
    def test_cleanup(self, mock_path, mock_wipe):
        mock_path.return_value = True
        self.boot_image.temp_directories.append('boot-root-directory')
        self.boot_image.cleanup()
        mock_wipe.assert_called_once_with('boot-root-directory')

    def test_has_initrd_support(self):
        assert self.boot_image.has_initrd_support() is True

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()
