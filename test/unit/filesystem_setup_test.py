from mock import patch

import mock

from kiwi.filesystem.setup import FileSystemSetup


class TestFileSystemSetup(object):
    @patch('kiwi.filesystem.setup.SystemSize')
    def setup(self, mock_size):
        size = mock.Mock()
        size.accumulate_mbyte_file_sizes = mock.Mock(
            return_value=42
        )
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.xml_state = mock.Mock()
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='ext4'
        )
        self.xml_state.get_build_type_unpartitioned_bytes = mock.Mock(
            return_value=0
        )
        self.setup = FileSystemSetup(
            self.xml_state, 'root_dir'
        )

    @patch('kiwi.logger.log.warning')
    def test_init_with_unpartitioned(self, mock_warn):
        self.xml_state.get_build_type_unpartitioned_bytes = mock.Mock(
            return_value=1024
        )
        FileSystemSetup(self.xml_state, 'root_dir')

    def test_setup_with_pxe_type(self):
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        self.xml_state.build_type.get_filesystem = mock.Mock(
            return_value='xfs'
        )
        setup = FileSystemSetup(
            self.xml_state, 'root_dir'
        )
        assert setup.requested_filesystem == 'xfs'

    def test_get_size_mbytes_calculated(self):
        self.setup.configured_size = None
        assert self.setup.get_size_mbytes() == 42

    def test_get_size_mbytes_configured_additive(self):
        self.setup.configured_size.mbytes = 20
        self.setup.configured_size.additive = True
        assert self.setup.get_size_mbytes() == 62

    @patch('kiwi.logger.log.warning')
    def test_get_size_mbytes_configured(self, mock_log_warn):
        self.setup.configured_size.mbytes = 3
        self.setup.configured_size.additive = False
        assert self.setup.get_size_mbytes() == 3
        assert mock_log_warn.called
