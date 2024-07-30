from unittest.mock import patch
from pytest import raises
import sys
import unittest.mock as mock
import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.builder.archive import ArchiveBuilder

from kiwi.exceptions import KiwiArchiveSetupError


class TestArchiveBuilder:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.xml_state = mock.Mock()
        self.xml_state.profiles = None
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        self.setup = mock.Mock()
        kiwi.builder.archive.SystemSetup = mock.Mock(
            return_value=self.setup
        )
        self.archive = ArchiveBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )

    def setup_method(self, cls):
        self.setup()

    def test_create_unknown_archive_type(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='bogus'
        )
        xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        archive = ArchiveBuilder(
            xml_state, 'target_dir', 'root_dir'
        )
        with raises(KiwiArchiveSetupError):
            archive.create()

    @patch('kiwi.builder.archive.ArchiveTar')
    def test_create_tar(self, mock_tar):
        Defaults.set_platform_name('x86_64')
        self.archive.requested_archive_type = 'tbz'
        archive = mock.Mock()
        mock_tar.return_value = archive
        self.archive.create()
        mock_tar.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.tar'
        )
        archive.create_xz_compressed.assert_called_once_with(
            'root_dir', exclude=[
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi'
            ], xz_options=None
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.archive.ArchiveCpio')
    def test_create_cpio(self, mock_cpio):
        Defaults.set_platform_name('x86_64')
        self.archive.requested_archive_type = 'cpio'
        archive = mock.Mock()
        mock_cpio.return_value = archive
        self.archive.create()
        mock_cpio.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.cpio'
        )
        archive.create.assert_called_once_with(
            'root_dir', exclude=[
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi'
            ]
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()
