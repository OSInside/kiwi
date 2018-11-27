from mock import patch
from pytest import raises

from kiwi.oci_tools.base import OCIBase


class TestOCIBase(object):
    @patch('kiwi.oci_tools.base.mkdtemp')
    def setup(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'kiwi_oci_dir.XXXX'
        self.oci = OCIBase('tag')
        mock_mkdtemp.assert_called_once_with(prefix='kiwi_oci_dir.')
        assert self.oci.container_tag == 'tag'

    def test_setup_existing_container_dir(self):
        oci = OCIBase('tag', 'layout_dir')
        assert oci.container_dir == 'layout_dir'

    def test_init_layout(self):
        with raises(NotImplementedError):
            self.oci.init_layout()

    def test_unpack(self):
        with raises(NotImplementedError):
            self.oci.unpack()

    def test_sync_rootfs(self):
        with raises(NotImplementedError):
            self.oci.sync_rootfs('root_dir')

    def test_import_rootfs(self):
        with raises(NotImplementedError):
            self.oci.import_rootfs('root_dir')

    def test_repack(self):
        with raises(NotImplementedError):
            self.oci.repack()

    def test_add_tag(self):
        with raises(NotImplementedError):
            self.oci.add_tag('tag')

    def test_set_config(self):
        with raises(NotImplementedError):
            self.oci.set_config(['data'])

    def test_garbage_collect(self):
        with raises(NotImplementedError):
            self.oci.garbage_collect()

    @patch('kiwi.oci_tools.base.Path')
    def test_destructor(self, mock_Path):
        self.oci.__del__()
        mock_Path.wipe.assert_called_once_with('kiwi_oci_dir.XXXX')
