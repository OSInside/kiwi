from pytest import raises
from unittest.mock import (
    patch, Mock
)

import kiwi

from kiwi.defaults import Defaults
from kiwi.storage.subformat.oci import DiskFormatOci
from kiwi.exceptions import KiwiContainerBuilderError
from kiwi.system.uri import Uri


class TestDiskFormatOci:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        xml_data = Mock()
        xml_data.get_name = Mock(
            return_value='some-disk-image'
        )
        self.xml_state = Mock()
        self.uri = Uri(
            'docker-archive:/home/ms/alpine.tar', repo_type='container'
        )
        self.xml_state.xml_data = xml_data
        self.xml_state.get_derived_from_image_uri = Mock(
            return_value=[self.uri]
        )
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.runtime_config = Mock()
        kiwi.storage.subformat.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.disk_format = DiskFormatOci(
            self.xml_state, 'root_dir', 'target_dir'
        )
        self.disk_format.base_format = 'raw'

    def setup_method(self, cls):
        self.setup()

    def test_post_init(self):
        self.disk_format.post_init({'base_format': 'raw'})
        assert self.disk_format.base_container_uris == [self.uri]
        assert self.disk_format.base_format == 'raw'

    @patch('kiwi.storage.subformat.oci.Temporary.new_dir')
    @patch('kiwi.storage.subformat.oci.Command.run')
    @patch('kiwi.storage.subformat.oci.Defaults')
    @patch('kiwi.storage.subformat.oci.ContainerImage')
    @patch('kiwi.storage.subformat.oci.DiskFormat')
    @patch('kiwi.storage.subformat.oci.Path')
    @patch('kiwi.storage.subformat.oci.Result')
    @patch('os.chown')
    @patch('os.stat')
    def test_create_image_format_empty_root(
        self,
        mock_stat,
        mock_chown,
        mock_Result,
        mock_Path,
        mock_DiskFormat,
        mock_ContainerImage,
        mock_Defaults,
        mock_Command_run,
        mock_Temporary_new_dir
    ):
        mock_Temporary_new_dir.return_value.name = 'root_dir'
        result = Mock()
        result.get_name_for_pattern.return_value = 'some_custom_name'
        mock_Result.return_value = result
        self.disk_format.bundle_format = 'some'
        self.disk_format.base_container_uris = []
        mock_Defaults.get_imported_root_image.return_value \
            = 'some-base'

        # test raw format
        self.disk_format.create_image_format()

        mock_Path.assert_called_once_with('root_dir/disk')
        mock_Command_run.assert_called_once_with(
            [
                'cp', '-a',
                'target_dir/some-disk-image.x86_64-1.2.3.raw',
                'root_dir/disk/some_custom_name.raw'
            ]
        )
        mock_ContainerImage.new.assert_called_once_with(
            'docker', 'root_dir',
            self.xml_state.get_container_config.return_value
        )
        mock_ContainerImage.new.return_value.create.assert_called_once_with(
            'target_dir/some-disk-image.x86_64-1.2.3.docker.tar',
            '', True, True
        )

    @patch('kiwi.storage.subformat.oci.Command.run')
    @patch('kiwi.storage.subformat.oci.Temporary.new_dir')
    @patch('kiwi.storage.subformat.oci.RootImport')
    @patch('kiwi.storage.subformat.oci.Defaults')
    @patch('kiwi.storage.subformat.oci.Checksum')
    @patch('kiwi.storage.subformat.oci.ContainerImage')
    @patch('kiwi.storage.subformat.oci.RootInit')
    @patch('kiwi.storage.subformat.oci.DiskFormat')
    @patch('kiwi.storage.subformat.oci.Path')
    @patch('kiwi.storage.subformat.oci.Result')
    @patch('os.chown')
    @patch('os.stat')
    def test_create_image_format_derived_from(
        self,
        mock_stat,
        mock_chown,
        mock_Result,
        mock_Path,
        mock_DiskFormat,
        mock_RootInit,
        mock_ContainerImage,
        mock_Checksum,
        mock_Defaults,
        mock_RootImport,
        mock_Temporary_new_dir,
        mock_Command_run
    ):
        result = Mock()
        result.get_name_for_pattern.return_value = 'some_custom_name'
        mock_Result.return_value = result
        self.disk_format.bundle_format = 'some'
        mock_Defaults.get_imported_root_image.return_value \
            = 'some-base'
        tmpdir = Mock()
        tmpdir.name = 'tmpdir'
        mock_Temporary_new_dir.return_value = tmpdir

        # test raw format
        self.disk_format.create_image_format()

        mock_RootInit.assert_called_once_with(
            'tmpdir', allow_existing=True
        )
        mock_RootInit.return_value.create.assert_called_once_with()
        mock_RootImport.new.assert_called_once_with(
            'tmpdir', [self.uri], 'docker'
        )
        mock_RootImport.new.return_value.sync_data.assert_called_once_with()
        mock_Path.assert_called_once_with('tmpdir/disk')
        mock_Command_run.assert_called_once_with(
            [
                'cp', '-a',
                'target_dir/some-disk-image.x86_64-1.2.3.raw',
                'tmpdir/disk/some_custom_name.raw'
            ]
        )
        mock_Checksum.return_value.matches.assert_called_once_with(
            mock_Checksum.return_value.sha256.return_value, 'some-base.sha256'
        )
        mock_ContainerImage.new.assert_called_once_with(
            'docker', 'tmpdir', self.xml_state.get_container_config.return_value
        )
        mock_ContainerImage.new.return_value.create.assert_called_once_with(
            'target_dir/some-disk-image.x86_64-1.2.3.docker.tar',
            'some-base', True, True
        )

        # test qcow2 format
        mock_Command_run.reset_mock()
        self.disk_format.base_format = 'qcow2'
        self.disk_format.create_image_format()
        mock_DiskFormat.new.assert_called_once_with(
            'qcow2', self.xml_state, 'root_dir', 'target_dir'
        )
        disk_format = mock_DiskFormat.new.return_value.__enter__.return_value
        disk_format.create_image_format.assert_called_once_with()
        mock_Command_run.assert_called_once_with(
            [
                'cp', '-a',
                disk_format.get_target_file_path_for_format.return_value,
                'tmpdir/disk/some_custom_name.qcow2'
            ]
        )

        # test checksum failed for base container
        mock_Checksum.return_value.matches.reset_mock()
        mock_Checksum.return_value.matches.return_value = False
        with raises(KiwiContainerBuilderError):
            self.disk_format.create_image_format()

    def test_store_to_result(self):
        result = Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-1.2.3.docker.tar',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )
