from mock import (
    patch, call, mock_open
)
import mock

from kiwi.storage.subformat.gce import DiskFormatGce


class TestDiskFormatGce:
    def setup(self):
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='0.8.15'
        )
        self.disk_format = DiskFormatGce(
            self.xml_state, 'root_dir', 'target_dir'
        )

    def test_post_init(self):
        self.disk_format.post_init({'option': 'value', '--tag': 'tag'})
        assert self.disk_format.tag == 'tag'

    def test_store_to_result(self):
        result = mock.Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/some-disk-image.x86_64-0.8.15.tar.gz',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )

    @patch('kiwi.storage.subformat.gce.Command.run')
    @patch('kiwi.storage.subformat.gce.ArchiveTar')
    @patch('kiwi.storage.subformat.gce.mkdtemp')
    def test_create_image_format(
        self, mock_mkdtemp, mock_archive, mock_command
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        archive = mock.Mock()
        mock_archive.return_value = archive
        self.disk_format.tag = 'gce-license'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.disk_format.create_image_format()

        mock_command.assert_called_once_with(
            [
                'cp', 'target_dir/some-disk-image.x86_64-0.8.15.raw',
                'tmpdir/disk.raw'
            ]
        )
        assert m_open.call_args_list == [
            call('tmpdir/manifest.json', 'w')
        ]
        assert m_open.return_value.write.call_args_list == [
            call('{"licenses": ["gce-license"]}')
        ]
        mock_archive.assert_called_once_with(
            filename='target_dir/some-disk-image.x86_64-0.8.15.tar',
            file_list=['manifest.json', 'disk.raw']
        )
        archive.create_gnu_gzip_compressed.assert_called_once_with(
            'tmpdir'
        )
        assert self.disk_format.get_target_file_path_for_format('gce') == \
            'target_dir/some-disk-image.x86_64-0.8.15.tar.gz'
